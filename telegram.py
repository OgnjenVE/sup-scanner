"""
telegram.py  —  Send alerts to Telegram
"""
import requests
from datetime import datetime
from config import TELEGRAM_BOT_TOKEN, TELEGRAM_CHAT_ID


def _send(message: str):
    url = f"https://api.telegram.org/bot{TELEGRAM_BOT_TOKEN}/sendMessage"
    payload = {"chat_id": TELEGRAM_CHAT_ID, "text": message, "parse_mode": "HTML"}
    try:
        r = requests.post(url, json=payload, timeout=10)
        r.raise_for_status()
    except Exception as e:
        print(f"[TELEGRAM ERROR] {e}")


def fmt(price: float) -> str:
    if price >= 1000:
        return f"{price:.2f}"
    elif price >= 1:
        return f"{price:.4f}"
    elif price >= 0.01:
        return f"{price:.6f}"
    else:
        return f"{price:.8f}"


def alert_sfp(symbol: str, sfp: dict, label: str):
    direction = sfp["direction"]
    emoji = "🔴" if direction == "BEARISH" else "🟢"
    ts = datetime.utcnow().strftime("%H:%M UTC")

    msg = (
        f"{emoji} <b>{label} SFP DETECTED</b>\n"
        f"━━━━━━━━━━━━━━━━━━\n"
        f"🪙 <b>Symbol:</b> {symbol}\n"
        f"📐 <b>Direction:</b> {direction}\n"
        f"📍 <b>Swept Level:</b> {fmt(sfp['swept_level'])}\n"
        f"💵 <b>Close:</b> {fmt(sfp['candle']['close'])}\n"
        f"⏰ <b>Time:</b> {ts}\n"
        f"━━━━━━━━━━━━━━━━━━\n"
        f"👀 Watching {label.split('/')[1]} for MSB + Breaker..."
    )
    _send(msg)
    print(f"[ALERT] {label} SFP sent for {symbol} {direction}")


def alert_msb_breaker(symbol: str, sfp: dict, msb: dict, label: str):
    direction = msb["direction"]
    emoji = "🔴" if direction == "BEARISH" else "🟢"
    ts = datetime.utcnow().strftime("%H:%M UTC")
    action = "SELL LIMIT" if direction == "BEARISH" else "BUY LIMIT"
    zone_desc = "price rallies into zone" if direction == "BEARISH" else "price dips into zone"

    msg = (
        f"{emoji} <b>{label} MSB CONFIRMED — SET YOUR ORDER</b>\n"
        f"━━━━━━━━━━━━━━━━━━\n"
        f"🪙 <b>Symbol:</b> {symbol}\n"
        f"📐 <b>Direction:</b> {direction}\n"
        f"🔓 <b>MSB Level Broken:</b> {fmt(msb['msb_level'])}\n"
        f"━━━━━━━━━━━━━━━━━━\n"
        f"📦 <b>BREAKER ZONE (your entry):</b>\n"
        f"   Top: {fmt(msb['breaker_high'])}\n"
        f"   Bot: {fmt(msb['breaker_low'])}\n"
        f"📌 <b>Action:</b> {action} when {zone_desc}\n"
        f"━━━━━━━━━━━━━━━━━━\n"
        f"📌 <b>{label.split('/')[0]} SFP Swept:</b> {fmt(sfp['swept_level'])}\n"
        f"⏰ <b>Time:</b> {ts}\n"
        f"━━━━━━━━━━━━━━━━━━\n"
        f"⚡️ <b>Open chart and set limit order now!</b>"
    )
    _send(msg)
    print(f"[ALERT] {label} MSB+Breaker sent for {symbol} {direction}")
