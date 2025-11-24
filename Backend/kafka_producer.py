# backend/kafka_producer.py
import json
import asyncio
import logging
from kafka import KafkaProducer
from binance import AsyncClient, BinanceSocketManager
from config import settings

logger = logging.getLogger(__name__)

class CryptoKafkaProducer:
    def __init__(self):
        self.producer = KafkaProducer(
            bootstrap_servers=settings.KAFKA_BOOTSTRAP_SERVERS,
            value_serializer=lambda v: json.dumps(v).encode('utf-8'),
            batch_size=16384,
            linger_ms=10,
            acks='all'
        )
        self.running = False
    
    async def start_streaming(self):
        """Start streaming data from Binance"""
        self.running = True
        try:
            client = await AsyncClient.create()
            bm = BinanceSocketManager(client)
            
            # Create multiple socket connections
            sockets = []
            for symbol in settings.CRYPTO_SYMBOLS:
                socket = bm.trade_socket(symbol.lower())
                sockets.append((socket, symbol))
            
            # Handle all sockets concurrently
            await asyncio.gather(*[
                self._handle_socket(socket, symbol) 
                for socket, symbol in sockets
            ])
            
        except Exception as e:
            logger.error(f"Error in streaming: {e}")
        finally:
            await client.close_connection()
    
    async def _handle_socket(self, socket, symbol):
        """Handle individual socket connection"""
        async with socket as stream:
            while self.running:
                try:
                    data = await stream.recv()
                    
                    message = {
                        'symbol': symbol,
                        'price': float(data['p']),
                        'quantity': float(data['q']),
                        'timestamp': data['T'],
                        'event_time': data['E']
                    }
                    
                    # Send to Kafka
                    self.producer.send(
                        settings.KAFKA_TOPICS["PRICES"], 
                        value=message
                    )
                    
                    logger.debug(f"Sent data for {symbol}: {message['price']}")
                    
                except Exception as e:
                    logger.error(f"Error processing {symbol}: {e}")
                    await asyncio.sleep(1)
    
    def stop_streaming(self):
        """Stop streaming data"""
        self.running = False
        self.producer.close()