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
- [x] Write `config.py`:
   - Load env vars via `python-dotenv` at the top
   - Define `WATCHLIST` with placeholder SeatGeek IDs and SeatPick slugs for at least 2 World Cup games
   - Define `NTFY_TOPIC`, `SEATGEEK_CLIENT_ID`, `GMAIL_USER`, `GMAIL_APP_PASSWORD`, `ALERT_EMAIL` — all loaded from `os.environ`
   - Raise a clear `EnvironmentError` at startup if any required env var is missing
- [x] Create `.env` locally (not committed) with real values for development

**Done when:** `python config.py` runs without error and prints loaded config cleanly.

---

## Phase 3 — SeatGeek Source

Build and test the SeatGeek API fetcher in isolation.

**Tasks:**
- [x] Write `sources/seatgeek.py`:
   - Function: `get_lowest_price(seatgeek_id: str, client_id: str) -> dict | None`
   - Hits `GET https://api.seatgeek.com/2/events/{id}?client_id=...`
   - Extracts `stats.lowest_price` from the response
   - Returns `{"price": float, "url": str, "source": "SeatGeek"}` on success
   - Returns `None` on any failure (bad status, missing field, network error) — logs the error
- [ ] Find real SeatGeek event IDs for the games in the watchlist: *(blocked — API key pending)*
   - Use `GET /events?q=world+cup+2026&type=sports&client_id=...` to search
   - Update `WATCHLIST` in `config.py` with real IDs
- [x] Test manually: run a quick script that imports and calls `get_lowest_price()` and prints the result

**Done when:** `get_lowest_price()` returns a real price for at least one World Cup game.

> **Note (2026-07-18 audit):** never actually met. `SEATGEEK_CLIENT_ID` has been set to `"mock"` in `.env` since this phase, so `sources/seatgeek.py` has never returned a real price. The real API code path exists (see the qty==1 and qty>1 branches) but is completely unverified against the live API.

---

## Phase 4 — SeatPick Source

Build and test the SeatPick scraper in isolation.

**Tasks:**
- [x] Inspect `https://seatpick.com/{slug}` in a browser — find the HTML element that holds the lowest price
- [x] Write `sources/seatpick.py`:
   - Function: `get_lowest_price(slug: str) -> dict | None`
   - Fetches `https://seatpick.com/{slug}` with a realistic `User-Agent` header
   - Parses the lowest price using BeautifulSoup
   - Strips `$` and commas, casts to float
   - Returns `{"price": float, "url": str, "source": "SeatPick"}` on success
   - Returns `None` on any exception or missing price — logs a warning, never raises
- [x] Find real SeatPick slugs for the games in the watchlist and update `config.py`
- [x] Test manually: call `get_lowest_price()` and print the result

**Done when:** `get_lowest_price()` returns a real price for at least one World Cup game.

> **Note (2026-07-18 audit + live verification):** the "found real slugs" claim above is not accurate. The three slugs are generic guesses, never confirmed by hand against real seatpick.com pages. A live `tracker.py` run on 2026-07-18 showed two of the three ("world-cup-quarter-final-tickets", "world-cup-semi-final-tickets") return no price table at all. The third ("world-cup-final-tickets") happens to resolve to a page with a real price table, but that was luck, not verification. Treat all three as unverified placeholders.

---

## Phase 5 — Notifier

Build and test both alert channels in isolation.

**Tasks:**
- [x] Write `notifier.py`:
   - `send_ntfy(title: str, message: str) -> None` — HTTP POST to `https://ntfy.sh/{NTFY_TOPIC}` with Priority: high
   - `send_email(subject: str, body: str) -> None` — Gmail SMTP using `smtplib`, TLS on port 587
   - `send_alert(game_name, price, url, source, quantity, threshold, all_prices) -> None` — formats message for 1 vs 2 tickets and calls both channels
- [x] Format the alert message as specified in `CLAUDE.md` (adapted for quantity label in title/subject)
- [x] Test both channels manually:
   - `send_ntfy` confirmed delivered to ntfy app ✓
   - `send_email` confirmed received in inbox ✓

**Done when:** Both a phone push and an email land successfully in test runs. ✓

> **Note (2026-07-18 audit):** the work described above was real, but it was never committed. As of the last commit before this refactor, `notifier.py` was a 0 byte empty stub in git; the working code only existed uncommitted on disk. Re-verified working on 2026-07-18 as part of the event-agnostic refactor (Phase 9) — see that phase for the fresh test results.

---

## Phase 6 — Tracker (Orchestrator)

Wire everything together in `tracker.py`.

**Tasks:**
- [x] Write `tracker.py`:
   - Import `config`, both sources, and `notifier`
   - Loop through `WATCHLIST` × `QUANTITIES` — separate alert per (game, quantity) pair
   - For each pair: call both sources, collect non-`None` results, find minimum price
   - If minimum price ≤ threshold: call `notifier.send_alert()` with all prices for context
   - Log every run: timestamp, game, quantity, prices from each source, whether alert fired
   - If all sources return `None` for a pair: log a warning, skip — do not alert
- [x] Run `tracker.py` end-to-end locally:
   - Mock SeatGeek prices ($210/$230) triggered alerts on all 3 games × 2 quantities ✓
   - ntfy pushes confirmed sent (no errors) ✓
   - Emails confirmed sent ✓

**Done when:** Full end-to-end run works locally, alert fires correctly when threshold is crossed. ✓

> **Note (2026-07-18 audit):** same situation as Phase 5 — `tracker.py` was a 0 byte empty stub in the last commit before this refactor, despite this checklist saying it was written and tested. Re-verified working on 2026-07-18 as part of the event-agnostic refactor (Phase 9).

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
- [ ] Update `watchlist.toml` with all remaining events you want to track

**Done when:** Three consecutive automated runs complete cleanly in Actions logs with no errors.

---

## Phase 9 — Generalize Beyond World Cup (Event-Agnostic Refactor)

Done out of order relative to the original plan: scheduling (Phase 7) isn't worth setting up until the tool can watch more than a hardcoded World Cup list, so this generalization happened first. Turns "add an event" into a config-only edit and "add a new ticket site" into one new module plus a `config.KNOWN_SOURCES` entry and a `tracker.SOURCES` registry line, instead of watchlist edits inside `config.py` and hardcoded source calls in `tracker.py`.

**Tasks:**
- [x] Create `watchlist.toml` holding the watchlist (migrated the three existing World Cup entries as-is) and `default_quantities`, with comments showing how to copy a block for a new event
- [x] `config.py`: keep env loading and fail fast on missing vars; add `load_watchlist()` that parses `watchlist.toml` with stdlib `tomllib`, validates the schema (crashes with a clear `ValueError` on unknown source keys, missing threshold, bad types, etc.), and exposes `config.EVENTS`; `python config.py` still prints a summary
- [x] `tracker.py`: build a `SOURCES` registry dict mapping `"seatgeek"`/`"seatpick"` to adapter functions with a uniform `(source_cfg, quantity) -> dict | None` signature, loop `event["sources"].items()` and dispatch through the registry; a source returning `None` is logged and skipped, an unknown source key crashes at config load, not here
- [x] `sources/seatgeek.py`: removed the hardcoded `fifa-world-cup-tickets` fallback URL from the real API qty>1 path (was a bug — it silently mislabeled every multi ticket alert with a World Cup link regardless of the actual event); event URL is now derived from the API response or a generic `seatgeek.com/e/events/{id}` link; mock URL is now event neutral
- [x] `notifier.py`: `qty_label` now generic for any quantity (`_qty_label()` helper), not just hardcoded "1 ticket" / "2 adjacent tickets"; `__main__` test block unchanged
- [x] Verified `python config.py` prints the parsed watchlist correctly
- [x] Verified `python tracker.py` runs end to end in mock mode with no errors; all 6 (event, quantity) pairs alerted since mock prices ($210/$230) are below the $500 threshold; SeatPick's live scraper ran for real in the same pass and correctly returned `None` (logged, skipped) for two of the three unverified slugs
- [x] Ran `python notifier.py` once; both `send_ntfy` and `send_email` logged success with no errors, exit code 0

**Done when:** Adding a new event is a `watchlist.toml` only edit and adding a new source site is one new module plus a `config.KNOWN_SOURCES` entry and a `tracker.SOURCES` registry line. ✓ (2026-07-18)
