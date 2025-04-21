import pandas as pd
import numpy as np
import json
import os
import time
from datetime import datetime
from typing import List, Dict, Any
from threading import Thread
from pathlib import Path
from confluent_kafka import Consumer, KafkaError
from sqlalchemy.orm import Session
from src.models.base import SessionLocal  # Using SessionLocal from base.py
from src.models.market_data import OHLCV  # Importing OHLCV model

from pyspark.sql.window import Window
from pyspark.sql import SparkSession
from pyspark.sql.functions import (
    col,
    min,
    max,
    avg,
    count,
    first,
    last,
    sum,
    window,
    when,
    mean,
)
from pyspark.sql.types import (
    StructType,
    StructField,
    StringType,
    DoubleType,
    TimestampType,
)

import logging

logging.basicConfig(
    level=logging.INFO, format="%(asctime)s - %(levelname)s - %(message)s"
)
logger = logging.getLogger(__name__)


class MarketDataProcessor:
    def __init__(self, window_size: int = 20, checkpoint_dir: str = "checkpoints"):
        self.window_size = window_size
        self.data_buffer: Dict[str, List[Dict[str, Any]]] = {}

        Path(checkpoint_dir).mkdir(parents=True, exist_ok=True)

        self.spark = (
            SparkSession.builder.appName("MarketDataSparkConsumer")
            .config("spark.sql.shuffle.partitions", "4")
            .config("spark.sql.streaming.checkpointLocation", checkpoint_dir)
            .getOrCreate()
        )

        self.schema = StructType(
            [
                StructField("symbol", StringType(), True),
                StructField("price", DoubleType(), True),
                StructField("volume", DoubleType(), True),
                StructField("event_time", TimestampType(), True),
            ]
        )

        self.kafka_consumer = Consumer(
            {
                "bootstrap.servers": os.getenv("KAFKA_BOOTSTRAP_SERVERS", "kafka:9092"),
                "group.id": "spark-consumer-group",
                "auto.offset.reset": "earliest",
            }
        )

        self.kafka_topic = os.getenv("KAFKA_TOPIC", "market_data")
        self.kafka_consumer.subscribe([self.kafka_topic])

    def consume_kafka_messages(self):
        while True:
            msg = self.kafka_consumer.poll(1.0)
            if msg is None:
                continue
            if msg.error():
                if msg.error().code() != KafkaError._PARTITION_EOF:
                    logger.error(f"Kafka error: {msg.error()}")
                continue

            try:
                data = msg.value().decode("utf-8")
                message = json.loads(data)

                symbol = message.get("symbol")
                if not symbol:
                    continue

                validated = {
                    "symbol": str(symbol),
                    "price": float(message["price"]),
                    "volume": float(message["volume"]),
                    "event_time": pd.to_datetime(message["event_time"]).to_pydatetime(),
                }

                self.data_buffer.setdefault(symbol, []).append(validated)
                logger.info(f"Received data for {symbol}")

            except Exception as e:
                logger.error(f"Error processing Kafka message: {str(e)}")

    def calculate_spark_metrics(self):
        try:
            for symbol, rows in self.data_buffer.items():
                if not rows:
                    continue

                df = pd.DataFrame(rows)
                df["event_time"] = pd.to_datetime(df["event_time"])

                spark_df = self.spark.createDataFrame(df, schema=self.schema)

                # Resample into 10-second windows
                ohlc_df = (
                    spark_df.groupBy(window("event_time", "10 seconds"), "symbol")
                    .agg(
                        first("price").alias("open"),
                        max("price").alias("high"),
                        min("price").alias("low"),
                        last("price").alias("close"),
                        sum("volume").alias("volume"),
                        avg("price").alias("avg_price"),
                    )
                    .orderBy("window")
                )

                ohlc_df.show(truncate=False)

                # Insert into DB using SQLAlchemy
                db = SessionLocal()  # Create a session using SessionLocal
                for row in ohlc_df.collect():
                    ohlcv_data = OHLCV(
                        symbol=row["symbol"],
                        timestamp=row["window"]["start"],  # timestamp from the window
                        open=row["open"],
                        high=row["high"],
                        low=row["low"],
                        close=row["close"],
                        volume=row["volume"],
                    )

                    db.add(ohlcv_data)
                    db.commit()  # Commit each insertion
                    logger.info(
                        f"Stored OHLCV data: {row['symbol']} at {row['window']['start']}"
                    )

                db.close()

        except Exception as e:
            logger.error(f"Error in calculate_spark_metrics: {str(e)}")

    def run_periodic_analytics(self, interval: int = 10):
        while True:
            try:
                self.calculate_spark_metrics()
            except Exception as e:
                logger.error(f"Analytics error: {e}")
            time.sleep(interval)


def main():
    processor = MarketDataProcessor()

    Thread(target=processor.consume_kafka_messages, daemon=True).start()
    Thread(target=processor.run_periodic_analytics, args=(10,), daemon=True).start()

    try:
        while True:
            time.sleep(1)
    except KeyboardInterrupt:
        logger.info("Shutting down...")


if __name__ == "__main__":
    main()
