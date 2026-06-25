# ticket-sniper — Build Plan

Explicit build order, phase by phase. Complete each phase fully before moving to the next. Each phase ends with a working, testable state.

---

## Phase 1 — Repo Scaffolding

Create the full directory and file structure with empty stubs. Nothing runs yet, but the skeleton is in place.

**Tasks:**
- [x] Create repo `ticket-sniper` on GitHub (public)
- [x] Create the following empty files:
   - `tracker.py`
   - `notifier.py`
   - `config.py`
   - `sources/__init__.py`
   - `sources/seatgeek.py`
   - `sources/seatpick.py`
   - `requirements.txt`
   - `.env.example`
   - `.gitignore` (ignore `.env`)
   - `CLAUDE.md`
   - `PLAN.md`
- [x] Populate `requirements.txt`:
   ```
   requests
   beautifulsoup4
   python-dotenv
   ```
- [x] Populate `.env.example`:
   ```
   SEATGEEK_CLIENT_ID=your_id_here
   GMAIL_USER=you@gmail.com
   GMAIL_APP_PASSWORD=xxxx xxxx xxxx xxxx
   ALERT_EMAIL=you@gmail.com
   ```
- [x] Populate `.gitignore`:
   ```
   .env
   __pycache__/
   *.pyc
   ```

**Done when:** Repo exists on GitHub with all files committed.

---

## Phase 2 — Config

Build `config.py` so all settings live in one place and credentials load cleanly from the environment.

**Tasks:**
- [ ] Write `config.py`:
   - Load env vars via `python-dotenv` at the top
   - Define `WATCHLIST` with placeholder SeatGeek IDs and SeatPick slugs for at least 2 World Cup games
   - Define `NTFY_TOPIC`, `SEATGEEK_CLIENT_ID`, `GMAIL_USER`, `GMAIL_APP_PASSWORD`, `ALERT_EMAIL` — all loaded from `os.environ`
   - Raise a clear `EnvironmentError` at startup if any required env var is missing
- [ ] Create `.env` locally (not committed) with real values for development

**Done when:** `python config.py` runs without error and prints loaded config cleanly.

---

## Phase 3 — SeatGeek Source

Build and test the SeatGeek API fetcher in isolation.

**Tasks:**
- [ ] Write `sources/seatgeek.py`:
   - Function: `get_lowest_price(seatgeek_id: str, client_id: str) -> dict | None`
   - Hits `GET https://api.seatgeek.com/2/events/{id}?client_id=...`
   - Extracts `stats.lowest_price` from the response
   - Returns `{"price": float, "url": str, "source": "SeatGeek"}` on success
   - Returns `None` on any failure (bad status, missing field, network error) — logs the error
- [ ] Find real SeatGeek event IDs for the games in the watchlist:
   - Use `GET /events?q=world+cup+2026&type=sports&client_id=...` to search
   - Update `WATCHLIST` in `config.py` with real IDs
- [ ] Test manually: run a quick script that imports and calls `get_lowest_price()` and prints the result

**Done when:** `get_lowest_price()` returns a real price for at least one World Cup game.

---

## Phase 4 — SeatPick Source

Build and test the SeatPick scraper in isolation.

**Tasks:**
- [ ] Inspect `https://seatpick.com/{slug}` in a browser — find the HTML element that holds the lowest price
- [ ] Write `sources/seatpick.py`:
   - Function: `get_lowest_price(slug: str) -> dict | None`
   - Fetches `https://seatpick.com/{slug}` with a realistic `User-Agent` header
   - Parses the lowest price using BeautifulSoup
   - Strips `$` and commas, casts to float
   - Returns `{"price": float, "url": str, "source": "SeatPick"}` on success
   - Returns `None` on any exception or missing price — logs a warning, never raises
- [ ] Find real SeatPick slugs for the games in the watchlist and update `config.py`
- [ ] Test manually: call `get_lowest_price()` and print the result

**Done when:** `get_lowest_price()` returns a real price for at least one World Cup game.

---

## Phase 5 — Notifier

Build and test both alert channels in isolation.

**Tasks:**
- [ ] Write `notifier.py`:
   - `send_ntfy(message: str) -> None` — HTTP POST to `https://ntfy.sh/{NTFY_TOPIC}` with the message as body
   - `send_email(subject: str, body: str) -> None` — Gmail SMTP using `smtplib`, TLS on port 587
   - `send_alert(game_name: str, price: float, url: str, source: str, all_prices: dict) -> None` — formats the message and calls both `send_ntfy` and `send_email`
- [ ] Format the alert message as specified in `CLAUDE.md`
- [ ] Test both channels manually:
   - Call `send_ntfy("test message")` → confirm push arrives on phone
   - Call `send_email("test subject", "test body")` → confirm email arrives in inbox

**Done when:** Both a phone push and an email land successfully in test runs.

---

## Phase 6 — Tracker (Orchestrator)

Wire everything together in `tracker.py`.

**Tasks:**
- [ ] Write `tracker.py`:
   - Import `config`, both sources, and `notifier`
   - Loop through `WATCHLIST`
   - For each game: call `seatgeek.get_lowest_price()` and `seatpick.get_lowest_price()` 
   - Collect all non-`None` results, find the minimum price across both
   - If minimum price ≤ game's threshold: call `notifier.send_alert()` with the winning result and all prices for context
   - Log every run: timestamp, game name, prices from each source, whether alert fired
   - If all sources return `None` for a game: log a warning, skip — do not alert
- [ ] Run `tracker.py` end-to-end locally:
   - Temporarily lower a threshold below current market price to force an alert
   - Confirm both ntfy push and email arrive with correct content
   - Restore threshold to real value

**Done when:** Full end-to-end run works locally, alert fires correctly when threshold is crossed.

---

## Phase 7 — GitHub Actions

Deploy the scheduler so the tool runs automatically every 15 minutes in the cloud.

**Tasks:**
- [ ] Create `.github/workflows/check_prices.yml`:
   ```yaml
   name: Check Ticket Prices

   on:
     schedule:
       - cron: '*/15 * * * *'
     workflow_dispatch:

   jobs:
     check:
       runs-on: ubuntu-latest
       steps:
         - uses: actions/checkout@v4
         - uses: actions/setup-python@v5
           with:
             python-version: '3.11'
         - run: pip install -r requirements.txt
         - run: python tracker.py
           env:
             SEATGEEK_CLIENT_ID: ${{ secrets.SEATGEEK_CLIENT_ID }}
             GMAIL_USER: ${{ secrets.GMAIL_USER }}
             GMAIL_APP_PASSWORD: ${{ secrets.GMAIL_APP_PASSWORD }}
             ALERT_EMAIL: ${{ secrets.ALERT_EMAIL }}
   ```
- [ ] Add all four secrets to GitHub repo settings (Settings → Secrets and variables → Actions)
- [ ] Trigger a manual run via `workflow_dispatch` to verify it works in CI
- [ ] Check the Actions run log — confirm prices are logged, no errors

**Done when:** Manual workflow run completes successfully with prices logged in the Actions output.

---

## Phase 8 — Validation & Hardening

Confirm everything is solid before leaving it to run unattended.

**Tasks:**
- [ ] Let the scheduler run for 2–3 cycles (30–45 min) and check the Actions run logs
- [ ] Confirm SeatPick scraper graceful fallback: temporarily break the slug in config, verify run completes on SeatGeek-only with a logged warning (not a crash)
- [ ] Confirm threshold alert end-to-end one more time in CI: temporarily lower a threshold, trigger `workflow_dispatch`, confirm ntfy + email both arrive
- [ ] Restore correct thresholds
- [ ] Update `WATCHLIST` in `config.py` with all remaining World Cup games you want to track

**Done when:** Three consecutive automated runs complete cleanly in Actions logs with no errors.
