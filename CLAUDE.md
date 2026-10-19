# ticket-sniper

A Python tool that watches ticket prices for one or more events across multiple resale platforms and fires an alert when a price drops to or below a set threshold. The 2026 FIFA World Cup was the first use case (the original watchlist still lists three World Cup games), but the tool itself is event-agnostic: any event with a SeatGeek listing and/or a SeatPick page can be added with a config edit.

---

## Status

- **Never deployed on any scheduler.** There is no GitHub Actions workflow and no Windows Scheduled Task in this repo. The tool only runs when someone runs `python tracker.py` by hand. Scheduling is Phase 7 in `PLAN.md` and is not built.
- **SeatGeek API key is mock.** `SEATGEEK_CLIENT_ID=mock` in `.env` makes `sources/seatgeek.py` return canned prices instead of hitting the real API. No real SeatGeek API key has been obtained.
- **Event IDs are placeholders.** Every `seatgeek.id` in `watchlist.toml` is `"TBD"`. The SeatPick slugs are unverified generic guesses, never confirmed against real pages.
- **SeatPick scraping works live.** Unlike SeatGeek, the scraper hits the real seatpick.com site even in "mock mode" runs, because there is no mock path for it.

---

## Vision

Ticket prices on the resale market are volatile and drop unpredictably. Manually checking platforms constantly is impractical. ticket-sniper watches the market and alerts the moment a price crosses a threshold, so the only job left is clicking buy.

---

## How It Works

Every event in `watchlist.toml` is checked against every source listed for it, at every quantity listed for it. The lowest price found across all sources for that (event, quantity) pair is compared against the event's threshold. If it's at or below the threshold, an alert fires to both phone (ntfy.sh push) and email (Gmail SMTP). Every run is logged regardless of whether an alert fires.

**SeatGeek API** (`sources/seatgeek.py`) — quantity-aware. For `quantity == 1` it hits `GET /2/events/{id}` and reads `stats.lowest_price`. For `quantity > 1` it hits `GET /2/listings?event_id={id}&quantity={quantity}` instead, so pricing reflects listings that can actually seat that many people together. **Untested assumption, flagged and unverified:** it is not confirmed whether the price returned by the listings endpoint for `quantity >= 2` is per-ticket or per-listing (i.e. total for all seats). This has never been checked against a real event because the client ID is still mock. Verify this before trusting any real qty>=2 alert. Supports a mock mode (`client_id == "mock"`) that returns canned prices without hitting the network, useful for testing the alert path end to end.

**SeatPick scraper** (`sources/seatpick.py`) — aggregator source, best-effort. Fetches `https://seatpick.com/{slug}`, adds `?qty={quantity}` to the URL when quantity is greater than 1, and parses the lowest price out of the HTML table with a "Low" column header. Has no mock mode; it always hits the live site. Returns `None` on any failure (bad status, missing table, network error) and never raises — a broken scrape must never crash the tool.

Both sources return the same contract: `{"price": float, "url": str, "source": str, "quantity": int} | None`.

---

## Repo Structure

```
ticket-sniper/
├── sources/
│   ├── seatgeek.py            # SeatGeek API adapter (mock mode + real API, qty-aware)
│   └── seatpick.py            # SeatPick scraper (aggregator, best-effort, always live)
├── tracker.py                 # Orchestrator — dispatches sources via a registry, compares prices, triggers alerts
├── notifier.py                # Alert delivery — ntfy.sh + Gmail SMTP
├── config.py                  # Env var loading (fail-fast) + watchlist.toml parsing/validation
├── watchlist.toml             # The actual watchlist: events, thresholds, quantities, sources
├── requirements.txt
├── .env.example
├── PLAN.md
└── CLAUDE.md
```

There is no `.github/workflows/` directory and no scheduled task anywhere. That is Phase 7, unbuilt.

---

## Stack

| Layer | Tool | Notes |
|---|---|---|
| Price data (primary) | SeatGeek API | Free `client_id` from developer.seatgeek.com; currently mock |
| Price data (aggregator) | SeatPick scraper | Aggregates SeatGeek, StubHub, Viagogo; always live, no mock |
| Scheduler | none yet | Manual `python tracker.py` only |
| Phone alerts | ntfy.sh | No account needed, HTTP POST |
| Email alerts | Gmail SMTP | App password via Google account settings |
| Language | Python 3.11+ | `requests`, `beautifulsoup4`, `python-dotenv`, stdlib `tomllib` |

---

## Configuration

Two layers, kept separate on purpose: `.env` for secrets, `watchlist.toml` for what to watch and at what price.

`config.py` loads both. It loads env vars first and raises `EnvironmentError` immediately if any required var is missing. Then it parses and validates `watchlist.toml` via `load_watchlist()`, exposing the result as `config.EVENTS`. Any schema problem in the TOML (missing field, unknown source key, bad type) raises `ValueError` immediately at import time — config errors crash, they do not get silently skipped.

`watchlist.toml` schema:

```toml
# Default ticket quantities checked per event, unless an event overrides it.
default_quantities = [1, 2]

[[events]]
name = "World Cup Final"
date = "2026-07-19"            # informational only, not read by the tracker
threshold = 500                 # dollars per ticket; alert fires at or below this
quantities = [1, 2]             # optional; falls back to default_quantities

[events.sources]
seatgeek = { id = "TBD" }
seatpick = { slug = "world-cup-final-tickets" }
```

Known source keys are `seatgeek` (needs `id`) and `seatpick` (needs `slug`), defined in `config.KNOWN_SOURCES`.

Required environment variables (`.env` locally, GitHub Actions secrets if this ever moves to CI):

| Var | Purpose |
|---|---|
| `SEATGEEK_CLIENT_ID` | SeatGeek API client ID, or `"mock"` for canned test prices |
| `GMAIL_USER` | Sending Gmail address |
| `GMAIL_APP_PASSWORD` | Gmail app password (not the account password) |
| `ALERT_EMAIL` | Address to receive alerts |
| `NTFY_TOPIC` | Private ntfy.sh topic name; anyone who knows it can push to your phone |

---

## Alert Format

Actual output from `notifier.py`, quantity label generic for any count (`"1 ticket"`, `"2 adjacent tickets"`, `"3 adjacent tickets"`, ...):

**ntfy push (phone), title:**
```
PRICE DROP: World Cup Final - 1 ticket
```

**ntfy push, body:**
```
🎟️ $210 via SeatGeek — below your $500 threshold
https://seatgeek.com/e/mock-event

SeatPick also showing: $7236
```

**Email subject:**
```
[ticket-sniper] World Cup Final — $210 (SeatGeek) — 1 ticket
```

**Email body:** the ntfy title and body concatenated.

---

## Running It

**Manual run (checks every event in `watchlist.toml`, fires real alerts if a threshold is crossed):**
```bash
python tracker.py
```

**Alert test path (sends one real ntfy push and one real test email, does not touch the watchlist):**
```bash
python notifier.py
```

**Config check (parses and prints the watchlist without running any checks):**
```bash
python config.py
```

---

## Adding a New Event (config-only)

Open `watchlist.toml`, copy an existing `[[events]]` block, and edit `name`, `date`, `threshold`, and the source IDs/slugs under `[events.sources]`. No code changes. Run `python config.py` to confirm it parses.

## Adding a New Source Site

1. Write `sources/<site>.py` with a `get_lowest_price(...)` function that returns `{"price": float, "url": str, "source": str, "quantity": int} | None` and never raises on a network or parse failure.
2. Add the site's name and required config fields to `config.KNOWN_SOURCES` in `config.py`.
3. Add one adapter function and one registry line in `tracker.py`'s `SOURCES` dict.
4. Reference the new source key under `[events.sources]` in `watchlist.toml`.

---

## Ground Rules

- **No secrets in code.** All credentials via env vars only, loaded through `config.py`.
- **Scraper failures are non-fatal.** SeatPick returns `None` on any failure, logs it, and the run continues on whatever other sources returned a price.
- **Config errors are fatal.** A bad `watchlist.toml` (unknown source key, missing threshold, etc.) crashes at startup with a clear message, on purpose.
- **ntfy topic is private.** Anyone with the topic name can push to your phone. Keep it out of the codebase; it lives in `.env` only.
