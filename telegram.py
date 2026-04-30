"""
telegram.py  —  Send alerts to Telegram
"""
import requests
from datetime import datetime
from config import TELEGRAM_BOT_TOKEN, TELEGRAM_CHAT_ID


def _send(message: str):
    """Fire a Telegram message."""
    url = f"https://api.telegram.org/bot{TELEGRAM_BOT_TOKEN}/sendMessage"
    payload = {
        "chat_id": TELEGRAM_CHAT_ID,
        "text": message,
        "parse_mode": "HTML",
    }
    try:
        r = requests.post(url, json=payload, timeout=10)
        r.raise_for_status()
    except Exception as e:
        print(f"[TELEGRAM ERROR] {e}")


def alert_sfp(symbol: str, sfp: dict):
    """Send H1 SFP alert."""
    direction = sfp["direction"]
    emoji = "🔴" if direction == "BEARISH" else "🟢"
    swept  = sfp["swept_level"]
    close  = sfp["candle"]["close"]
    ts     = datetime.utcnow().strftime("%H:%M UTC")

    msg = (
        f"{emoji} <b>H1 SFP DETECTED</b>\n"
        f"━━━━━━━━━━━━━━━━━━\n"
        f"🪙 <b>Symbol:</b> {symbol}\n"
        f"📐 <b>Direction:</b> {direction}\n"
        f"📍 <b>Swept Level:</b> {swept:.4f}\n"
        f"💵 <b>Close:</b> {close:.4f}\n"
        f"⏰ <b>Time:</b> {ts}\n"
        f"━━━━━━━━━━━━━━━━━━\n"
        f"👀 Watching M5 for MSB + Breaker..."
    )
    _send(msg)
    print(f"[ALERT] SFP sent for {symbol} {direction}")


def alert_msb_breaker(symbol: str, sfp: dict, msb: dict):
    """Send M5 MSB + Breaker alert."""
    direction = msb["direction"]
    emoji = "🔴" if direction == "BEARISH" else "🟢"
    ts = datetime.utcnow().strftime("%H:%M UTC")

    msg = (
        f"{emoji} <b>MSB + BREAKER CONFIRMED</b>\n"
        f"━━━━━━━━━━━━━━━━━━\n"
        f"🪙 <b>Symbol:</b> {symbol}\n"
        f"📐 <b>Direction:</b> {direction}\n"
        f"🔓 <b>MSB Level:</b> {msb['msb_level']:.4f}\n"
        f"📦 <b>Breaker Zone:</b> {msb['breaker_low']:.4f} — {msb['breaker_high']:.4f}\n"
        f"💵 <b>Current Price:</b> {msb['current_candle']['close']:.4f}\n"
        f"📌 <b>H1 SFP Swept:</b> {sfp['swept_level']:.4f}\n"
        f"⏰ <b>Time:</b> {ts}\n"
        f"━━━━━━━━━━━━━━━━━━\n"
        f"⚡️ <b>H1 → M5 Setup Complete!</b>"
    )
    _send(msg)
    print(f"[ALERT] MSB+Breaker sent for {symbol} {direction}")
