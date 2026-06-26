import logging
import requests
from bs4 import BeautifulSoup

logger = logging.getLogger(__name__)

BASE_URL = "https://seatpick.com"
HEADERS = {
    "User-Agent": (
        "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
        "AppleWebKit/537.36 (KHTML, like Gecko) "
        "Chrome/125.0.0.0 Safari/537.36"
    )
}


def get_lowest_price(slug: str, quantity: int = 1) -> dict | None:
    url = f"{BASE_URL}/{slug}"
    params = {"qty": quantity} if quantity > 1 else {}
    try:
        r = requests.get(url, headers=HEADERS, params=params, timeout=15)
        r.raise_for_status()
        soup = BeautifulSoup(r.text, "html.parser")

        # Find the table that has a 'Low' column — present on all event pages
        for table in soup.find_all("table"):
            headers = [th.get_text(strip=True) for th in table.find_all("th")]
            if "Low" not in headers:
                continue
            low_idx = headers.index("Low")
            prices = []
            for row in table.find_all("tr")[1:]:
                cells = row.find_all("td")
                if len(cells) > low_idx:
                    raw = cells[low_idx].get_text(strip=True)
                    cleaned = raw.replace("US$", "").replace("$", "").replace(",", "").strip()
                    if cleaned:
                        try:
                            prices.append(float(cleaned))
                        except ValueError:
                            pass
            if prices:
                return {"price": min(prices), "url": r.url, "source": "SeatPick", "quantity": quantity}

        logger.warning(f"SeatPick {slug} qty={quantity}: no price table found on page")
        return None
    except Exception as e:
        logger.warning(f"SeatPick {slug} qty={quantity}: {e}")
        return None
