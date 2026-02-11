CREATE TABLE IF NOT EXISTS price_history (
    id SERIAL PRIMARY KEY,
    symbol VARCHAR(10) NOT NULL,
    trade_date DATE NOT NULL,
    close_price NUMERIC(10,2),
    adjusted_price NUMERIC(10,2),
    change_amount NUMERIC(10,2),
    change_percent NUMERIC(6,2),
    matched_volume BIGINT,
    matched_value NUMERIC(15,2),
    negotiated_volume BIGINT,
    negotiated_value NUMERIC(15,2),
    open_price NUMERIC(10,2),
    high_price NUMERIC(10,2),
    low_price NUMERIC(10,2),
    created_at TIMESTAMP DEFAULT NOW(),
    UNIQUE(symbol, trade_date)
);

CREATE INDEX IF NOT EXISTS idx_price_history_symbol ON price_history(symbol);
CREATE INDEX IF NOT EXISTS idx_price_history_date ON price_history(trade_date);
