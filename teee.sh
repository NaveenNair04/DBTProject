#!/bin/bash

# Colors for better readability
GREEN='\033[0;32m'
BLUE='\033[0;34m'
RED='\033[0;31m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

echo -e "${BLUE}Testing Market Data API Endpoints${NC}"
echo "--------------------------------"

# Helper function to print section headers
print_header() {
  echo -e "\n${GREEN}$1${NC}"
  echo "--------------------------------"
}

# Helper function to make API calls
call_api() {
  echo -e "${BLUE}Request:${NC} $1"
  echo -e "${BLUE}Response:${NC}"
  curl -s -X "$2" "$1" | jq
  echo ""
}

# Helper function to get user input
get_symbol() {
  local prompt="$1"
  local default="$2"
  local input

  echo -e "${YELLOW}${prompt}${NC} (default: ${default})"
  read -rp "Enter symbol: " input
  echo "${input:-$default}"
}

get_timeframe() {
  local prompt="$1"
  local default="$2"
  local input

  echo -e "${YELLOW}${prompt}${NC} (default: ${default})"
  echo -e "Available timeframes: 1m, 5m, 15m, 30m, 1h, 4h, 1d"
  read -rp "Enter timeframe: " input
  echo "${input:-$default}"
}

get_limit() {
  local prompt="$1"
  local default="$2"
  local input

  echo -e "${YELLOW}${prompt}${NC} (default: ${default})"
  read -rp "Enter limit: " input
  echo "${input:-$default}"
}

# Market Data Tests
test_market_data() {
  print_header "Market Data Endpoint Tests"

  local symbol
  symbol=$(get_symbol "Enter symbol to test (e.g., BTCUSDT, AAPL, ETHUSDT)" "BTCUSDT")
  local timeframe
  timeframe=$(get_timeframe "Enter timeframe" "1m")
  local limit
  limit=$(get_limit "Enter number of results to show" "10")

  echo -e "${BLUE}1. Basic Market Data Request:${NC}"
  call_api "http://localhost:8000/api/v1/market-data?symbol=${symbol}" "GET"

  echo -e "${BLUE}2. Market Data with Timeframe:${NC}"
  call_api "http://localhost:8000/api/v1/market-data?symbol=${symbol}&timeframe=${timeframe}" "GET"

  echo -e "${BLUE}3. Market Data with Limit:${NC}"
  call_api "http://localhost:8000/api/v1/market-data?symbol=${symbol}&limit=${limit}" "GET"

  echo -e "${BLUE}4. Market Data with Aggregation:${NC}"
  call_api "http://localhost:8000/api/v1/market-data?symbol=${symbol}&timeframe=${timeframe}&aggregate=avg" "GET"
}

# Analytics Tests
test_analytics() {
  print_header "Analytics Endpoint Tests"

  local symbol
  symbol=$(get_symbol "Enter symbol to analyze" "BTCUSDT")
  local timeframe
  timeframe=$(get_timeframe "Enter timeframe" "1h")

  echo -e "${BLUE}1. Basic Analytics (RSI):${NC}"
  call_api "http://localhost:8000/api/v1/analytics?symbol=${symbol}&indicators=rsi" "GET"

  echo -e "${BLUE}2. Multiple Indicators:${NC}"
  call_api "http://localhost:8000/api/v1/analytics?symbol=${symbol}&indicators=rsi,macd,bollinger&timeframe=${timeframe}" "GET"
}

# Alerts Tests
test_alerts() {
  print_header "Alerts Endpoint Tests"

  local symbol
  symbol=$(get_symbol "Enter symbol for alerts" "BTCUSDT")
  local timeframe
  timeframe=$(get_timeframe "Enter timeframe" "1h")

  echo -e "${BLUE}1. Get Alerts for Symbol:${NC}"
  call_api "http://localhost:8000/api/v1/alerts?symbol=${symbol}" "GET"

  echo -e "${BLUE}2. Create New Alert:${NC}"
  read -rp "Enter alert value (e.g., 85000 for price): " value

  curl -s -X POST "http://localhost:8000/api/v1/alerts" \
    -H "Content-Type: application/json" \
    -d "{
      \"symbol\": \"${symbol}\",
      \"type\": \"price_above\",
      \"value\": ${value},
      \"timeframe\": \"${timeframe}\",
      \"notification_channels\": [\"email\", \"slack\"]
    }" | jq
}

# Symbols Tests
test_symbols() {
  print_header "Symbols Endpoint Tests"

  echo -e "${BLUE}1. Get All Symbols:${NC}"
  call_api "http://localhost:8000/api/v1/symbols" "GET"

  echo -e "${BLUE}2. Filter by Source:${NC}"
  read -rp "Enter source (binance/yahoo): " source
  call_api "http://localhost:8000/api/v1/symbols?source=${source}" "GET"

  echo -e "${BLUE}3. Filter by Type:${NC}"
  read -rp "Enter type (crypto/stock/forex): " type
  call_api "http://localhost:8000/api/v1/symbols?type=${type}" "GET"
}

# Timeframes Tests
test_timeframes() {
  print_header "Timeframes Endpoint Tests"
  call_api "http://localhost:8000/api/v1/timeframes" "GET"
}

# Legacy Tests
test_legacy() {
  print_header "Legacy Endpoint Tests"

  local symbol
  symbol=$(get_symbol "Enter symbol for legacy tests" "BTCUSDT")
  local limit
  limit=$(get_limit "Enter number of results to show" "10")

  echo -e "${BLUE}1. Legacy Latest Data:${NC}"
  call_api "http://localhost:8000/latest-data?symbol=${symbol}&limit=${limit}" "GET"

  echo -e "${BLUE}2. Legacy OHLC Data:${NC}"
  call_api "http://localhost:8000/ohlc?symbol=${symbol}&timeframe=1min&limit=${limit}" "GET"
}

# Main menu function
show_menu() {
  echo -e "\n${GREEN}Market Data API Test Menu${NC}"
  echo "--------------------------------"
  echo "1. Test Market Data Endpoint"
  echo "2. Test Analytics Endpoint"
  echo "3. Test Alerts Endpoint"
  echo "4. Test Symbols Endpoint"
  echo "5. Test Timeframes Endpoint"
  echo "6. Test Legacy Endpoints"
  echo "7. Exit"
  echo "--------------------------------"
  read -rp "Enter your choice (1-7): " choice

  if [[ "$choice" =~ ^[1-7]$ ]]; then
    echo "$choice"
  else
    echo "invalid"
  fi
}

# Main loop
while true; do
  choice=$(show_menu)

  case "$choice" in
  1) test_market_data ;;
  2) test_analytics ;;
  3) test_alerts ;;
  4) test_symbols ;;
  5) test_timeframes ;;
  6) test_legacy ;;
  7)
    echo -e "${GREEN}Exiting...${NC}"
    exit 0
    ;;
  invalid)
    echo -e "${RED}Invalid choice. Please enter a number between 1 and 7.${NC}"
    ;;
  esac

  echo -e "\n${YELLOW}Press Enter to continue...${NC}"
  read -r
done
