# backend/spark_processor.py
from pyspark.sql import SparkSession
from pyspark.sql.functions import *
from pyspark.sql.types import *
from pyspark.sql.window import Window
import logging
from config import settings

logger = logging.getLogger(__name__)

class CryptoSparkProcessor:
    def __init__(self):
        self.spark = None
        self.queries = []
    
    def initialize_spark(self):
        """Initialize Spark session with correct master"""
        try:
            self.spark = SparkSession.builder \
                .appName("CryptoRealTimeDashboard") \
                .master("local[*]") \
                .config("spark.jars.packages", 
                       "org.apache.spark:spark-sql-kafka-0-10_2.12:3.5.0,"
                       "org.apache.kafka:kafka-clients:3.5.1") \
                .config("spark.sql.streaming.checkpointLocation", "./checkpoint") \
                .config("spark.sql.adaptive.enabled", "true") \
                .config("spark.sql.adaptive.coalescePartitions.enabled", "true") \
                .config("spark.sql.shuffle.partitions", "10") \
                .config("spark.streaming.stopGracefullyOnShutdown", "true") \
                .config("spark.jars.repositories", "https://repo1.maven.org/maven2/") \
                .config("spark.driver.memory", "2g") \
                .config("spark.executor.memory", "2g") \
                .config("spark.driver.bindAddress", "127.0.0.1") \
                .config("spark.driver.host", "localhost") \
                .config("spark.driver.port", "0") \
                .config("spark.blockManager.port", "0") \
                .config("spark.ui.port", "0") \
                .getOrCreate()
            
            self.spark.sparkContext.setLogLevel("WARN")
            logger.info(f"Spark session initialized with master: local[*]")
            logger.info(f"Spark version: {self.spark.version}")
            
        except Exception as e:
            logger.error(f"Failed to initialize Spark: {e}")
            raise
    
    def create_price_stream(self):
        """Create streaming DataFrame from Kafka"""
        price_schema = StructType([
            StructField("symbol", StringType()),
            StructField("price", DoubleType()),
            StructField("quantity", DoubleType()),
            StructField("timestamp", LongType()),
            StructField("event_time", LongType())
        ])
        
        stream_df = self.spark \
            .readStream \
            .format("kafka") \
            .option("kafka.bootstrap.servers", settings.KAFKA_BOOTSTRAP_SERVERS) \
            .option("subscribe", settings.KAFKA_TOPICS["PRICES"]) \
            .option("startingOffsets", "latest") \
            .option("failOnDataLoss", "false") \
            .load()
        
        # Parse JSON data
        parsed_df = stream_df \
            .select(
                from_json(col("value").cast("string"), price_schema).alias("data"),
                col("timestamp").alias("kafka_timestamp")
            ) \
            .select(
                "data.symbol",
                "data.price",
                "data.quantity", 
                "data.timestamp",
                "data.event_time",
                "kafka_timestamp"
            )
        
        return parsed_df
    
    def calculate_metrics(self, stream_df):
        """Calculate real-time metrics"""
        # Convert timestamp to timestamp type for watermarking
        stream_df = stream_df.withColumn(
            "event_time", 
            (col("event_time") / 1000).cast("timestamp")
        )
        
        # Define window with watermark
        windowed_df = stream_df \
            .withWatermark("event_time", "30 seconds") \
            .groupBy(
                window(col("event_time"), "1 minute", "30 seconds"),
                col("symbol")
            )
        
        # Calculate metrics (without Window functions which aren't supported in streaming)
        metrics_df = windowed_df.agg(
            last("price").alias("current_price"),
            avg("price").alias("moving_avg_1min"),
            stddev("price").alias("price_volatility"),
            max("price").alias("high_1min"),
            min("price").alias("low_1min"),
            count("price").alias("trade_count"),
            first("event_time").alias("window_start_time"),
            last("event_time").alias("window_end_time")
        ) \
        .withColumn("price_trend",
            when(col("current_price") > col("moving_avg_1min"), "up")
            .when(col("current_price") < col("moving_avg_1min"), "down")
            .otherwise("stable")
        ) \
        .withColumn("price_change",
            ((col("current_price") - col("moving_avg_1min")) / col("moving_avg_1min")) * 100
        ) \
        .select(
            "symbol",
            "current_price",
            "moving_avg_1min",
            "price_volatility",
            "price_trend",
            "price_change",
            "high_1min",
            "low_1min",
            "trade_count",
            col("window.start").alias("window_start"),
            col("window.end").alias("window_end")
        )
        
        return metrics_df
    
    def calculate_correlations(self, stream_df):
        """Calculate real-time correlations between symbols"""
        # Convert timestamp
        stream_df = stream_df.withColumn(
            "event_time", 
            (col("event_time") / 1000).cast("timestamp")
        )
        
        # Pivot data to get prices by symbol
        pivot_df = stream_df \
            .withWatermark("event_time", "1 minute") \
            .groupBy(
                window(col("event_time"), "5 minutes"),
                col("symbol")
            ) \
            .agg(avg("price").alias("avg_price"))
        
        # Pivot for correlation matrix
        correlation_df = pivot_df \
            .groupBy("window") \
            .pivot("symbol", settings.CRYPTO_SYMBOLS[:5]) \
            .agg(first("avg_price")) \
            .drop("window")
        
        return correlation_df
    
    def start_processing(self):
        """Start all streaming processing"""
        if not self.spark:
            self.initialize_spark()
        
        # Start metrics processing
        price_stream = self.create_price_stream()
        metrics_stream = self.calculate_metrics(price_stream)
        
        # Write metrics to Kafka
        metrics_query = metrics_stream \
            .select(
                to_json(struct("*")).alias("value")
            ) \
            .writeStream \
            .format("kafka") \
            .option("kafka.bootstrap.servers", settings.KAFKA_BOOTSTRAP_SERVERS) \
            .option("topic", settings.KAFKA_TOPICS["PROCESSED_METRICS"]) \
            .option("checkpointLocation", "./checkpoint/metrics") \
            .outputMode("update") \
            .start()
        
        self.queries.append(metrics_query)
        logger.info("Started metrics streaming processing")
        
        return self.queries
    
    def stop_processing(self):
        """Stop all streaming queries"""
        for query in self.queries:
            query.stop()
        if self.spark:
            self.spark.stop()