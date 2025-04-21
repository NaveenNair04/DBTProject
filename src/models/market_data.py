from sqlalchemy import Column, Integer, Float, String, DateTime, Index, ForeignKey
from sqlalchemy.orm import relationship
from .base import Base
from datetime import datetime


class MarketData(Base):
    __tablename__ = "market_data"

    id = Column(Integer, primary_key=True)
    source = Column(String, nullable=False)
    symbol = Column(String, nullable=False)
    price = Column(Float, nullable=False)
    volume = Column(Float, nullable=False)
    event_time = Column(DateTime, nullable=False)

    # Create index on symbol and event_time for faster queries
    __table_args__ = (Index("idx_market_data_symbol_time", "symbol", "event_time"),)


class OHLCV(Base):
    __tablename__ = "ohlcv"

    id = Column(Integer, primary_key=True, index=True)
    symbol = Column(String, index=True)
    timestamp = Column(DateTime, index=True)
    open = Column(Float)
    high = Column(Float)
    low = Column(Float)
    close = Column(Float)
    volume = Column(Float)

    # Create index on symbol and timestamp
    __table_args__ = (Index("idx_ohlcv_symbol_time", "symbol", "timestamp"),)


class Alert(Base):
    __tablename__ = "alerts"

    id = Column(Integer, primary_key=True)
    symbol = Column(String, nullable=False)
    alert_type = Column(String, nullable=False)  # e.g., "VOLUME_SPIKE", "PRICE_CHANGE"
    message = Column(String, nullable=False)
    timestamp = Column(DateTime, nullable=False, default=datetime.utcnow)
    value = Column(Float, nullable=True)  # The value that triggered the alert

    # Create index on timestamp for faster queries
    __table_args__ = (Index("idx_alerts_timestamp", "timestamp"),)


class AnalyticsResult(Base):
    __tablename__ = "analytics_results"

    id = Column(Integer, primary_key=True, index=True)
    symbol = Column(String, index=True)
    timestamp = Column(DateTime, index=True)
    min_price = Column(Float)
    max_price = Column(Float)
    avg_price = Column(Float)
    total_volume = Column(Float)
    trade_count = Column(Integer)
    window_start = Column(DateTime)
    window_end = Column(DateTime)

