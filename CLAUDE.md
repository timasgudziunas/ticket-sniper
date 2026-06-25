# ticket-sniper

A Python tool that monitors 2026 FIFA World Cup ticket prices across multiple resale platforms and fires instant alerts when prices drop below a set threshold. Runs on a GitHub Actions cron schedule every 15 minutes — completely free on a public repo.

---

## Vision

Ticket prices on the resale market are volatile and drop unpredictably, especially for lower-demand group stage games. Manually checking platforms constantly is impractical. ticket-sniper watches the market 24/7 and alerts instantly the moment a price crosses a threshold — so the only job left is clicking buy.

The tool is scoped to the 2026 FIFA World Cup but is architected to be reusable for any ticketed event on SeatGeek or SeatPick.

---

## How It Works

Two data sources run on every check. The lowest price found across both is compared against a per-game threshold. If it's at or below the threshold, an alert fires to both phone (ntfy.sh push) and email (Gmail SMTP). Every run is logged regardless of whether an alert fires.

**SeatGeek API** — primary, stable source. Reliable programmatic access with a free public API. Never breaks. Falls back gracefully if the scraper fails.

**SeatPick scraper** — aggregator source. SeatPick pulls listings from SeatGeek, StubHub, Viagogo, and others into one page — meaning it often surfaces a lower price than any single platform. Scraped via `requests` + `BeautifulSoup`. Treated as best-effort: if the scrape fails, the run continues on SeatGeek data only and logs the failure. A broken scraper must never crash the tool.

---

## Repo Structure

```
ticket-sniper/
├── .github/
│   └── workflows/
│       └── check_prices.yml   # GitHub Actions cron scheduler (every 15 min)
├── sources/
│   ├── seatgeek.py            # SeatGeek API fetcher (primary)
│   └── seatpick.py            # SeatPick scraper (aggregator, best-effort)
├── tracker.py                 # Orchestrator — runs sources, compares prices, triggers alerts
├── notifier.py                # Alert delivery — ntfy.sh + Gmail SMTP
├── config.py                  # Watchlist, thresholds, env var refs
├── requirements.txt
├── .env.example
├── PLAN.md
└── CLAUDE.md
```

---

## Stack

| Layer | Tool | Notes |
|---|---|---|
| Price data (primary) | SeatGeek API | Free `client_id` from developer.seatgeek.com |
| Price data (aggregator) | SeatPick scraper | Aggregates SeatGeek, StubHub, Viagogo |
| Scheduler | GitHub Actions cron | Every 15 min, free on public repos |
| Phone alerts | ntfy.sh | No account needed, HTTP POST |
| Email alerts | Gmail SMTP | App password via Google account settings |
| Language | Python 3.11+ | `requests`, `beautifulsoup4`, `smtplib` (stdlib) |

---

## Configuration

`config.py` holds the watchlist and credentials references. Credentials are never hardcoded — always loaded from environment variables (GitHub Actions secrets in CI, `.env` locally).

```python
WATCHLIST = [
    {
        "name": "Czech Republic vs South Africa",
        "seatgeek_id": "XXXXX",
        "seatpick_slug": "czech-republic-vs-south-africa-tickets",
        "threshold": 200,
    },
]

NTFY_TOPIC = "ticket-sniper-timas"   # private — treat like a password
SEATGEEK_CLIENT_ID = None            # from env: SEATGEEK_CLIENT_ID
GMAIL_USER = None                    # from env: GMAIL_USER
GMAIL_APP_PASSWORD = None            # from env: GMAIL_APP_PASSWORD
ALERT_EMAIL = None                   # from env: ALERT_EMAIL
```

---

## Alert Format

**ntfy push (phone):**
```
🎟️ PRICE DROP: Czech Republic vs South Africa
$187 via SeatPick (cross-platform low) — below your $200 threshold
https://seatpick.com/...

SeatGeek also showing: $214
```

**Email subject:**
```
[ticket-sniper] Czech Republic vs South Africa — $187 (SeatPick)
```

---

## API & Scraping References

**SeatGeek API** — base URL: `https://api.seatgeek.com/2/`
- `GET /events/{id}?client_id=...` — fetch event; use `stats.lowest_price`
- `GET /events?q=world+cup+2026&type=sports&client_id=...` — search to find event IDs

**SeatPick scraper** — base URL: `https://seatpick.com/`
- Event pages: `https://seatpick.com/{slug}`
- Parse the lowest price from the listing header using BeautifulSoup
- Always set a realistic `User-Agent` header
- Strip `$` and commas before casting to float
- Return `None` on any failure — never raise

---

## GitHub Actions Secrets

Set under **Settings → Secrets and variables → Actions**:

| Secret | Description |
|---|---|
| `SEATGEEK_CLIENT_ID` | From developer.seatgeek.com |
| `GMAIL_USER` | Sending Gmail address |
| `GMAIL_APP_PASSWORD` | Gmail app password (not account password) |
| `ALERT_EMAIL` | Address to receive alerts |

---

## Local Development

```bash
pip install requests beautifulsoup4 python-dotenv
cp .env.example .env
python tracker.py
```

---

## Ground Rules

- **No secrets in code.** All credentials via env vars only.
- **Scraper failures are non-fatal.** Log them, fall back to SeatGeek, keep running.
- **Public repo.** GitHub Actions cron is unlimited free on public repos — keep it public, keep secrets in GitHub's secrets manager.
- **15-minute cadence.** SeatGeek rate limits are generous; SeatPick scraping at this cadence is fine. Don't go below 5 minutes.
- **World Cup ends July 19.** GitHub disables scheduled workflows after 60 days of repo inactivity — push a commit if needed before the deadline.
- **ntfy topic is private.** Anyone with the topic name can push to your phone. Keep it out of the codebase.