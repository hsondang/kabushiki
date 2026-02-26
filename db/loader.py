import csv
import os

import psycopg2
from dotenv import load_dotenv

load_dotenv()

PRICE_HISTORY_UPSERT = """
    INSERT INTO price_history (
        symbol, trade_date, close_price, adjusted_price,
        change_amount, change_percent,
        matched_volume, matched_value,
        negotiated_volume, negotiated_value,
        open_price, high_price, low_price
    ) VALUES (
        %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s
    )
    ON CONFLICT (symbol, trade_date) DO UPDATE SET
        close_price = EXCLUDED.close_price,
        adjusted_price = EXCLUDED.adjusted_price,
        change_amount = EXCLUDED.change_amount,
        change_percent = EXCLUDED.change_percent,
        matched_volume = EXCLUDED.matched_volume,
        matched_value = EXCLUDED.matched_value,
        negotiated_volume = EXCLUDED.negotiated_volume,
        negotiated_value = EXCLUDED.negotiated_value,
        open_price = EXCLUDED.open_price,
        high_price = EXCLUDED.high_price,
        low_price = EXCLUDED.low_price;
"""

FOREIGN_TRADING_UPSERT = """
    INSERT INTO foreign_trading (
        symbol, trade_date, buy_volume, buy_value,
        sell_volume, sell_value, net_volume, net_value,
        room_remaining, foreign_ownership_pct,
        change_amount, change_percent
    ) VALUES (
        %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s
    )
    ON CONFLICT (symbol, trade_date) DO UPDATE SET
        buy_volume = EXCLUDED.buy_volume,
        buy_value = EXCLUDED.buy_value,
        sell_volume = EXCLUDED.sell_volume,
        sell_value = EXCLUDED.sell_value,
        net_volume = EXCLUDED.net_volume,
        net_value = EXCLUDED.net_value,
        room_remaining = EXCLUDED.room_remaining,
        foreign_ownership_pct = EXCLUDED.foreign_ownership_pct,
        change_amount = EXCLUDED.change_amount,
        change_percent = EXCLUDED.change_percent;
"""

PROPRIETARY_TRADING_UPSERT = """
    INSERT INTO proprietary_trading (
        symbol, trade_date, buy_volume, buy_value,
        sell_volume, sell_value
    ) VALUES (
        %s, %s, %s, %s, %s, %s
    )
    ON CONFLICT (symbol, trade_date) DO UPDATE SET
        buy_volume = EXCLUDED.buy_volume,
        buy_value = EXCLUDED.buy_value,
        sell_volume = EXCLUDED.sell_volume,
        sell_value = EXCLUDED.sell_value;
"""


def get_connection():
    return psycopg2.connect(
        host=os.getenv("DB_HOST", "localhost"),
        port=os.getenv("DB_PORT", "5432"),
        dbname=os.getenv("DB_NAME", "stocks_db"),
        user=os.getenv("DB_USER", "stocks_user"),
        password=os.getenv("DB_PASSWORD", "stocks_pass"),
    )


def init_schema():
    """Run schema.sql to create tables if they don't exist."""
    schema_path = os.path.join(os.path.dirname(__file__), "schema.sql")
    with open(schema_path, "r") as f:
        sql = f.read()
    conn = get_connection()
    try:
        with conn.cursor() as cur:
            cur.execute(sql)
        conn.commit()
        print("Database schema initialized.")
    finally:
        conn.close()


def _load_csv(csv_path, upsert_sql, columns):
    """Generic CSV-to-DB loader."""
    init_schema()

    conn = get_connection()
    loaded = 0
    try:
        with conn.cursor() as cur:
            with open(csv_path, "r", encoding="utf-8") as f:
                reader = csv.DictReader(f)
                for row in reader:
                    cur.execute(upsert_sql, tuple(row[col] for col in columns))
                    loaded += 1
        conn.commit()
        print(f"Loaded {loaded} records from {csv_path} into PostgreSQL.")
    finally:
        conn.close()

    return loaded


def load_price_history_csv(csv_path):
    """Load a price history CSV file into PostgreSQL."""
    return _load_csv(csv_path, PRICE_HISTORY_UPSERT, [
        "symbol", "trade_date", "close_price", "adjusted_price",
        "change_amount", "change_percent",
        "matched_volume", "matched_value",
        "negotiated_volume", "negotiated_value",
        "open_price", "high_price", "low_price",
    ])


def load_foreign_trading_csv(csv_path):
    """Load a foreign trading CSV file into PostgreSQL."""
    return _load_csv(csv_path, FOREIGN_TRADING_UPSERT, [
        "symbol", "trade_date", "buy_volume", "buy_value",
        "sell_volume", "sell_value", "net_volume", "net_value",
        "room_remaining", "foreign_ownership_pct",
        "change_amount", "change_percent",
    ])


def load_proprietary_trading_csv(csv_path):
    """Load a proprietary trading CSV file into PostgreSQL."""
    return _load_csv(csv_path, PROPRIETARY_TRADING_UPSERT, [
        "symbol", "trade_date", "buy_volume", "buy_value",
        "sell_volume", "sell_value",
    ])


# Backward compatibility alias
load_csv_to_db = load_price_history_csv
