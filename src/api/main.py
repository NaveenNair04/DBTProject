from fastapi import FastAPI, Depends, Query, WebSocket, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from sqlalchemy.orm import Session
from sqlalchemy import desc
from datetime import datetime, timedelta
from typing import List, Optional, Dict, Any
import json
import asyncio

from ..models.base import get_db
from ..models.market_data import MarketData, OHLCV, Alert
from .spark_analytics import router as spark_analytics_router

app = FastAPI(
    title="Market Data API",
    description="API for accessing real-time and historical market data",
    version="1.0.0",
)

# Enable CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Include Spark analytics routes
app.include_router(spark_analytics_router)


# API v1 routes
@app.get("/api/v1/market-data")
def get_market_data(
    symbol: Optional[str] = None,
    timeframe: Optional[str] = Query(None, regex="^[1-9][0-9]*(m|h|d)$"),
    start_time: Optional[datetime] = None,
    end_time: Optional[datetime] = None,
    limit: int = Query(default=100, le=1000),
    db: Session = Depends(get_db),
):
    """Get market data with optional filtering."""
    query = db.query(MarketData)

    if symbol:
        query = query.filter(MarketData.symbol == symbol)

    if start_time:
        query = query.filter(MarketData.event_time >= start_time)

    if end_time:
        query = query.filter(MarketData.event_time <= end_time)

    data = query.order_by(desc(MarketData.event_time)).limit(limit).all()

    return {
        "data": [
            {
                "symbol": item.symbol,
                "timestamp": item.event_time.isoformat(),
                "open": item.price,  # Using price as open since we don't have OHLC in raw data
                "high": item.price,  # Using price as high since we don't have OHLC in raw data
                "low": item.price,  # Using price as low since we don't have OHLC in raw data
                "close": item.price,  # Using price as close since we don't have OHLC in raw data
                "volume": item.volume,
                "source": item.source,
            }
            for item in data
        ],
        "total": len(data),
    }


@app.get("/api/v1/symbols")
def get_symbols(db: Session = Depends(get_db)):
    """Get available trading symbols."""
    symbols = db.query(MarketData.symbol).distinct().all()

    return {"symbols": [symbol[0] for symbol in symbols]}


@app.get("/api/v1/timeframes")
def get_timeframes():
    """Get available timeframes."""
    return {"timeframes": ["1m", "5m", "15m", "30m", "1h", "4h", "1d"]}


# Legacy routes (keeping for backward compatibility)
@app.get("/latest-data")
def get_latest_data(
    symbol: str, limit: int = Query(default=100, le=1000), db: Session = Depends(get_db)
):
    """Get the latest market data for a symbol."""
    data = (
        db.query(MarketData)
        .filter(MarketData.symbol == symbol)
        .order_by(desc(MarketData.event_time))
        .limit(limit)
        .all()
    )

    return [
        {
            "source": item.source,
            "symbol": item.symbol,
            "price": item.price,
            "volume": item.volume,
            "event_time": item.event_time.isoformat(),
        }
        for item in data
    ]


@app.get("/ohlc")
def get_ohlc_data(
    symbol: str,
    timeframe: str = Query(default="1min", regex="^[1-9][0-9]*(min|hour|day)$"),
    start_time: Optional[datetime] = None,
    end_time: Optional[datetime] = None,
    limit: int = Query(default=100, le=1000),
    db: Session = Depends(get_db),
):
    """Get OHLC data for a symbol."""
    query = db.query(OHLCV).filter(OHLCV.symbol == symbol)

    if start_time:
        query = query.filter(OHLCV.timestamp >= start_time)
    if end_time:
        query = query.filter(OHLCV.timestamp <= end_time)

    data = query.order_by(desc(OHLCV.timestamp)).limit(limit).all()

    return [
        {
            "symbol": item.symbol,
            "timestamp": item.timestamp.isoformat(),
            "open": item.open,
            "high": item.high,
            "low": item.low,
            "close": item.close,
            "volume": item.volume,
        }
        for item in data
    ]


@app.get("/alerts")
def get_alerts(
    symbol: Optional[str] = None,
    alert_type: Optional[str] = None,
    limit: int = Query(default=100, le=1000),
    db: Session = Depends(get_db),
):
    """Get market alerts."""
    query = db.query(Alert)

    if symbol:
        query = query.filter(Alert.symbol == symbol)
    if alert_type:
        query = query.filter(Alert.alert_type == alert_type)

    alerts = query.order_by(desc(Alert.timestamp)).limit(limit).all()

    return [
        {
            "symbol": alert.symbol,
            "alert_type": alert.alert_type,
            "message": alert.message,
            "timestamp": alert.timestamp.isoformat(),
            "value": alert.value,
        }
        for alert in alerts
    ]


# WebSocket connection manager
class ConnectionManager:
    def __init__(self):
        self.active_connections: List[WebSocket] = []

    async def connect(self, websocket: WebSocket):
        await websocket.accept()
        self.active_connections.append(websocket)

    def disconnect(self, websocket: WebSocket):
        self.active_connections.remove(websocket)

    async def broadcast(self, message: str):
        for connection in self.active_connections:
            try:
                await connection.send_text(message)
            except:
                await self.disconnect(connection)


manager = ConnectionManager()


@app.websocket("/ws/market-data/{symbol}")
async def websocket_endpoint(
    websocket: WebSocket, symbol: str, db: Session = Depends(get_db)
):
    await manager.connect(websocket)
    try:
        while True:
            # Get latest data
            latest_data = (
                db.query(MarketData)
                .filter(MarketData.symbol == symbol)
                .order_by(desc(MarketData.event_time))
                .first()
            )

            if latest_data:
                data = {
                    "symbol": latest_data.symbol,
                    "price": latest_data.price,
                    "volume": latest_data.volume,
                    "event_time": latest_data.event_time.isoformat(),
                }
                await websocket.send_text(json.dumps(data))

            await asyncio.sleep(1)  # Wait for 1 second before next update

    except Exception as e:
        print(f"WebSocket error: {e}")
    finally:
        manager.disconnect(websocket)


if __name__ == "__main__":
    import uvicorn

    uvicorn.run(app, host="0.0.0.0", port=8000)
