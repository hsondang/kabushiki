import argparse
import os
import sys

from scraper.price_history import scrape_price_history
from scraper.foreign_trading import scrape_foreign_trading
from scraper.proprietary_trading import scrape_proprietary_trading
from db.loader import (
    load_price_history_csv,
    load_foreign_trading_csv,
    load_proprietary_trading_csv,
)

DATA_DIR = os.path.join(os.path.dirname(__file__), "data")

SCRAPERS = {
    "price": scrape_price_history,
    "foreign": scrape_foreign_trading,
    "proprietary": scrape_proprietary_trading,
}

LOADERS = {
    "price": load_price_history_csv,
    "foreign": load_foreign_trading_csv,
    "proprietary": load_proprietary_trading_csv,
}

CSV_SUFFIXES = {
    "price": "price_history",
    "foreign": "foreign_trading",
    "proprietary": "proprietary_trading",
}


def get_csv_path(symbol, data_type):
    return os.path.join(DATA_DIR, f"{symbol.upper()}_{CSV_SUFFIXES[data_type]}.csv")


def resolve_types(data_type):
    """Expand 'all' into the list of all types, or return a single-item list."""
    if data_type == "all":
        return list(SCRAPERS.keys())
    return [data_type]


def cmd_scrape(args):
    for dt in resolve_types(args.type):
        SCRAPERS[dt](args.symbol, args.start or "", args.end or "")


def cmd_load(args):
    for dt in resolve_types(args.type):
        csv_path = get_csv_path(args.symbol, dt)
        if not os.path.exists(csv_path):
            print(f"CSV file not found: {csv_path}")
            print(f"Run 'python main.py scrape {args.symbol} --type {dt}' first.")
            sys.exit(1)
        LOADERS[dt](csv_path)


def cmd_scrape_and_load(args):
    for dt in resolve_types(args.type):
        csv_path = SCRAPERS[dt](args.symbol, args.start or "", args.end or "")
        LOADERS[dt](csv_path)


def add_common_args(parser):
    parser.add_argument("symbol", help="Stock ticker symbol (e.g., HDB)")
    parser.add_argument(
        "--type",
        choices=["price", "foreign", "proprietary", "all"],
        default="price",
        help="Data type to process (default: price)",
    )


def main():
    parser = argparse.ArgumentParser(description="CafeF Stock Data Scraper")
    subparsers = parser.add_subparsers(dest="command", required=True)

    # scrape
    p_scrape = subparsers.add_parser("scrape", help="Scrape data to CSV")
    add_common_args(p_scrape)
    p_scrape.add_argument("--start", help="Start date (MM/DD/YYYY)")
    p_scrape.add_argument("--end", help="End date (MM/DD/YYYY)")
    p_scrape.set_defaults(func=cmd_scrape)

    # load
    p_load = subparsers.add_parser("load", help="Load CSV into PostgreSQL")
    add_common_args(p_load)
    p_load.set_defaults(func=cmd_load)

    # scrape-and-load
    p_both = subparsers.add_parser("scrape-and-load", help="Scrape then load into PostgreSQL")
    add_common_args(p_both)
    p_both.add_argument("--start", help="Start date (MM/DD/YYYY)")
    p_both.add_argument("--end", help="End date (MM/DD/YYYY)")
    p_both.set_defaults(func=cmd_scrape_and_load)

    args = parser.parse_args()
    args.func(args)


if __name__ == "__main__":
    main()
