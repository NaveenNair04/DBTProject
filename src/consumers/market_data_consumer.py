from confluent_kafka import Consumer
import json
from datetime import datetime
import os
from dotenv import load_dotenv
from sqlalchemy.orm import Session
from src.models.base import SessionLocal
from src.models.market_data import MarketData, OHLCV

load_dotenv()

class MarketDataConsumer:
    def __init__(self):
        self.kafka_config = {
            'bootstrap.servers': os.getenv('KAFKA_BOOTSTRAP_SERVERS'),
            'group.id': 'market_data_consumer',
            'auto.offset.reset': 'earliest'
        }
        self.kafka_topic = os.getenv('KAFKA_TOPIC')
        self.consumer = Consumer(self.kafka_config)
        self.consumer.subscribe([self.kafka_topic])

    def process_message(self, msg):
        try:
            data = json.loads(msg.value())
            db = SessionLocal()
            
            # Create market data entry
            market_data = MarketData(
                source=data['source'],
                symbol=data['symbol'],
                price=data['price'],
                volume=data['volume'],
                event_time=datetime.fromisoformat(data['event_time'].replace('Z', '+00:00'))
            )
            
            db.add(market_data)
            db.commit()
            print(f"Stored market data: {data['symbol']} at {data['event_time']}")
            
        except Exception as e:
            print(f"Error processing message: {e}")
        finally:
            db.close()

    def run(self):
        try:
            while True:
                msg = self.consumer.poll(1.0)
                if msg is None:
                    continue
                if msg.error():
                    print(f"Consumer error: {msg.error()}")
                    continue
                self.process_message(msg)
                
        except KeyboardInterrupt:
            print("Shutting down consumer...")
        finally:
            self.consumer.close()

if __name__ == "__main__":
    consumer = MarketDataConsumer()
    consumer.run() 