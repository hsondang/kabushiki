# CafeF Stock Data Scraping — Research Notes

## Overview

This document captures everything learned from reverse-engineering the CafeF "Lịch sử giá" (Price History) data tab for Vietnamese stocks. The goal was to understand how price history data is loaded on the page so we could scrape it efficiently — without needing browser automation (Selenium/Playwright) and instead using simple HTTP requests.

**Target page:** `https://cafef.vn/du-lieu/lich-su-giao-dich-hdb-1.chn`
**Stock symbol used for research:** `HDB`

---

## Key Insight: The Page Is Just a Shell

When you visit the CafeF URL above, your browser loads an HTML file that contains the page layout — the header, tabs, search box, and an empty table skeleton. **The actual price data is not in that HTML.** Instead, after the page loads, a piece of JavaScript runs silently in the background and fires a second, separate HTTP request to a different URL to fetch the data. The response comes back as JSON, and the JavaScript injects it into the table you see.

This pattern is called **Ajax** (Asynchronous JavaScript and XML). "Asynchronous" means it happens in the background without reloading the whole page. You've seen this in action on any website where content appears after the page loads — infinite scrolling, live search results, stock tickers updating — all of that is Ajax.

**The practical implication for scraping:** we don't need to scrape the HTML page at all. We can skip directly to the background JSON request and get clean, structured data with zero HTML parsing.

---

## How to Find the Hidden API Endpoint Using Chrome DevTools

This is the core technique. Every Ajax request a page makes is visible in the browser's Network tab. Here's how to find it:

### Step 1 — Open DevTools on the Target Page

Navigate to the CafeF page, then open DevTools:
- **Windows/Linux:** Press `F12`  
- **Mac:** Press `Cmd + Option + I`

Then click the **Network** tab at the top of the DevTools panel.

### Step 2 — Filter for XHR/Fetch Requests Only

In the Network tab you'll see a filter bar:

```
All  |  Fetch/XHR  |  JS  |  CSS  |  Img  |  Media  |  Font  |  Doc  |  WS  |  Other
```

Click **Fetch/XHR**. This hides everything except background data requests (images, CSS, fonts are all noise — we only care about data).

### Step 3 — Trigger the Data Load

With the Network tab open and filtered:
1. Either **refresh the page** (`F5`), or
2. Type a stock symbol (e.g. `HDB`) in the search box and click **Xem**

You will see new requests appear in the list as the page loads data.

### Step 4 — Spot the Right Request

Look for a request with `PriceHistory.ashx` in its name. Click on it. A side panel opens with several sub-tabs:

| Sub-tab | What it shows |
|---|---|
| **Headers** | The full request URL with all parameters |
| **Preview** | The JSON response, nicely formatted and explorable |
| **Response** | The raw JSON text |
| **Timing** | How long the request took |

The **Headers** and **Preview** tabs are the two you care about most.

### Step 5 — Read the Parameters from the URL

In the Headers tab, the full Request URL looks like this:

```
https://cafef.vn/du-lieu/Ajax/PageNew/DataHistory/PriceHistory.ashx
  ?Symbol=HDB
  &StartDate=
  &EndDate=
  &PageIndex=1
  &PageSize=20
```

Every `?key=value` pair is a parameter the page sent to the server. This tells you exactly how to call the API yourself.

---

## The API Endpoint

```
GET https://cafef.vn/du-lieu/Ajax/PageNew/DataHistory/PriceHistory.ashx
```

### Parameters

| Parameter | Type | Required | Notes |
|---|---|---|---|
| `Symbol` | string | Yes | Stock ticker, e.g. `HDB`, `VNM`, `FPT` |
| `StartDate` | string | No | Format: `MM/DD/YYYY`. Leave empty for all history |
| `EndDate` | string | No | Format: `MM/DD/YYYY`. Leave empty for all history |
| `PageIndex` | int | Yes | 1-based. First page = `1` |
| `PageSize` | int | Yes | Number of rows to return per request. Website default is `20` |

### Example Request

```
GET https://cafef.vn/du-lieu/Ajax/PageNew/DataHistory/PriceHistory.ashx?Symbol=HDB&StartDate=&EndDate=&PageIndex=1&PageSize=20
```

### Why `.ashx`?

The `.ashx` extension means the server is running **ASP.NET** (Microsoft's web framework). An `.ashx` file is an "HTTP Handler" — a lightweight server-side script that processes a request and returns a response, with no HTML page involved. It's the equivalent of a `.php` or `.py` API endpoint, just in the Microsoft ecosystem. From a scraping perspective it behaves identically to any other REST API endpoint.

---

## The JSON Response

The API returns a JSON object with this structure:

```json
{
  "Data": {
    "TotalCount": 2019,
    "Data": [
      {
        "Ngay": "10/02/2026",
        "GiaDieuChinh": 26.8,
        "GiaDongCua": 26.8,
        "ThayDoi": "0(0.00 %)",
        "KhoiLuongKhopLenh": 12368700,
        "GiaTriKhopLenh": 330681805000,
        "KLThoaThuan": 0,
        "GtThoaThuan": 0,
        "GiaMoCua": 26.85,
        "GiaCaoNhat": 26.9,
        "GiaThapNhat": 26
      },
      ...
    ]
  }
}
```

### Field Reference

| JSON Field | Vietnamese Label | English Meaning | Notes |
|---|---|---|---|
| `TotalCount` | — | Total rows across all pages | Key for pagination logic |
| `Ngay` | Ngày | Trade date | Format: `DD/MM/YYYY` — note day/month order, opposite of URL params |
| `GiaDieuChinh` | Điều chỉnh | Adjusted close price | Thousand VND |
| `GiaDongCua` | Đóng cửa | Close price | Thousand VND |
| `ThayDoi` | Thay đổi | Change | String encoding both amount and %, e.g. `"0.3(1.13 %)"` — must be parsed |
| `KhoiLuongKhopLenh` | Khối lượng (Khớp lệnh) | Matched order volume | Number of shares |
| `GiaTriKhopLenh` | Giá trị (Khớp lệnh) | Matched order value | VND (not thousands) |
| `KLThoaThuan` | Khối lượng (Thỏa thuận) | Negotiated volume | Usually 0 for most stocks |
| `GtThoaThuan` | Giá trị (Thỏa thuận) | Negotiated value | Usually 0 for most stocks |
| `GiaMoCua` | Mở cửa | Open price | Thousand VND |
| `GiaCaoNhat` | Cao nhất | High price | Thousand VND |
| `GiaThapNhat` | Thấp nhất | Low price | Thousand VND |

### Data Quirks to Handle

1. **`ThayDoi` is a string, not a number.** It encodes both the change amount and percentage in one field: `"0.3(1.13 %)"` or `"-1.05(-3.81 %)"`. You need to parse this with a regex to split into `change_amount` and `change_percent`.

2. **Date format mismatch.** The URL parameters take `MM/DD/YYYY` (American format) but the `Ngay` field in the response comes back as `DD/MM/YYYY` (European/Vietnamese format). Don't mix them up.

3. **`GiaTriKhopLenh` is in raw VND, not thousands.** All prices are in thousand VND, but this value field is in full VND. A value of `330681805000` = ~330.68 billion VND.

---

## Pagination Logic

`TotalCount` is the key. When the scraper gets the first response, it reads this number to know how many total rows exist, then calculates how many more requests are needed:

```python
# Example with PageSize=100
total_rows = 2019
page_size = 100
total_pages = math.ceil(total_rows / page_size)  # = 21 pages

for page_index in range(1, total_pages + 1):
    # fetch page_index, collect rows
    # sleep 1-2 seconds between requests (politeness)
```

Without `TotalCount`, you'd have to keep requesting pages until you get an empty response — less clean and more error-prone.

---

## Why Not Scrape the HTML Page Directly?

You could parse the HTML table, but it has serious disadvantages:

| | Ajax API approach | HTML scraping approach |
|---|---|---|
| Data format | Clean JSON, typed values | Raw HTML strings, everything needs parsing |
| Reliability | Stable — APIs change rarely | Fragile — any CSS class rename breaks your scraper |
| Speed | 100 rows per request | 20 rows per page (website default) |
| Complexity | Simple `requests.get()` | Needs HTML parser (BeautifulSoup) + CSS selectors |
| Automation needed | None | None (but some scrapers require Selenium for JS-rendered pages) |

The API approach is strictly better in every dimension here.

---

## Extensibility to Other Tabs

The page has 6 tabs under "Dữ liệu lịch sử":

1. **Lịch sử giá** ← this document covers this tab
2. Thống kê đặt lệnh
3. Khối ngoại
4. Tự doanh
5. Khớp lệnh theo phiên
6. Cổ đông & Nội bộ

Each tab almost certainly has its own `.ashx` endpoint under the same `/du-lieu/Ajax/PageNew/DataHistory/` path. To find them, repeat the same DevTools process: click each tab, watch the Fetch/XHR requests appear, and note the new endpoint and its parameters. The scraper architecture is designed to accommodate these as additional modules under `scraper/`.

---

## Verification Against the Screenshot

The first row in the captured JSON matches exactly what's displayed in the website screenshot:

| Field | API value | Website display |
|---|---|---|
| Date | `10/02/2026` | `10/02/2026` |
| Close | `26.8` | `26.8` |
| Adjusted | `26.8` | `26.8` |
| Change | `0(0.00 %)` | `0(0.00 %)` |
| Volume | `12,368,700` | `12,368,700` |
| Open | `26.85` | `26.85` |
| High | `26.9` | `26.9` |
| Low | `26` | `26` |

The data pipeline (API → CSV → PostgreSQL) faithfully mirrors what CafeF displays to users.
