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

-- Foreign trading (Khoi Ngoai)
CREATE TABLE IF NOT EXISTS foreign_trading (
    id SERIAL PRIMARY KEY,
    symbol VARCHAR(10) NOT NULL,
    trade_date DATE NOT NULL,
    buy_volume BIGINT,
    buy_value NUMERIC(18,2),
    sell_volume BIGINT,
    sell_value NUMERIC(18,2),
    net_volume BIGINT,
    net_value NUMERIC(18,2),
    room_remaining BIGINT,
    foreign_ownership_pct NUMERIC(6,2),
    change_amount NUMERIC(10,2),
    change_percent NUMERIC(6,2),
    created_at TIMESTAMP DEFAULT NOW(),
    UNIQUE(symbol, trade_date)
);

CREATE INDEX IF NOT EXISTS idx_foreign_trading_symbol ON foreign_trading(symbol);
CREATE INDEX IF NOT EXISTS idx_foreign_trading_date ON foreign_trading(trade_date);

-- Proprietary trading (Tu Doanh)
CREATE TABLE IF NOT EXISTS proprietary_trading (
    id SERIAL PRIMARY KEY,
    symbol VARCHAR(10) NOT NULL,
    trade_date DATE NOT NULL,
    buy_volume BIGINT,
    buy_value NUMERIC(18,2),
    sell_volume BIGINT,
    sell_value NUMERIC(18,2),
    created_at TIMESTAMP DEFAULT NOW(),
    UNIQUE(symbol, trade_date)
);

CREATE INDEX IF NOT EXISTS idx_proprietary_trading_symbol ON proprietary_trading(symbol);
CREATE INDEX IF NOT EXISTS idx_proprietary_trading_date ON proprietary_trading(trade_date);
