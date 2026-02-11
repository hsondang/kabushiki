import argparse
import os
import sys

from scraper.price_history import scrape_price_history
from db.loader import load_csv_to_db


def get_csv_path(symbol):
    return os.path.join(os.path.dirname(__file__), "data", f"{symbol.upper()}_price_history.csv")


def cmd_scrape(args):
    scrape_price_history(args.symbol, args.start or "", args.end or "")


def cmd_load(args):
    csv_path = get_csv_path(args.symbol)
    if not os.path.exists(csv_path):
        print(f"CSV file not found: {csv_path}")
        print(f"Run 'python main.py scrape {args.symbol}' first.")
        sys.exit(1)
    load_csv_to_db(csv_path)


def cmd_scrape_and_load(args):
    csv_path = scrape_price_history(args.symbol, args.start or "", args.end or "")
    load_csv_to_db(csv_path)


def main():
    parser = argparse.ArgumentParser(description="CafeF Stock Data Scraper")
    subparsers = parser.add_subparsers(dest="command", required=True)

    # scrape
    p_scrape = subparsers.add_parser("scrape", help="Scrape price history to CSV")
    p_scrape.add_argument("symbol", help="Stock ticker symbol (e.g., HDB)")
    p_scrape.add_argument("--start", help="Start date (MM/DD/YYYY)")
    p_scrape.add_argument("--end", help="End date (MM/DD/YYYY)")
    p_scrape.set_defaults(func=cmd_scrape)

    # load
    p_load = subparsers.add_parser("load", help="Load CSV into PostgreSQL")
    p_load.add_argument("symbol", help="Stock ticker symbol (e.g., HDB)")
    p_load.set_defaults(func=cmd_load)

    # scrape-and-load
    p_both = subparsers.add_parser("scrape-and-load", help="Scrape then load into PostgreSQL")
    p_both.add_argument("symbol", help="Stock ticker symbol (e.g., HDB)")
    p_both.add_argument("--start", help="Start date (MM/DD/YYYY)")
    p_both.add_argument("--end", help="End date (MM/DD/YYYY)")
    p_both.set_defaults(func=cmd_scrape_and_load)

    args = parser.parse_args()
    args.func(args)


if __name__ == "__main__":
    main()
