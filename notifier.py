import logging
import smtplib
import requests
from email.message import EmailMessage

import config

logger = logging.getLogger(__name__)


def send_ntfy(title: str, message: str) -> None:
    try:
        requests.post(
            f"https://ntfy.sh/{config.NTFY_TOPIC}",
            data=message.encode("utf-8"),
            headers={"Title": title, "Priority": "high", "Tags": "ticket"},
            timeout=10,
        )
        logger.info(f"ntfy sent: {title}")
    except Exception as e:
        logger.error(f"ntfy send failed: {e}")


def send_email(subject: str, body: str) -> None:
    try:
        msg = EmailMessage()
        msg["Subject"] = subject
        msg["From"] = config.GMAIL_USER
        msg["To"] = config.ALERT_EMAIL
        msg.set_content(body)
        with smtplib.SMTP("smtp.gmail.com", 587) as smtp:
            smtp.ehlo()
            smtp.starttls()
            smtp.login(config.GMAIL_USER, config.GMAIL_APP_PASSWORD)
            smtp.send_message(msg)
        logger.info(f"email sent: {subject}")
    except Exception as e:
        logger.error(f"email send failed: {e}")


def _qty_label(quantity: int) -> str:
    return "1 ticket" if quantity == 1 else f"{quantity} adjacent tickets"


def send_alert(
    game_name: str,
    price: float,
    url: str,
    source: str,
    quantity: int,
    threshold: int,
    all_prices: list,
) -> None:
    qty_label = _qty_label(quantity)
    price_str = f"${price:.0f}"

    other_lines = [
        f"{p['source']} also showing: ${p['price']:.0f}"
        for p in all_prices
        if p["source"] != source
    ]

    ntfy_title = f"PRICE DROP: {game_name} - {qty_label}"
    ntfy_body = (
        f"🎟️ {price_str} via {source} — below your ${threshold} threshold\n"
        f"{url}"
        + ("\n\n" + "\n".join(other_lines) if other_lines else "")
    )

    email_subject = f"[ticket-sniper] {game_name} — {price_str} ({source}) — {qty_label}"
    email_body = f"{ntfy_title}\n\n{ntfy_body}"

    send_ntfy(ntfy_title, ntfy_body)
    send_email(email_subject, email_body)
    logger.info(f"Alert fired: {game_name} | {qty_label} | {price_str} via {source}")


if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO)
    print("Sending test ntfy push...")
    send_ntfy("ticket-sniper test", "If you see this, ntfy is working.")
    print("Sending test email...")
    send_email("[ticket-sniper] test", "If you see this, email is working.")
    print("Done — check your phone and inbox.")
