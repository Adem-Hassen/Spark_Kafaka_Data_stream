# backend/config.py
import os
from typing import List

class Settings:
    KAFKA_BOOTSTRAP_SERVERS = os.getenv("KAFKA_BOOTSTRAP_SERVERS", "localhost:9092")
    REDIS_URL = os.getenv("REDIS_URL", "redis://localhost:6379")
    SPARK_MASTER = os.getenv("SPARK_MASTER", "spark://localhost:7077")
    
    # Crypto symbols to monitor
    CRYPTO_SYMBOLS = [
        "BTCUSDT", "ETHUSDT", "ADAUSDT", "DOTUSDT", "LINKUSDT",
        "BNBUSDT", "XRPUSDT", "DOGEUSDT", "SOLUSDT", "MATICUSDT"
    ]
    
    KAFKA_TOPICS = {
        "PRICES": "crypto-prices",
        "METRICS": "crypto-metrics",
        "PROCESSED_METRICS": "crypto-metrics-processed"
    }

settings = Settings()