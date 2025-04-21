# Market Data API

A comprehensive market data API service that provides real-time and historical market data for cryptocurrencies and stocks, with advanced analytics and alerting capabilities.

## Features

- **Real-time Market Data**: Live price data for cryptocurrencies and stocks
- **Historical Data**: Access to historical OHLCV data with various timeframes
- **Technical Analytics**: Built-in technical indicators (RSI, MACD, Bollinger Bands)
- **Custom Alerts**: Create and manage price and technical indicator alerts
- **Multiple Data Sources**: Integration with Binance (crypto) and Yahoo Finance (stocks)
- **RESTful API**: Clean, well-documented API endpoints
- **Docker Support**: Easy deployment with Docker and Docker Compose

## Prerequisites

- Docker
- Docker Compose
- Git

## Quick Start

1. Clone the repository:
   ```bash
   git clone <repository-url>
   cd <repository-name>
   ```

2. Copy the example environment file:
   ```bash
   cp .env.example .env
   ```

3. Start the services:
   ```bash
   docker-compose up -d
   ```

4. Test the API:
   ```bash
   ./test_api.sh
   ```

## Docker Architecture

The project uses Docker Compose to orchestrate multiple services:

- **API Service**: FastAPI-based REST API
- **Market Data Consumer**: Kafka consumer for processing market data
- **PostgreSQL**: Database for storing market data and alerts
- **Kafka**: Message broker for real-time data processing
- **Zookeeper**: Required for Kafka operation

## API Endpoints

### Market Data

- `GET /api/v1/market-data`: Get market data with filtering options
  - Parameters: `symbol`, `timeframe`, `start_time`, `end_time`, `limit`, `aggregate`

### Analytics

- `GET /api/v1/analytics`: Get technical indicators
  - Parameters: `symbol`, `indicators`, `timeframe`, `start_time`, `end_time`

### Alerts

- `GET /api/v1/alerts`: Get alerts
  - Parameters: `symbol`, `status`, `limit`
- `POST /api/v1/alerts`: Create a new alert
  - Body: `symbol`, `type`, `value`, `timeframe`, `notification_channels`

### Symbols

- `GET /api/v1/symbols`: Get available symbols
  - Parameters: `source`, `type`

### Timeframes

- `GET /api/v1/timeframes`: Get available timeframes

## Environment Variables

Create a `.env` file with the following variables:

```
# API Configuration
API_HOST=0.0.0.0
API_PORT=8000
API_WORKERS=4
API_RELOAD=true

# Database Configuration
POSTGRES_USER=postgres
POSTGRES_PASSWORD=postgres
POSTGRES_DB=market_data
POSTGRES_HOST=postgres
POSTGRES_PORT=5432

# Kafka Configuration
KAFKA_BOOTSTRAP_SERVERS=kafka:9092
KAFKA_TOPIC_MARKET_DATA=market_data
KAFKA_GROUP_ID=market_data_consumer

# Zookeeper Configuration
ZOOKEEPER_HOST=zookeeper
ZOOKEEPER_PORT=2181

# Market Data Sources
BINANCE_API_KEY=your_binance_api_key
BINANCE_API_SECRET=your_binance_api_secret
YAHOO_API_KEY=your_yahoo_api_key
```

## Development

1. Install dependencies:
   ```bash
   pip install -r requirements.txt
   ```

2. Run the API locally:
   ```bash
   uvicorn src.api.main:app --reload
   ```

3. Run tests:
   ```bash
   pytest
   ```

## Testing the API

Use the provided `test_api.sh` script to test the API endpoints:

```bash
./test_api.sh
```

The script provides an interactive menu to test different endpoints and features.

## Contributing

1. Fork the repository
2. Create a feature branch
3. Commit your changes
4. Push to the branch
5. Create a Pull Request

## License

This project is licensed under the MIT License - see the LICENSE file for details. 