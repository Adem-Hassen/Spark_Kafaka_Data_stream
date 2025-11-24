# backend/models.py
from pydantic import BaseModel
from typing import List, Dict, Optional
from datetime import datetime

class PriceData(BaseModel):
    symbol: str
    price: float
    quantity: float
    timestamp: int
    event_time: int

class CryptoMetrics(BaseModel):
    symbol: str
    current_price: float
    moving_avg_5: float
    moving_avg_10: float
    moving_avg_1min: float
    price_volatility: float
    price_trend: str
    price_change: float
    high_1min: float
    low_1min: float
    trade_count: int
    window_start: str
    window_end: str

class CorrelationData(BaseModel):
    pair: str
    correlation: float

class DashboardResponse(BaseModel):
    latest_metrics: List[CryptoMetrics]
    correlations: List[CorrelationData]
    total_data_points: int
    calculation_method: str
    timestamp: datetime