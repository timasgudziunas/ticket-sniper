import os
import tomllib
from pathlib import Path

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

WATCHLIST_PATH = Path(__file__).parent / "watchlist.toml"

# Source keys understood by tracker.py's SOURCES registry, mapped to the
# fields each one requires under an event's [events.sources.<key>] table.
# Adding a new source site means adding one adapter module, one entry here,
# and one line in tracker.py's SOURCES registry.
KNOWN_SOURCES: dict[str, tuple[str, ...]] = {
    "seatgeek": ("id",),
    "seatpick": ("slug",),
}


def load_watchlist(path: Path = WATCHLIST_PATH) -> list[dict]:
    """Parse and validate watchlist.toml into a list of event dicts.

    Crashes with a clear ValueError on any schema problem: missing fields,
    unknown source keys, bad types. Config errors are not recoverable, so
    they are not caught here.
    """
    try:
        with open(path, "rb") as f:
            data = tomllib.load(f)
    except FileNotFoundError:
        raise ValueError(f"Watchlist file not found: {path}")
    except tomllib.TOMLDecodeError as e:
        raise ValueError(f"Watchlist file is not valid TOML ({path}): {e}")

    default_quantities = data.get("default_quantities", [1])
    if not isinstance(default_quantities, list) or not all(
        isinstance(q, int) and q > 0 for q in default_quantities
    ):
        raise ValueError("watchlist.toml: default_quantities must be a list of positive integers")

    events_raw = data.get("events", [])
    if not events_raw:
        raise ValueError(f"watchlist.toml: no [[events]] entries found in {path}")

    events = []
    for i, entry in enumerate(events_raw):
        label = entry.get("name", f"entry #{i + 1}")

        if "name" not in entry:
            raise ValueError(f"watchlist.toml: event #{i + 1} is missing required field 'name'")
        if "threshold" not in entry:
            raise ValueError(f"watchlist.toml: event '{label}' is missing required field 'threshold'")

        threshold = entry["threshold"]
        if not isinstance(threshold, (int, float)) or isinstance(threshold, bool) or threshold <= 0:
            raise ValueError(f"watchlist.toml: event '{label}' threshold must be a positive number")

        quantities = entry.get("quantities", default_quantities)
        if not isinstance(quantities, list) or not all(isinstance(q, int) and q > 0 for q in quantities):
            raise ValueError(f"watchlist.toml: event '{label}' quantities must be a list of positive integers")

        sources = entry.get("sources", {})
        if not sources:
            raise ValueError(f"watchlist.toml: event '{label}' has no [events.sources] entries")

        for source_key, source_cfg in sources.items():
            if source_key not in KNOWN_SOURCES:
                raise ValueError(
                    f"watchlist.toml: event '{label}' uses unknown source '{source_key}' "
                    f"(known sources: {', '.join(sorted(KNOWN_SOURCES))})"
                )
            required_fields = KNOWN_SOURCES[source_key]
            missing_fields = [f for f in required_fields if f not in source_cfg]
            if missing_fields:
                raise ValueError(
                    f"watchlist.toml: event '{label}' source '{source_key}' is missing "
                    f"required field(s): {', '.join(missing_fields)}"
                )

        events.append(
            {
                "name": entry["name"],
                "date": entry.get("date"),
                "threshold": threshold,
                "quantities": quantities,
                "sources": sources,
            }
        )

    return events


EVENTS = load_watchlist()

if __name__ == "__main__":
    print("Config loaded successfully.")
    print(f"  SEATGEEK_CLIENT_ID : {SEATGEEK_CLIENT_ID[:4]}...")
    print(f"  GMAIL_USER         : {GMAIL_USER}")
    print(f"  ALERT_EMAIL        : {ALERT_EMAIL}")
    print(f"  NTFY_TOPIC         : {NTFY_TOPIC}")
    print(f"  Watching {len(EVENTS)} event(s):")
    for event in EVENTS:
        sources = ", ".join(sorted(event["sources"]))
        print(
            f"    - {event['name']} (date: {event['date']}, threshold: ${event['threshold']}, "
            f"quantities: {event['quantities']}, sources: {sources})"
        )
