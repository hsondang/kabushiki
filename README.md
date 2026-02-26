# kabushiki

Scrapes historical stock data from [cafef.vn](https://cafef.vn) for Vietnamese stock market tickers.

## Currently supported

- **Tab 1 - Lich su gia (Price History)**: Daily OHLC prices, volume, and negotiated trades

## Setup

### Prerequisites
- Python 3.12+ (via pyenv)
- Docker (for PostgreSQL)

### Install

```bash
pyenv activate web-scraping
pip install -r requirements.txt
```

### Database

```bash
cp .env.example .env   # edit credentials if needed
docker compose up -d   # starts PostgreSQL 16
```

The schema is auto-applied on first container start via `db/schema.sql`.

## Usage

```bash
# Scrape price history to CSV
python main.py scrape HDB

# Scrape with date range (MM/DD/YYYY)
python main.py scrape HDB --start 01/01/2024 --end 12/31/2025

# Load CSV into PostgreSQL
python main.py load HDB

# Scrape and load in one step
python main.py scrape-and-load HDB
```

Output CSVs are saved to `data/{SYMBOL}_price_history.csv`.

## Data source

- **API endpoint**: `cafef.vn/du-lieu/Ajax/PageNew/DataHistory/PriceHistory.ashx`
- **URL pattern**: `cafef.vn/du-lieu/lich-su-giao-dich-{ticker}-{tab}.chn` where tab 1-6 maps to:
  1. Lich su gia (Price History)
  2. Thong ke dat lenh (Order Statistics)
  3. Khoi ngoai (Foreign Trading)
  4. Tu doanh (Proprietary Trading)
  5. Khop lenh theo phien (Intraday Matching)
  6. Co dong & Noi bo (Shareholders & Insiders)

## Project structure

```
kabushiki/
├── main.py                   # CLI entry point
├── scraper/
│   ├── config.py             # API URL, headers, rate limit
│   └── price_history.py      # Price history scraper
├── db/
│   ├── schema.sql            # PostgreSQL schema
│   └── loader.py             # CSV -> PostgreSQL loader
├── data/                     # Output CSVs (gitignored)
├── docker-compose.yml        # PostgreSQL container
├── requirements.txt          # Python dependencies
└── .env.example              # DB config template
```
