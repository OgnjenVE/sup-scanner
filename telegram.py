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


def alert_sfp(symbol: str, sfp: dict):
    direction = sfp["direction"]
    emoji = "🔴" if direction == "BEARISH" else "🟢"
    ts = datetime.utcnow().strftime("%H:%M UTC")

    msg = (
        f"{emoji} <b>H1 SFP DETECTED</b>\n"
        f"━━━━━━━━━━━━━━━━━━\n"
        f"🪙 <b>Symbol:</b> {symbol}\n"
        f"📐 <b>Direction:</b> {direction}\n"
        f"📍 <b>Swept Level:</b> {sfp['swept_level']:.4f}\n"
        f"💵 <b>Close:</b> {sfp['candle']['close']:.4f}\n"
        f"⏰ <b>Time:</b> {ts}\n"
        f"━━━━━━━━━━━━━━━━━━\n"
        f"👀 Watching M5 for MSB + Breaker..."
    )
    _send(msg)
    print(f"[ALERT] SFP sent for {symbol} {direction}")


def alert_msb_breaker(symbol: str, sfp: dict, msb: dict):
    direction = msb["direction"]
    emoji = "🔴" if direction == "BEARISH" else "🟢"
    ts = datetime.utcnow().strftime("%H:%M UTC")

    action = "SELL LIMIT" if direction == "BEARISH" else "BUY LIMIT"
    zone_desc = "price rallies into zone" if direction == "BEARISH" else "price dips into zone"

    msg = (
        f"{emoji} <b>MSB CONFIRMED — SET YOUR ORDER</b>\n"
        f"━━━━━━━━━━━━━━━━━━\n"
        f"🪙 <b>Symbol:</b> {symbol}\n"
        f"📐 <b>Direction:</b> {direction}\n"
        f"🔓 <b>MSB Level Broken:</b> {msb['msb_level']:.4f}\n"
        f"━━━━━━━━━━━━━━━━━━\n"
        f"📦 <b>BREAKER ZONE (your entry):</b>\n"
        f"   Top: {msb['breaker_high']:.4f}\n"
        f"   Bot: {msb['breaker_low']:.4f}\n"
        f"📌 <b>Action:</b> {action} when {zone_desc}\n"
        f"━━━━━━━━━━━━━━━━━━\n"
        f"📌 <b>H1 SFP Swept:</b> {sfp['swept_level']:.4f}\n"
        f"⏰ <b>Time:</b> {ts}\n"
        f"━━━━━━━━━━━━━━━━━━\n"
        f"⚡️ <b>Open chart and set limit order now!</b>"
    )
    _send(msg)
    print(f"[ALERT] MSB+Breaker sent for {symbol} {direction}")
