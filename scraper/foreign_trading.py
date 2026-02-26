import csv
import os

from scraper.config import FOREIGN_TRADING_URL
from scraper.utils import parse_change, parse_date, safe_float, safe_int, scrape_paginated

CSV_COLUMNS = [
    "symbol",
    "trade_date",
    "buy_volume",
    "buy_value",
    "sell_volume",
    "sell_value",
    "net_volume",
    "net_value",
    "room_remaining",
    "foreign_ownership_pct",
    "change_amount",
    "change_percent",
]


def parse_record(symbol, record):
    """Parse a single Khoi Ngoai API record into a flat dict for CSV."""
    change_amount, change_percent = parse_change(record.get("ThayDoi", ""))
    return {
        "symbol": symbol.upper(),
        "trade_date": parse_date(record.get("Ngay", "")),
        "buy_volume": safe_int(record.get("KLMua")),
        "buy_value": safe_float(record.get("GtMua")),
        "sell_volume": safe_int(record.get("KLBan")),
        "sell_value": safe_float(record.get("GtBan")),
        "net_volume": safe_int(record.get("KLGDRong")),
        "net_value": safe_float(record.get("GTDGRong")),
        "room_remaining": safe_int(record.get("RoomConLai")),
        "foreign_ownership_pct": safe_float(record.get("DangSoHuu")),
        "change_amount": change_amount,
        "change_percent": change_percent,
    }


def scrape_foreign_trading(symbol, start_date="", end_date=""):
    """
    Scrape all foreign trading data for a stock symbol and save to CSV.

    Returns:
        Path to the output CSV file.
    """
    symbol = symbol.upper()
    print(f"Scraping foreign trading for {symbol}...")

    def extract_records(data):
        return data["Data"]["Data"]

    raw_records, total_count = scrape_paginated(
        FOREIGN_TRADING_URL, symbol, start_date, end_date, extract_records
    )

    all_records = [parse_record(symbol, r) for r in raw_records]

    # Write CSV
    data_dir = os.path.join(os.path.dirname(os.path.dirname(__file__)), "data")
    os.makedirs(data_dir, exist_ok=True)
    csv_path = os.path.join(data_dir, f"{symbol}_foreign_trading.csv")

    with open(csv_path, "w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=CSV_COLUMNS)
        writer.writeheader()
        writer.writerows(all_records)

    print(f"  Saved {len(all_records)} records to {csv_path}")
    return csv_path
