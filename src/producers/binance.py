import json
import asyncio
import websockets
from datetime import datetime
from confluent_kafka import Producer
import os
from dotenv import load_dotenv

load_dotenv()


class BinanceProducer:
    def __init__(self):
        self.ws_url = os.getenv("BINANCE_WS_URL")
        self.kafka_config = {
            "bootstrap.servers": os.getenv("KAFKA_BOOTSTRAP_SERVERS"),
            "client.id": "binance_producer",
        }
        self.kafka_topic = os.getenv("KAFKA_TOPIC")
        self.producer = Producer(self.kafka_config)
        self.symbols = ["btcusdt"]  # Add more symbols as needed

    def delivery_report(self, err, msg):
        if err is not None:
            print(f"Message delivery failed: {err}")
        else:
            print(f"Message delivered to {msg.topic()} [{msg.partition()}]")

    async def process_message(self, message):
        try:
            data = json.loads(message)
            if "e" in data and data["e"] == "trade":
                kafka_message = {
                    "source": "binance",
                    "symbol": data["s"].upper(),  # Convert BTCUSDT to uppercase
                    "price": float(data["p"]),
                    "volume": float(data["q"]),
                    "event_time": datetime.fromtimestamp(data["T"] / 1000).isoformat()
                    + "Z",
                }

                # Produce to Kafka
                self.producer.produce(
                    self.kafka_topic,
                    key=kafka_message["symbol"],
                    value=json.dumps(kafka_message),
                    callback=self.delivery_report,
                )
                self.producer.poll(0)  # Trigger delivery reports

        except Exception as e:
            print(f"Error processing message: {e}")

    async def connect_and_subscribe(self):
        streams = [f"{symbol}@trade" for symbol in self.symbols]
        subscribe_message = {"method": "SUBSCRIBE", "params": streams, "id": 1}

        while True:
            try:
                async with websockets.connect(f"{self.ws_url}/stream") as ws:
                    print("Connected to Binance WebSocket")
                    await ws.send(json.dumps(subscribe_message))

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
            print("Shutting down Binance producer...")
        finally:
            self.producer.flush()  # Make sure all messages are sent
            loop.close()


if __name__ == "__main__":
    producer = BinanceProducer()
    producer.run()

