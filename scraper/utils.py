import math
import re
import time
from datetime import datetime

import requests

from scraper.config import HEADERS, PAGE_SIZE, REQUEST_DELAY


def parse_change(raw):
    """Parse ThayDoi field like '0.3(1.13 %)' into (amount, percent)."""
    if not raw or raw.strip() == "":
        return 0.0, 0.0
    raw = raw.strip()
    match = re.match(r"([+-]?[\d.]+)\(([+-]?[\d.]+)\s*%\s*\)", raw)
    if match:
        return float(match.group(1)), float(match.group(2))
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


def fetch_page(url, symbol, page_index, start_date="", end_date=""):
    """Fetch a single page of data from a CafeF API endpoint."""
    params = {
        "Symbol": symbol.upper(),
        "StartDate": start_date,
        "EndDate": end_date,
        "PageIndex": page_index,
        "PageSize": PAGE_SIZE,
    }
    resp = requests.get(url, params=params, headers=HEADERS, timeout=30)
    resp.raise_for_status()
    return resp.json()


def scrape_paginated(url, symbol, start_date, end_date, extract_records):
    """
    Generic paginated scraper for CafeF endpoints.

    Args:
        url: API endpoint URL
        symbol: Stock ticker
        start_date: Start date (MM/DD/YYYY) or empty string
        end_date: End date (MM/DD/YYYY) or empty string
        extract_records: Function that takes the API response dict and returns
                         the list of records for that page.

    Returns:
        Tuple of (all_raw_records, total_count)
    """
    symbol = symbol.upper()

    data = fetch_page(url, symbol, 1, start_date, end_date)
    if not data.get("Success"):
        raise RuntimeError(f"API returned error: {data.get('Message')}")

    total_count = data["Data"]["TotalCount"]
    total_pages = math.ceil(total_count / PAGE_SIZE)
    print(f"  Total records: {total_count}, pages: {total_pages}")

    all_records = list(extract_records(data))

    for page in range(2, total_pages + 1):
        print(f"  Fetching page {page}/{total_pages}...")
        time.sleep(REQUEST_DELAY)
        data = fetch_page(url, symbol, page, start_date, end_date)
        if data.get("Success"):
            records = extract_records(data)
            if records:
                all_records.extend(records)

    return all_records, total_count
