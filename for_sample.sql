-- Analytics Results Table
CREATE TABLE analytics_results (
    id SERIAL PRIMARY KEY,
    symbol VARCHAR NOT NULL,
    timestamp TIMESTAMP NOT NULL,
    min_price FLOAT NOT NULL,
    max_price FLOAT NOT NULL,
    avg_price FLOAT NOT NULL,
    total_volume FLOAT NOT NULL,
    trade_count INTEGER NOT NULL,
    window_start TIMESTAMP NOT NULL,
    window_end TIMESTAMP NOT NULL
);

-- Create indexes for analytics_results
CREATE INDEX idx_analytics_results_symbol ON analytics_results(symbol);
CREATE INDEX idx_analytics_results_timestamp ON analytics_results(timestamp);

-- OHLCV Table
CREATE TABLE ohlcv (
    id SERIAL PRIMARY KEY,
    symbol VARCHAR NOT NULL,
    timestamp TIMESTAMP NOT NULL,
    open FLOAT NOT NULL,
    high FLOAT NOT NULL,
    low FLOAT NOT NULL,
    close FLOAT NOT NULL,
    volume FLOAT NOT NULL
);

-- Create indexes for ohlcv
CREATE INDEX idx_ohlcv_symbol ON ohlcv(symbol);
CREATE INDEX idx_ohlcv_timestamp ON ohlcv(timestamp);