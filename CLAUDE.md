# CLAUDE.md

## Project overview
CafeF stock data scraper for Vietnamese stock market. Scrapes historical data from cafef.vn's AJAX API and stores it in CSV and PostgreSQL.

## Tech stack
- Python 3.12 (`uv`-managed `.venv`)
- PostgreSQL 16 (via Docker)
- Key libraries: requests, psycopg2-binary, python-dotenv

## Commands
- `uv python install 3.12` — install the project Python version
- `uv python pin 3.12` — create a local `.python-version` for `uv`
- `uv venv` — create the local virtual environment
- `source .venv/bin/activate` — activate the virtual environment
- `uv pip install -r requirements.txt` — install Python dependencies
- `python main.py scrape {SYMBOL}` — scrape price history to CSV
- `python main.py load {SYMBOL}` — load CSV into PostgreSQL
- `python main.py scrape-and-load {SYMBOL}` — both in one step
- `docker compose up -d` — start PostgreSQL

## Architecture
- `scraper/config.py` — API endpoint, headers, rate limiting constants
- `scraper/price_history.py` — fetches paginated JSON from CafeF API, parses records, writes CSV
- `db/loader.py` — reads CSV and upserts into PostgreSQL (idempotent via ON CONFLICT)
- `db/schema.sql` — table definitions, auto-applied by Docker on first run
- `main.py` — argparse CLI with scrape/load/scrape-and-load subcommands

## Key patterns
- API returns JSON at `cafef.vn/du-lieu/Ajax/PageNew/DataHistory/PriceHistory.ashx`
- Pagination: `PageIndex` (1-based), `PageSize`, response includes `TotalCount`
- Date format from API: DD/MM/YYYY, stored as YYYY-MM-DD
- Rate limiting: 1.5s delay between requests (configurable in config.py)
- DB upsert uses UNIQUE(symbol, trade_date) constraint for idempotency

## Future work
- Tabs 2-6 scrapers (order stats, foreign trading, proprietary, intraday, shareholders)
