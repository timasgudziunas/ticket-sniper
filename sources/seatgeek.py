import logging
import requests

logger = logging.getLogger(__name__)

_MOCK_PRICES = {
    "default": {"price": 210.0, "url": "https://seatgeek.com/fifa-world-cup-tickets"},
}

def get_lowest_price(seatgeek_id: str, client_id: str) -> dict | None:
    if client_id == "mock":
        data = _MOCK_PRICES.get(seatgeek_id, _MOCK_PRICES["default"])
        logger.info(f"[MOCK] SeatGeek {seatgeek_id}: ${data['price']}")
        return {"price": data["price"], "url": data["url"], "source": "SeatGeek"}

    try:
        url = f"https://api.seatgeek.com/2/events/{seatgeek_id}"
        response = requests.get(url, params={"client_id": client_id}, timeout=10)
        response.raise_for_status()
        data = response.json()
        price = data.get("stats", {}).get("lowest_price")
        if price is None:
            logger.warning(f"SeatGeek {seatgeek_id}: no lowest_price in response")
            return None
        event_url = f"https://seatgeek.com/{data.get('slug', '')}"
        return {"price": float(price), "url": event_url, "source": "SeatGeek"}
    except Exception as e:
        logger.error(f"SeatGeek {seatgeek_id}: {e}")
        return None
