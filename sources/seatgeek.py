import logging
import requests

logger = logging.getLogger(__name__)

_MOCK_PRICES = {
    "default": {1: 210.0, 2: 230.0},
}
_MOCK_URL = "https://seatgeek.com/fifa-world-cup-tickets"


def get_lowest_price(seatgeek_id: str, client_id: str, quantity: int = 1) -> dict | None:
    if client_id == "mock":
        prices = _MOCK_PRICES.get(seatgeek_id, _MOCK_PRICES["default"])
        price = prices.get(quantity, prices[1])
        logger.info(f"[MOCK] SeatGeek {seatgeek_id} qty={quantity}: ${price}")
        return {"price": price, "url": _MOCK_URL, "source": "SeatGeek", "quantity": quantity}

    try:
        if quantity == 1:
            url = f"https://api.seatgeek.com/2/events/{seatgeek_id}"
            response = requests.get(url, params={"client_id": client_id}, timeout=10)
            response.raise_for_status()
            data = response.json()
            price = data.get("stats", {}).get("lowest_price")
            if price is None:
                logger.warning(f"SeatGeek {seatgeek_id} qty=1: no lowest_price in response")
                return None
            event_url = f"https://seatgeek.com/{data.get('slug', '')}"
        else:
            # Listings endpoint lets us filter to listings that can seat `quantity` together.
            url = "https://api.seatgeek.com/2/listings"
            response = requests.get(
                url,
                params={"event_id": seatgeek_id, "quantity": quantity, "client_id": client_id},
                timeout=10,
            )
            response.raise_for_status()
            listings = response.json().get("listings", [])
            prices = [l["price"] for l in listings if l.get("price")]
            if not prices:
                logger.warning(f"SeatGeek {seatgeek_id} qty={quantity}: no listings found")
                return None
            price = min(prices)
            event_url = f"https://seatgeek.com/fifa-world-cup-tickets"

        return {"price": float(price), "url": event_url, "source": "SeatGeek", "quantity": quantity}
    except Exception as e:
        logger.error(f"SeatGeek {seatgeek_id} qty={quantity}: {e}")
        return None
