from confluent_kafka import Consumer, Producer
import json
from datetime import datetime
import os
from dotenv import load_dotenv
import logging
from typing import List, Dict, Any
import time

load_dotenv()

logging.basicConfig(
    level=logging.INFO, format="%(asctime)s - %(levelname)s - %(message)s"
)
logger = logging.getLogger(__name__)

class MarketDataConsumer:
    def __init__(self, batch_size: int = 100, batch_timeout: float = 1.0):
        self.kafka_config = {
            'bootstrap.servers': os.getenv('KAFKA_BOOTSTRAP_SERVERS'),
            'group.id': 'market_data_consumer',
            'auto.offset.reset': 'earliest',
            'enable.auto.commit': True,
            'auto.commit.interval.ms': 5000
        }
        self.producer_config = {
            'bootstrap.servers': os.getenv('KAFKA_BOOTSTRAP_SERVERS'),
            'client.id': 'market_data_producer',
            'acks': 'all',
            'retries': 3,
            'retry.backoff.ms': 1000
        }
        self.kafka_topic = os.getenv('KAFKA_TOPIC')
        self.consumer = Consumer(self.kafka_config)
        self.producer = Producer(self.producer_config)
        self.consumer.subscribe([self.kafka_topic])
        
        self.batch_size = batch_size
        self.batch_timeout = batch_timeout
        self.message_buffer: List[Dict[str, Any]] = []
        self.last_flush_time = time.time()

    def validate_message(self, data: Dict[str, Any]) -> bool:
        required_fields = ['source', 'symbol', 'price', 'volume', 'event_time']
        if not all(field in data for field in required_fields):
            logger.warning(f"Missing required fields in message: {data}")
            return False
        
        try:
            # Validate data types and ranges
            price = float(data['price'])
            volume = float(data['volume'])
            event_time = datetime.fromisoformat(data['event_time'].replace('Z', '+00:00'))
            
            if price <= 0:
                logger.warning(f"Invalid price value: {price}")
                return False
            if volume < 0:
                logger.warning(f"Invalid volume value: {volume}")
                return False
            if event_time > datetime.now():
                logger.warning(f"Future timestamp detected: {event_time}")
                return False
                
            return True
        except (ValueError, TypeError) as e:
            logger.warning(f"Data validation error: {e}")
            return False

    def process_message(self, msg) -> None:
        try:
            data = json.loads(msg.value())
            
            # Validate the message
            if not self.validate_message(data):
                return
            
            # Add to buffer
            self.message_buffer.append(data)
            
            # Check if we should flush the buffer
            current_time = time.time()
            if (len(self.message_buffer) >= self.batch_size or 
                current_time - self.last_flush_time >= self.batch_timeout):
                self.flush_buffer()
            
        except json.JSONDecodeError as e:
            logger.error(f"JSON decode error: {e}")
        except Exception as e:
            logger.error(f"Error processing message: {e}")

    def flush_buffer(self) -> None:
        if not self.message_buffer:
            return
            
        try:
            # Forward messages in batch
            for data in self.message_buffer:
                self.producer.produce(
                    self.kafka_topic,
                    value=json.dumps(data).encode('utf-8'),
                    callback=self.delivery_report
                )
            
            # Poll to handle delivery reports
            self.producer.poll(0)
            
            logger.info(f"Forwarded {len(self.message_buffer)} messages to Kafka")
            self.message_buffer.clear()
            self.last_flush_time = time.time()
            
        except Exception as e:
            logger.error(f"Error flushing message buffer: {e}")
            # Keep messages in buffer for retry
            time.sleep(1)  # Back off before retry

    def delivery_report(self, err, msg) -> None:
        if err is not None:
            logger.error(f'Message delivery failed: {err}')
            # Could implement retry logic here if needed
        else:
            logger.debug(f'Message delivered to {msg.topic()} [{msg.partition()}]')

    def run(self) -> None:
        try:
            while True:
                msg = self.consumer.poll(1.0)
                if msg is None:
                    # Check if we should flush buffer due to timeout
                    if time.time() - self.last_flush_time >= self.batch_timeout:
                        self.flush_buffer()
                    continue
                    
                if msg.error():
                    logger.error(f"Consumer error: {msg.error()}")
                    continue
                    
                self.process_message(msg)
                
        except KeyboardInterrupt:
            logger.info("Shutting down consumer...")
        except Exception as e:
            logger.error(f"Unexpected error in consumer: {e}")
        finally:
            # Flush any remaining messages
            self.flush_buffer()
            self.producer.flush()
            self.consumer.close()

if __name__ == "__main__":
    consumer = MarketDataConsumer()
    consumer.run() 