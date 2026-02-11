import csv
import math
import os
import re
import time
from datetime import datetime

import requests

from scraper.config import BASE_URL, HEADERS, PAGE_SIZE, REQUEST_DELAY

CSV_COLUMNS = [
    "symbol",
    "trade_date",
    "close_price",
    "adjusted_price",
    "change_amount",
    "change_percent",
    "matched_volume",
    "matched_value",
    "negotiated_volume",
    "negotiated_value",
    "open_price",
    "high_price",
    "low_price",
]


def parse_change(raw):
    """Parse ThayDoi field like '0.3(1.13 %)' into (amount, percent)."""
    if not raw or raw.strip() == "":
        return 0.0, 0.0
    raw = raw.strip()
    match = re.match(r"([+-]?[\d.]+)\(([+-]?[\d.]+)\s*%\s*\)", raw)
    if match:
        return float(match.group(1)), float(match.group(2))
    # Fallback: try parsing as just a number
    try:
        return float(raw), 0.0
    except (ValueError, TypeError):
        return 0.0, 0.0


def parse_date(raw):
    """Parse date from DD/MM/YYYY to YYYY-MM-DD."""
    try:
        return datetime.strptime(raw.strip(), "%d/%m/%Y").strftime("%Y-%m-%d")
    except (ValueError, AttributeError):
        return raw


def safe_float(val):
    """Safely convert to float, returning 0.0 on failure."""
    try:
        return float(val) if val is not None else 0.0
    except (ValueError, TypeError):
        return 0.0


def safe_int(val):
    """Safely convert to int, returning 0 on failure."""
    try:
        return int(val) if val is not None else 0
    except (ValueError, TypeError):
        return 0


def parse_record(symbol, record):
    """Parse a single API record into a flat dict for CSV."""
    change_amount, change_percent = parse_change(record.get("ThayDoi", ""))
    return {
        "symbol": symbol.upper(),
        "trade_date": parse_date(record.get("Ngay", "")),
        "close_price": safe_float(record.get("GiaDongCua")),
        "adjusted_price": safe_float(record.get("GiaDieuChinh")),
        "change_amount": change_amount,
        "change_percent": change_percent,
        "matched_volume": safe_int(record.get("KhoiLuongKhopLenh")),
        "matched_value": safe_float(record.get("GiaTriKhopLenh")),
        "negotiated_volume": safe_int(record.get("KLThoaThuan")),
        "negotiated_value": safe_float(record.get("GtThoaThuan")),
        "open_price": safe_float(record.get("GiaMoCua")),
        "high_price": safe_float(record.get("GiaCaoNhat")),
        "low_price": safe_float(record.get("GiaThapNhat")),
    }


def fetch_page(symbol, page_index, start_date="", end_date=""):
    """Fetch a single page of price history from the API."""
    params = {
        "Symbol": symbol.upper(),
        "StartDate": start_date,
        "EndDate": end_date,
        "PageIndex": page_index,
        "PageSize": PAGE_SIZE,
    }
    resp = requests.get(BASE_URL, params=params, headers=HEADERS, timeout=30)
    resp.raise_for_status()
    return resp.json()


def scrape_price_history(symbol, start_date="", end_date=""):
    """
    Scrape all price history for a stock symbol and save to CSV.

    Args:
        symbol: Stock ticker (e.g., "HDB")
        start_date: Optional start date in MM/DD/YYYY format
        end_date: Optional end date in MM/DD/YYYY format

    Returns:
        Path to the output CSV file.
    """
    symbol = symbol.upper()
    print(f"Scraping price history for {symbol}...")

    # First request to get total count
    data = fetch_page(symbol, 1, start_date, end_date)
    if not data.get("Success"):
        raise RuntimeError(f"API returned error: {data.get('Message')}")

    total_count = data["Data"]["TotalCount"]
    total_pages = math.ceil(total_count / PAGE_SIZE)
    print(f"  Total records: {total_count}, pages: {total_pages}")

    all_records = []

    # Parse first page
    for record in data["Data"]["Data"]:
        all_records.append(parse_record(symbol, record))

    # Fetch remaining pages
    for page in range(2, total_pages + 1):
        print(f"  Fetching page {page}/{total_pages}...")
        time.sleep(REQUEST_DELAY)
        data = fetch_page(symbol, page, start_date, end_date)
        if data.get("Success") and data["Data"]["Data"]:
            for record in data["Data"]["Data"]:
                all_records.append(parse_record(symbol, record))

    # Write CSV
    data_dir = os.path.join(os.path.dirname(os.path.dirname(__file__)), "data")
    os.makedirs(data_dir, exist_ok=True)
    csv_path = os.path.join(data_dir, f"{symbol}_price_history.csv")

    with open(csv_path, "w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=CSV_COLUMNS)
        writer.writeheader()
        writer.writerows(all_records)

    print(f"  Saved {len(all_records)} records to {csv_path}")
    return csv_path
