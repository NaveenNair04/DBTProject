#!/bin/bash

# Colors for better readability
GREEN='\033[0;32m'
BLUE='\033[0;34m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

echo -e "${BLUE}Running All Market API Endpoint Tests${NC}"
echo "--------------------------------"

# Helper to print headers
print_header() {
  echo -e "\n${GREEN}$1${NC}"
  echo "--------------------------------"
}

# Helper to make API call
call_api() {
  echo -e "${BLUE}Request:${NC} $1"
  echo -e "${BLUE}Response:${NC}"
  curl -s -X ${2:-GET} "$1" | jq
  echo ""
}

# Defaults
symbol="BTCUSDT"
timeframe="1m"
limit="10"

### Run Tests

print_header "Market Data Endpoints"
call_api "http://localhost:8000/api/v1/market-data?symbol=$symbol"
call_api "http://localhost:8000/api/v1/market-data?symbol=$symbol&timeframe=$timeframe"
call_api "http://localhost:8000/api/v1/market-data?symbol=$symbol&limit=$limit"
call_api "http://localhost:8000/api/v1/market-data?symbol=$symbol&timeframe=$timeframe&aggregate=avg"

print_header "Analytics Endpoints"
call_api "http://localhost:8000/api/v1/analytics?symbol=$symbol&indicators=rsi"
call_api "http://localhost:8000/api/v1/analytics?symbol=$symbol&indicators=rsi,macd,bollinger&timeframe=1h"

print_header "Alerts Endpoints"
call_api "http://localhost:8000/api/v1/alerts?symbol=$symbol"
echo -e "${YELLOW}Creating new alert...${NC}"
curl -s -X POST "http://localhost:8000/api/v1/alerts" \
  -H "Content-Type: application/json" \
  -d "{
    \"symbol\": \"$symbol\",
    \"type\": \"price_above\",
    \"value\": 85000,
    \"timeframe\": \"1h\",
    \"notification_channels\": [\"email\", \"slack\"]
  }" | jq

print_header "Symbols Endpoints"
call_api "http://localhost:8000/api/v1/symbols"
call_api "http://localhost:8000/api/v1/symbols?source=binance"
call_api "http://localhost:8000/api/v1/symbols?type=crypto"

print_header "Timeframes Endpoint"
call_api "http://localhost:8000/api/v1/timeframes"

print_header "Legacy Endpoints"
call_api "http://localhost:8000/latest-data?symbol=$symbol&limit=$limit"
call_api "http://localhost:8000/ohlc?symbol=$symbol&timeframe=1min&limit=$limit"

echo -e "\n${GREEN}All tests completed.${NC}"
