import logging

import config
import notifier
from sources import seatgeek, seatpick

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s %(levelname)s %(message)s",
    datefmt="%Y-%m-%d %H:%M:%S",
)
logger = logging.getLogger(__name__)


def _fetch_seatgeek(source_cfg: dict, quantity: int) -> dict | None:
    return seatgeek.get_lowest_price(source_cfg["id"], config.SEATGEEK_CLIENT_ID, quantity)


def _fetch_seatpick(source_cfg: dict, quantity: int) -> dict | None:
    return seatpick.get_lowest_price(source_cfg["slug"], quantity)


# One adapter per source key in watchlist.toml. Each adapter takes the
# event's [events.sources.<key>] table plus a quantity and returns the
# {"price", "url", "source", "quantity"} contract or None.
# To add a new source site: write sources/<site>.py with a get_lowest_price()
# that follows that contract, add an adapter above, and add one line here.
SOURCES = {
    "seatgeek": _fetch_seatgeek,
    "seatpick": _fetch_seatpick,
}


def check_event(event: dict, quantity: int) -> None:
    name = event["name"]
    threshold = event["threshold"]
    qty_label = f"qty={quantity}"

    results = []
    for source_key, source_cfg in event["sources"].items():
        fetch = SOURCES[source_key]
        result = fetch(source_cfg, quantity)
        if result is None:
            logger.warning(f"{name} | {qty_label} | {source_key} returned no price — skipping")
            continue
        results.append(result)

    if not results:
        logger.warning(f"{name} | {qty_label} | all sources returned None — skipping")
        return

    for r in results:
        logger.info(f"{name} | {qty_label} | {r['source']}: ${r['price']:.0f}")

    best = min(results, key=lambda r: r["price"])

    if best["price"] <= threshold:
        logger.info(
            f"{name} | {qty_label} | ALERT FIRED: ${best['price']:.0f} via {best['source']} "
            f"<= ${threshold} threshold"
        )
        notifier.send_alert(
            game_name=name,
            price=best["price"],
            url=best["url"],
            source=best["source"],
            quantity=quantity,
            threshold=threshold,
            all_prices=results,
        )
    else:
        logger.info(
            f"{name} | {qty_label} | no alert — best ${best['price']:.0f} > ${threshold} threshold"
        )


def run() -> None:
    logger.info("=== ticket-sniper run started ===")
    for event in config.EVENTS:
        for qty in event["quantities"]:
            check_event(event, qty)
    logger.info("=== run complete ===")


if __name__ == "__main__":
    run()
