from pydantic import BaseModel, Field
from typing import List, Dict, Optional
from datetime import datetime

class SymbolResponse(BaseModel):
    symbols: List[str] = Field(..., description="List of available trading symbols")

class MinMaxAnalytics(BaseModel):
    symbol: str = Field(..., description="Trading symbol")
    min_price: float = Field(..., description="Minimum price in the period")
    max_price: float = Field(..., description="Maximum price in the period")
    avg_price: float = Field(..., description="Average price in the period")
    count: int = Field(..., description="Number of data points")
    timestamp: datetime = Field(..., description="Timestamp of the analytics")

class RollingMetrics(BaseModel):
    symbol: str = Field(..., description="Trading symbol")
    window_start: datetime = Field(..., description="Start time of the window")
    window_end: datetime = Field(..., description="End time of the window")
    min_price: float = Field(..., description="Minimum price in the window")
    max_price: float = Field(..., description="Maximum price in the window")
    avg_price: float = Field(..., description="Average price in the window")
    avg_volume: float = Field(..., description="Average volume in the window")

class SymbolAnalytics(BaseModel):
    min_price: float = Field(..., description="Minimum price")
    max_price: float = Field(..., description="Maximum price")
    avg_price: float = Field(..., description="Average price")
    volume: float = Field(..., description="Total volume")

class AnalyticsSummary(BaseModel):
    timestamp: datetime = Field(..., description="Timestamp of the summary")
    analytics: Dict[str, SymbolAnalytics] = Field(..., description="Analytics for each symbol")

class ErrorResponse(BaseModel):
    detail: str = Field(..., description="Error message")

# API Documentation
API_TITLE = "Market Data Analytics API"
API_DESCRIPTION = """
Real-time market data analytics API powered by Spark Streaming.

This API provides:
- List of available trading symbols
- Min-max price analytics for individual symbols
- Rolling window metrics with customizable time windows
- Summary analytics for all symbols

Data is processed in real-time using Spark Streaming and stored in PostgreSQL.
"""

API_VERSION = "1.0.0"

# API Tags
TAGS = [
    {
        "name": "symbols",
        "description": "Operations related to available trading symbols"
    },
    {
        "name": "analytics",
        "description": "Market data analytics operations"
    }
]

# API Endpoints Documentation
ENDPOINTS = {
    "get_symbols": {
        "summary": "Get available trading symbols",
        "description": "Returns a list of all trading symbols currently being processed",
        "response_description": "List of available trading symbols",
        "tags": ["symbols"]
    },
    "get_min_max_analytics": {
        "summary": "Get min-max analytics for a symbol",
        "description": "Returns minimum, maximum, and average prices for a specific symbol",
        "response_description": "Min-max analytics for the specified symbol",
        "tags": ["analytics"]
    },
    "get_rolling_metrics": {
        "summary": "Get rolling window metrics",
        "description": "Returns analytics for a specific symbol within a rolling time window",
        "response_description": "Rolling window metrics for the specified symbol",
        "tags": ["analytics"]
    },
    "get_analytics_summary": {
        "summary": "Get analytics summary",
        "description": "Returns analytics summary for all available symbols",
        "response_description": "Summary of analytics for all symbols",
        "tags": ["analytics"]
    }
} 