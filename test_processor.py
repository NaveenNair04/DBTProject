from datetime import datetime, timedelta
import time
from src.analytics.processor import MarketDataProcessor

def generate_sample_data(symbol: str, base_price: float, base_volume: int) -> dict:
    """Generate sample stock data with some random variation."""
    import random
    price_variation = random.uniform(-2.0, 2.0)
    volume_variation = random.randint(-100, 100)
    return {
        "symbol": symbol,
        "price": base_price + price_variation,
        "volume": base_volume + volume_variation,
        "event_time": datetime.now().isoformat()
    }

def main():
    # Initialize the processor
    processor = MarketDataProcessor()
    
    # Sample stock symbols and their base values
    stocks = {
        "AAPL": {"base_price": 150.0, "base_volume": 1000},
        "GOOGL": {"base_price": 2800.0, "base_volume": 500},
        "MSFT": {"base_price": 400.0, "base_volume": 800}
    }
    
    print("Starting stock data processor...")
    print("Press Ctrl+C to stop")
    
    try:
        while True:
            # Generate and add sample data for each stock
            for symbol, values in stocks.items():
                sample_data = generate_sample_data(
                    symbol,
                    values["base_price"],
                    values["base_volume"]
                )
                processor.add_data(sample_data)
            
            # Wait for 1 second before generating next batch
            time.sleep(1)
            
    except KeyboardInterrupt:
        print("\nStopping processor...")

if __name__ == "__main__":
    main() 