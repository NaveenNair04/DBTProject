import os
import json
import time
from datetime import datetime, timedelta
from typing import Dict, Any, Optional
from pathlib import Path
from sqlalchemy.orm import Session
from src.models.base import SessionLocal
from src.models.market_data import OHLCV, AnalyticsResult

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
    from_json,
    to_json,
    struct,
    lit,
    current_timestamp,
    to_timestamp
)
from pyspark.sql.types import (
    StructType,
    StructField,
    StringType,
    DoubleType,
    TimestampType,
    MapType
)

import logging

logging.basicConfig(
    level=logging.INFO, format="%(asctime)s - %(levelname)s - %(message)s"
)
logger = logging.getLogger(__name__)


class MarketDataProcessor:
    def __init__(self, checkpoint_dir: str = "checkpoints", mode: str = "streaming"):
        """
        Initialize the MarketDataProcessor.
        
        Args:
            checkpoint_dir (str): Directory for Spark checkpoints
            mode (str): Processing mode - "streaming" or "batch"
        """
        Path(checkpoint_dir).mkdir(parents=True, exist_ok=True)
        self.mode = mode.lower()
        
        if self.mode not in ["streaming", "batch"]:
            raise ValueError("Mode must be either 'streaming' or 'batch'")

        # Initialize Spark session with Kafka support
        self.spark = (
            SparkSession.builder.appName(f"MarketDataSparkProcessor_{self.mode}")
            .config("spark.sql.shuffle.partitions", "4")
            .config("spark.sql.streaming.checkpointLocation", checkpoint_dir)
            .config("spark.jars.packages", "org.apache.spark:spark-sql-kafka-0-10_2.12:3.3.2")
            .getOrCreate()
        )

        # Define schema for market data
        self.market_data_schema = StructType([
            StructField("source", StringType(), True),
            StructField("symbol", StringType(), True),
            StructField("price", DoubleType(), True),
            StructField("volume", DoubleType(), True),
            StructField("event_time", StringType(), True)
        ])

        # Kafka configuration
        self.kafka_bootstrap_servers = os.getenv("KAFKA_BOOTSTRAP_SERVERS", "kafka:9092")
        self.kafka_topic = os.getenv("KAFKA_TOPIC", "market_data")

    def process_stream(self):
        """Process data in streaming mode."""
        try:
            # Read from Kafka
            kafka_df = (
                self.spark.readStream
                .format("kafka")
                .option("kafka.bootstrap.servers", self.kafka_bootstrap_servers)
                .option("subscribe", self.kafka_topic)
                .option("startingOffsets", "latest")
                .load()
            )

            # Parse and process the stream
            self._process_dataframe(kafka_df, is_streaming=True)

        except Exception as e:
            logger.error(f"Error in streaming mode: {e}")
            raise

    def process_batch(self, start_time: Optional[datetime] = None, end_time: Optional[datetime] = None):
        """
        Process data in batch mode.
        
        Args:
            start_time (datetime, optional): Start time for batch processing
            end_time (datetime, optional): End time for batch processing
        """
        try:
            # If no time range specified, process last 24 hours
            if not start_time:
                start_time = datetime.now() - timedelta(days=1)
            if not end_time:
                end_time = datetime.now()

            # Read from Kafka for the specified time range
            kafka_df = (
                self.spark.read
                .format("kafka")
                .option("kafka.bootstrap.servers", self.kafka_bootstrap_servers)
                .option("subscribe", self.kafka_topic)
                .option("startingOffsets", f"{{'market_data': {{'0': {int(start_time.timestamp() * 1000)}}}}}")
                .option("endingOffsets", f"{{'market_data': {{'0': {int(end_time.timestamp() * 1000)}}}}}")
                .load()
            )

            # Parse and process the batch
            self._process_dataframe(kafka_df, is_streaming=False)

        except Exception as e:
            logger.error(f"Error in batch mode: {e}")
            raise

    def _process_dataframe(self, df, is_streaming: bool):
        """Process the dataframe in either streaming or batch mode."""
        # Parse JSON data
        parsed_df = df.select(
            from_json(col("value").cast("string"), self.market_data_schema).alias("data")
        ).select("data.*")

        # Convert event_time string to timestamp
        parsed_df = parsed_df.withColumn(
            "event_time", 
            col("event_time").cast(TimestampType())
        )

        # Calculate analytics for different time windows
        window_analytics = self._calculate_window_analytics(parsed_df, "1 minute")
        window_5min_analytics = self._calculate_window_analytics(parsed_df, "5 minutes")
        ohlcv_data = self._calculate_ohlcv(parsed_df)

        if is_streaming:
            # Write streaming results
            query = ohlcv_data.writeStream.foreachBatch(
                lambda batch_df, batch_id: self._write_analytics_to_db(batch_df, batch_id)
            ).start()
            query.awaitTermination()
        else:
            # Write batch results
            self._write_analytics_to_db(ohlcv_data, 0)

    def _calculate_window_analytics(self, df, window_duration: str):
        """Calculate analytics for a specific time window."""
        return (
            df
            .withWatermark("event_time", window_duration)
            .groupBy(
                window("event_time", window_duration),
                "symbol"
            )
            .agg(
                min("price").alias("min_price"),
                max("price").alias("max_price"),
                avg("price").alias("avg_price"),
                sum("volume").alias("total_volume"),
                count("*").alias("trade_count")
            )
            .withColumn("window_start", col("window.start"))
            .withColumn("window_end", col("window.end"))
            .drop("window")
        )

    def _calculate_ohlcv(self, df):
        """Calculate OHLCV data."""
        return (
            df
            .withWatermark("event_time", "10 seconds")
            .groupBy(
                window("event_time", "10 seconds"),
                "symbol"
            )
            .agg(
                first("price").alias("open"),
                max("price").alias("high"),
                min("price").alias("low"),
                last("price").alias("close"),
                sum("volume").alias("volume")
            )
            .withColumn("timestamp", col("window.start"))
            .drop("window")
        )

    def _write_analytics_to_db(self, batch_df, batch_id):
        """Write analytics results to the database."""
        if batch_df.rdd.isEmpty():
            return
        
        # Convert to pandas for easier processing
        analytics_df = batch_df.toPandas()
        
        # Store in database
        db = SessionLocal()
        try:
            for _, row in analytics_df.iterrows():
                # Store OHLCV data
                ohlcv = OHLCV(
                    symbol=row["symbol"],
                    timestamp=row["timestamp"],
                    open=row["open"],
                    high=row["high"],
                    low=row["low"],
                    close=row["close"],
                    volume=row["volume"]
                )
                db.add(ohlcv)
            
            db.commit()
            logger.info(f"Stored analytics for batch {batch_id}")
        except Exception as e:
            logger.error(f"Error storing analytics: {e}")
            db.rollback()
        finally:
            db.close()


def main():
    """Main entry point for the processor."""
    import argparse
    
    parser = argparse.ArgumentParser(description="Market Data Processor")
    parser.add_argument("--mode", choices=["streaming", "batch"], default="streaming",
                      help="Processing mode: streaming or batch")
    parser.add_argument("--start-time", help="Start time for batch processing (ISO format)")
    parser.add_argument("--end-time", help="End time for batch processing (ISO format)")
    
    args = parser.parse_args()
    
    processor = MarketDataProcessor(mode=args.mode)
    
    if args.mode == "streaming":
        processor.process_stream()
    else:
        start_time = datetime.fromisoformat(args.start_time) if args.start_time else None
        end_time = datetime.fromisoformat(args.end_time) if args.end_time else None
        processor.process_batch(start_time, end_time)


if __name__ == "__main__":
    main()
