from base import Base, engine
from market_data import MarketData, OHLCV, Alert

def init_db():
    # Create all tables
    Base.metadata.create_all(bind=engine)
    print("Database tables created successfully!")

if __name__ == "__main__":
    init_db() 