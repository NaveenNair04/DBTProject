FROM python:3.11-slim

# Install Java and other dependencies
RUN apt-get update && apt-get install -y \
    default-jdk \
    wget \
    && rm -rf /var/lib/apt/lists/*

# Set Java environment variables
ENV JAVA_HOME=/usr/lib/jvm/java-17-openjdk-amd64
ENV PATH=$PATH:$JAVA_HOME/bin

WORKDIR /app

# Install Python dependencies
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Create checkpoint directory for Spark
RUN mkdir -p /app/checkpoints

COPY . .

# Set environment variables for Spark
ENV PYSPARK_PYTHON=/usr/local/bin/python
ENV PYSPARK_DRIVER_PYTHON=/usr/local/bin/python
ENV SPARK_HOME=/usr/local/lib/python3.11/site-packages/pyspark

CMD ["python", "-m", "src.producers.binance"] 