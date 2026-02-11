import csv
import os

import psycopg2
from dotenv import load_dotenv

load_dotenv()

UPSERT_SQL = """
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


def load_csv_to_db(csv_path):
    """Load a price history CSV file into PostgreSQL."""
    init_schema()

    conn = get_connection()
    loaded = 0
    try:
        with conn.cursor() as cur:
            with open(csv_path, "r", encoding="utf-8") as f:
                reader = csv.DictReader(f)
                for row in reader:
                    cur.execute(UPSERT_SQL, (
                        row["symbol"],
                        row["trade_date"],
                        row["close_price"],
                        row["adjusted_price"],
                        row["change_amount"],
                        row["change_percent"],
                        row["matched_volume"],
                        row["matched_value"],
                        row["negotiated_volume"],
                        row["negotiated_value"],
                        row["open_price"],
                        row["high_price"],
                        row["low_price"],
                    ))
                    loaded += 1
        conn.commit()
        print(f"Loaded {loaded} records from {csv_path} into PostgreSQL.")
    finally:
        conn.close()

    return loaded
