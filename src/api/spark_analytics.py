from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from sqlalchemy import func, desc
from typing import List, Dict, Any
from datetime import datetime, timedelta
import json
import requests
import os

from ..models.base import get_db
from ..models.market_data import MarketData, OHLCV

router = APIRouter(
    prefix="/api/v1/spark-analytics",
    tags=["spark-analytics"]
)

# Configuration
SPARK_PROCESSOR_URL = os.getenv("SPARK_PROCESSOR_URL", "http://spark-processor:8001")

@router.get("/min-max/{symbol}")
async def get_min_max_analytics(symbol: str, db: Session = Depends(get_db)):
    """Get min/max analytics for a specific symbol."""
    try:
        # Get the latest data from the database
        latest_data = (
            db.query(
                func.min(MarketData.price).label('min_price'),
                func.max(MarketData.price).label('max_price'),
                func.avg(MarketData.price).label('avg_price'),
                func.count(MarketData.id).label('count')
            )
            .filter(MarketData.symbol == symbol)
            .filter(MarketData.event_time >= datetime.now() - timedelta(hours=1))
            .first()
        )

        if not latest_data or latest_data.count == 0:
            raise HTTPException(status_code=404, detail=f"No data found for symbol {symbol}")

        return {
            "symbol": symbol,
            "min_price": float(latest_data.min_price),
            "max_price": float(latest_data.max_price),
            "avg_price": float(latest_data.avg_price),
            "count": latest_data.count,
            "timestamp": datetime.now().isoformat()
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/rolling-metrics/{symbol}")
async def get_rolling_metrics(
    symbol: str,
    window_duration: str = "5 minutes",
    db: Session = Depends(get_db)
):
    """Get rolling metrics for a specific symbol."""
    try:
        # Parse window duration
        duration = int(window_duration.split()[0])
        unit = window_duration.split()[1].lower()
        
        if unit == "minutes":
            time_delta = timedelta(minutes=duration)
        elif unit == "hours":
            time_delta = timedelta(hours=duration)
        else:
            raise HTTPException(status_code=400, detail="Invalid window duration. Use 'minutes' or 'hours'")

        # Get data for the specified window
        window_data = (
            db.query(
                func.min(MarketData.price).label('min_price'),
                func.max(MarketData.price).label('max_price'),
                func.avg(MarketData.price).label('avg_price'),
                func.avg(MarketData.volume).label('avg_volume')
            )
            .filter(MarketData.symbol == symbol)
            .filter(MarketData.event_time >= datetime.now() - time_delta)
            .first()
        )

        if not window_data:
            raise HTTPException(status_code=404, detail=f"No data found for symbol {symbol} in the specified window")

        return {
            "symbol": symbol,
            "window_start": (datetime.now() - time_delta).isoformat(),
            "window_end": datetime.now().isoformat(),
            "min_price": float(window_data.min_price),
            "max_price": float(window_data.max_price),
            "avg_price": float(window_data.avg_price),
            "avg_volume": float(window_data.avg_volume)
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/symbols")
async def get_analytics_symbols(db: Session = Depends(get_db)):
    """Get list of symbols with available analytics."""
    try:
        # Get unique symbols from the database
        symbols = (
            db.query(MarketData.symbol)
            .distinct()
            .filter(MarketData.event_time >= datetime.now() - timedelta(hours=24))
            .all()
        )
        
        return {
            "symbols": [symbol[0] for symbol in symbols]
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/summary")
async def get_analytics_summary(db: Session = Depends(get_db)):
    """Get summary of all analytics."""
    try:
        # Get the latest data for each symbol
        latest_data = (
            db.query(MarketData)
            .filter(MarketData.event_time >= datetime.now() - timedelta(hours=1))
            .order_by(MarketData.symbol, desc(MarketData.event_time))
            .distinct(MarketData.symbol)
            .all()
        )

        analytics = {}
        for data in latest_data:
            analytics[data.symbol] = {
                "min_price": float(data.price),  # Using current price as min/max for simplicity
                "max_price": float(data.price),
                "avg_price": float(data.price),
                "volume": float(data.volume)
            }

        return {
            "timestamp": datetime.now().isoformat(),
            "analytics": analytics
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))