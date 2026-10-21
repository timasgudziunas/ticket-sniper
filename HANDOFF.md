# ticket-sniper HANDOFF

**ARCHIVED 2026-10-19.** Retired to `projects/archives/` because the project stalled in June 2026, was never deployed on any scheduler, and the owner's attention moved elsewhere. No meaningful sessions occurred after the July 2026 event-agnostic refactor that is captured in the final commit. **Closed out 2026-10-21:** archive commit pushed, GitHub repo archived (read-only). Nothing external ever existed to turn off.

---

## What the final commit contained

The last commit before archiving preserved uncommitted work from the July 2026 refactor (Phase 9). It was substantial:

- `notifier.py` and `tracker.py` were both 0-byte empty stubs in git. The final commit fills them in with the actual working code that had only ever existed on disk.
- `config.py` was rewritten to load `watchlist.toml` via stdlib `tomllib` instead of holding a hardcoded Python list. It validates the schema at import time and crashes fast on any bad entry.
- `watchlist.toml` is a new untracked file with the three World Cup events migrated out of `config.py`. This is now the one place to add or change events.
- `sources/seatgeek.py` had a bug where every multi-ticket alert hardcoded a World Cup URL regardless of the actual event. Fixed.
- `CLAUDE.md`, `PLAN.md`, and `README.md` were updated to reflect the refactored architecture and the scheduler situation.

The end-to-end alert path was verified in mock mode (ntfy push and email both confirmed delivered, per PLAN.md Phase 9 notes). The live SeatPick scraper was run as part of that verification.

---

## What is genuinely unfinished

- **SeatGeek API key is mock.** `SEATGEEK_CLIENT_ID=mock` in `.env` causes `sources/seatgeek.py` to return canned prices ($210/$230) instead of hitting the real API. No real SeatGeek client ID was ever obtained from developer.seatgeek.com.
- **All SeatGeek event IDs are placeholders.** Every `seatgeek.id` in `watchlist.toml` is `"TBD"`. The real API code path exists and is structured correctly, but it has never been exercised against a live event.
- **SeatPick slugs are unverified guesses.** Live verification on 2026-07-18 showed two of the three slugs ("world-cup-quarter-final-tickets", "world-cup-semi-final-tickets") return no price table. Only the third ("world-cup-final-tickets") happened to resolve, and that was luck, not deliberate verification. Treat all three as placeholders.
- **Unverified assumption in SeatGeek qty >= 2 path.** It is not confirmed whether the listings endpoint returns a per-ticket price or a per-listing total. This cannot be checked without a real client ID and a real event ID.
- **No scheduler built.** Phase 7 (GitHub Actions cron) and Phase 8 (pre-deployment hardening) are not started. There was never a Windows Scheduled Task and never a `.github/workflows/` directory in this repo. Nothing had to be turned off at archive time.

---

## To revive this project

1. Register for a SeatGeek API client ID at developer.seatgeek.com. Set `SEATGEEK_CLIENT_ID` in `.env` to the real value.
2. Find real SeatGeek event IDs and real SeatPick slugs for the events you want to watch. Replace every `"TBD"` in `watchlist.toml`.
3. Verify the SeatGeek listings endpoint price semantics for qty >= 2 (per-ticket vs per-listing total) before trusting multi-ticket alerts.
4. Verify `python tracker.py` runs cleanly with real data.
5. Build Phase 7: either a `.github/workflows/check_prices.yml` cron (free on public repos) or a Windows Scheduled Task via the `register-windows-scheduled-task` skill. PLAN.md has the spec.
6. Run Phase 8 hardening (PLAN.md has the checklist).
