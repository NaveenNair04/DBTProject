import json
import asyncio
import websockets
from datetime import datetime
from confluent_kafka import Producer
import os
from dotenv import load_dotenv

load_dotenv()

class FinnhubProducer:
    def __init__(self):
        self.ws_url = os.getenv('FINNHUB_WS_URL')
        self.api_key = os.getenv('FINNHUB_API_KEY')
        self.kafka_config = {
            'bootstrap.servers': os.getenv('KAFKA_BOOTSTRAP_SERVERS'),
            'client.id': 'finnhub_producer'
        }
        self.kafka_topic = os.getenv('KAFKA_TOPIC')
        self.producer = Producer(self.kafka_config)
        self.symbols = ['AAPL']  # Add more symbols as needed

    def delivery_report(self, err, msg):
        if err is not None:
            print(f'Message delivery failed: {err}')
        else:
            print(f'Message delivered to {msg.topic()} [{msg.partition()}]')

    async def process_message(self, message):
        try:
            data = json.loads(message)
            if data['type'] == 'trade':
                for trade in data['data']:
                    kafka_message = {
                        'source': 'finnhub',
                        'symbol': trade['s'],  # Symbol
                        'price': float(trade['p']),  # Price
                        'volume': float(trade['v']),  # Volume
                        'event_time': datetime.fromtimestamp(trade['t'] / 1000).isoformat() + 'Z'
                    }
                    
                    # Produce to Kafka
                    self.producer.produce(
                        self.kafka_topic,
                        key=kafka_message['symbol'],
                        value=json.dumps(kafka_message),
                        callback=self.delivery_report
                    )
                    self.producer.poll(0)  # Trigger delivery reports
                    
        except Exception as e:
            print(f'Error processing message: {e}')

    async def connect_and_subscribe(self):
        while True:
            try:
                async with websockets.connect(f"{self.ws_url}?token={self.api_key}") as ws:
                    print("Connected to Finnhub WebSocket")
                    
                    # Subscribe to symbols
                    for symbol in self.symbols:
                        subscribe_message = {
                            "type": "subscribe",
                            "symbol": symbol
                        }
                        await ws.send(json.dumps(subscribe_message))
                        print(f"Subscribed to {symbol}")
                    
                    while True:
                        message = await ws.recv()
                        await self.process_message(message)
                        
            except Exception as e:
                print(f"WebSocket connection error: {e}")
                print("Reconnecting in 5 seconds...")
                await asyncio.sleep(5)

    def run(self):
        loop = asyncio.get_event_loop()
        try:
            loop.run_until_complete(self.connect_and_subscribe())
        except KeyboardInterrupt:
            print("Shutting down Finnhub producer...")
        finally:
            self.producer.flush()  # Make sure all messages are sent
            loop.close()

if __name__ == "__main__":
    producer = FinnhubProducer()
    producer.run() 