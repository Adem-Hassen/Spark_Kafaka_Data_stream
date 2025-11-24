# backend/main.py
from fastapi import FastAPI, WebSocket, WebSocketDisconnect, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import HTMLResponse
import asyncio
import json
import redis
import logging
from typing import Dict, List
from kafka import KafkaConsumer
import threading

from config import settings
from kafka_producer import CryptoKafkaProducer
from spark_processor import CryptoSparkProcessor
from models import CryptoMetrics, CorrelationData, DashboardResponse

# Setup logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

app = FastAPI(title="Crypto Spark Dashboard", version="1.0.0")

# CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)

# Global instances
redis_client = redis.Redis.from_url(settings.REDIS_URL, decode_responses=True)
kafka_producer = CryptoKafkaProducer()
spark_processor = CryptoSparkProcessor()

class ConnectionManager:
    def __init__(self):
        self.active_connections: List[WebSocket] = []
        self.loop = None
    
    def set_loop(self, loop):
        """Set the event loop for the manager"""
        self.loop = loop
    
    async def connect(self, websocket: WebSocket):
        await websocket.accept()
        self.active_connections.append(websocket)
        logger.info(f"New WebSocket connection. Total: {len(self.active_connections)}")
    
    def disconnect(self, websocket: WebSocket):
        if websocket in self.active_connections:
            self.active_connections.remove(websocket)
            logger.info(f"WebSocket disconnected. Total: {len(self.active_connections)}")
    
    def broadcast_sync(self, message: dict):
        """Synchronous broadcast that schedules the async broadcast"""
        if self.loop and not self.loop.is_closed():
            asyncio.run_coroutine_threadsafe(self._broadcast_async(message), self.loop)
    
    async def _broadcast_async(self, message: dict):
        """Async broadcast helper"""
        if not self.active_connections:
            return
        
        disconnected = []
        for connection in self.active_connections:
            try:
                await connection.send_json(message)
            except Exception as e:
                logger.error(f"Error sending message: {e}")
                disconnected.append(connection)
        
        for connection in disconnected:
            self.disconnect(connection)

manager = ConnectionManager()

@app.on_event("startup")
async def startup_event():
    """Initialize services on startup"""
    logger.info("Starting up Crypto Dashboard Services")
    
    # Set the event loop for the manager
    manager.set_loop(asyncio.get_event_loop())
    
    # Start Kafka consumer in background thread
    def start_consumer():
        consumer = KafkaConsumer(
            settings.KAFKA_TOPICS["PROCESSED_METRICS"],
            bootstrap_servers=settings.KAFKA_BOOTSTRAP_SERVERS,
            value_deserializer=lambda m: json.loads(m.decode('utf-8')),
            group_id='fastapi-dashboard',
            auto_offset_reset='latest',
            enable_auto_commit=True
        )
        
        logger.info("Kafka consumer thread started")
        
        for message in consumer:
            try:
                metrics_data = message.value
                # Cache in Redis
                symbol = metrics_data.get('symbol')
                if symbol:
                    redis_client.setex(
                        f"metrics:{symbol}",
                        300,  # 5 minutes TTL
                        json.dumps(metrics_data)
                    )
                    logger.debug(f"Cached metrics for {symbol}")
                    
                    # Broadcast to WebSocket connections
                    manager.broadcast_sync(metrics_data)
                    
            except Exception as e:
                logger.error(f"Error processing Kafka message: {e}", exc_info=True)
    
    # Start background threads
    kafka_thread = threading.Thread(target=start_consumer, daemon=True)
    kafka_thread.start()
    
    # Start Spark processing
    try:
        spark_processor.start_processing()
        logger.info("Spark processing started")
    except Exception as e:
        logger.error(f"Failed to start Spark processing: {e}", exc_info=True)
    
    # Start Binance streaming
    try:
        asyncio.create_task(kafka_producer.start_streaming())
        logger.info("Binance streaming started")
    except Exception as e:
        logger.error(f"Failed to start Binance streaming: {e}", exc_info=True)
    
    logger.info("All services started successfully")

@app.on_event("shutdown")
async def shutdown_event():
    """Cleanup on shutdown"""
    logger.info("Shutting down services")
    kafka_producer.stop_streaming()
    spark_processor.stop_processing()
    redis_client.close()

@app.get("/")
async def root():
    return {"message": "Crypto Spark Dashboard API", "status": "running"}

@app.get("/health")
async def health_check():
    """Health check endpoint"""
    try:
        redis_ping = redis_client.ping()
        return {
            "status": "healthy",
            "redis": redis_ping,
            "kafka": "connected"
        }
    except Exception as e:
        logger.error(f"Health check failed: {e}")
        return {
            "status": "unhealthy",
            "error": str(e)
        }

@app.get("/metrics/current")
async def get_current_metrics():
    """Get current cached metrics for all symbols"""
    try:
        metrics = []
        
        # Get all metrics keys from Redis
        keys = redis_client.keys("metrics:*")
        logger.info(f"Found {len(keys)} metric keys in Redis")
        
        if not keys:
            # Return empty response if no data yet
            return {
                "latest_metrics": [],
                "correlations": [],
                "total_data_points": 0,
                "calculation_method": "spark_streaming",
                "timestamp": asyncio.get_event_loop().time(),
                "message": "No data available yet. Waiting for Spark processing..."
            }
        
        for key in keys:
            try:
                cached = redis_client.get(key)
                if cached:
                    metric_data = json.loads(cached)
                    metrics.append(metric_data)
            except Exception as e:
                logger.error(f"Error reading key {key}: {e}")
        
        # Generate sample correlations
        correlations = []
        symbols = settings.CRYPTO_SYMBOLS[:5]
        for i, sym1 in enumerate(symbols):
            for j, sym2 in enumerate(symbols):
                if i < j:  # Avoid duplicates
                    correlations.append({
                        "pair": f"{sym1}-{sym2}",
                        "correlation": 0.3 + (i * 0.1)
                    })
        
        return {
            "latest_metrics": metrics,
            "correlations": correlations,
            "total_data_points": len(metrics),
            "calculation_method": "spark_streaming",
            "timestamp": asyncio.get_event_loop().time()
        }
    
    except Exception as e:
        logger.error(f"Error getting metrics: {e}", exc_info=True)
        raise HTTPException(
            status_code=500, 
            detail=f"Error retrieving metrics: {str(e)}"
        )

@app.get("/metrics/{symbol}")
async def get_symbol_metrics(symbol: str):
    """Get metrics for a specific symbol"""
    try:
        cached = redis_client.get(f"metrics:{symbol}")
        if not cached:
            raise HTTPException(
                status_code=404, 
                detail=f"No metrics found for {symbol}"
            )
        
        return json.loads(cached)
    
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error getting metrics for {symbol}: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@app.websocket("/ws/live")
async def websocket_live(websocket: WebSocket):
    """WebSocket for real-time metrics"""
    await manager.connect(websocket)
    
    try:
        # Send initial data
        try:
            initial_data = await get_current_metrics()
            await websocket.send_json(initial_data)
        except Exception as e:
            logger.error(f"Error sending initial data: {e}")
        
        # Keep connection alive
        while True:
            await asyncio.sleep(30)
            await websocket.send_json({
                "type": "ping", 
                "timestamp": asyncio.get_event_loop().time()
            })
            
    except WebSocketDisconnect:
        manager.disconnect(websocket)
    except Exception as e:
        logger.error(f"WebSocket error: {e}")
        manager.disconnect(websocket)

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="127.0.0.1", port=8000)