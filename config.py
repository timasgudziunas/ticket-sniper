import os
from dotenv import load_dotenv

load_dotenv()

_REQUIRED = ["SEATGEEK_CLIENT_ID", "GMAIL_USER", "GMAIL_APP_PASSWORD", "ALERT_EMAIL", "NTFY_TOPIC"]
_missing = [v for v in _REQUIRED if not os.environ.get(v)]
if _missing:
    raise EnvironmentError(f"Missing required environment variables: {', '.join(_missing)}")

SEATGEEK_CLIENT_ID = os.environ["SEATGEEK_CLIENT_ID"]
GMAIL_USER = os.environ["GMAIL_USER"]
GMAIL_APP_PASSWORD = os.environ["GMAIL_APP_PASSWORD"]
ALERT_EMAIL = os.environ["ALERT_EMAIL"]
NTFY_TOPIC = os.environ["NTFY_TOPIC"]

# How many tickets to check per game — alerts fire independently for each quantity.
QUANTITIES = [1, 2]

# Only games after July 1, 2026. $500 per-ticket cap applies to all quantities.
WATCHLIST = [
    {
        "name": "World Cup Quarter Finals",
        "date": "2026-07-04",
        "seatgeek_id": "TBD",
        "seatpick_slug": "world-cup-quarter-final-tickets",
        "threshold": 500,
    },
    {
        "name": "World Cup Semi Finals",
        "date": "2026-07-08",
        "seatgeek_id": "TBD",
        "seatpick_slug": "world-cup-semi-final-tickets",
        "threshold": 500,
    },
    {
        "name": "World Cup Final",
        "date": "2026-07-19",
        "seatgeek_id": "TBD",
        "seatpick_slug": "world-cup-final-tickets",
        "threshold": 500,
    },
]

if __name__ == "__main__":
    print("Config loaded successfully.")
    print(f"  SEATGEEK_CLIENT_ID : {SEATGEEK_CLIENT_ID[:4]}...")
    print(f"  GMAIL_USER         : {GMAIL_USER}")
    print(f"  ALERT_EMAIL        : {ALERT_EMAIL}")
    print(f"  NTFY_TOPIC         : {NTFY_TOPIC}")
    print(f"  Watching {len(WATCHLIST)} game(s):")
    for game in WATCHLIST:
        print(f"    - {game['name']} (threshold: ${game['threshold']})")
