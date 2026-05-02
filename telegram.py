"""
telegram.py  —  Send alerts to Telegram
"""
import requests
from datetime import datetime
from config import TELEGRAM_BOT_TOKEN, TELEGRAM_CHAT_ID, TIMEFRAME_CONFIGS


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


def _get_candle_ms(label: str) -> int:
    """Get candle duration in ms for a given TF label."""
    for tf in TIMEFRAME_CONFIGS:
        if tf["label"] == label:
            return tf["sfp_candle_ms"]
    return 3_600_000  # default 1H


def _sfp_block(sfp: dict, label: str) -> str:
    direction = sfp["direction"]
    emoji = "🔴" if direction == "BEARISH" else "🟢"
    msb_tf = label.split("/")[1]
    candle_ms = _get_candle_ms(label)
    candle_open_ts  = sfp["candle"]["open_time"] / 1000
    candle_close_ts = candle_open_ts + (candle_ms / 1000)
    candle_close_str = datetime.utcfromtimestamp(candle_close_ts).strftime("%H:%M UTC")
    return (
        f"{emoji} <b>{label}</b> — {direction}\n"
        f"   📍 Swept: {fmt(sfp['swept_level'])}\n"
        f"   💵 Close: {fmt(sfp['candle']['close'])}\n"
        f"   🕯 Candle closed: {candle_close_str}\n"
        f"   👀 Watching {msb_tf} for MSB + Breaker"
    )


def alert_sfp(symbol: str, sfp: dict, label: str):
    direction = sfp["direction"]
    emoji = "🔴" if direction == "BEARISH" else "🟢"
    ts = datetime.utcnow().strftime("%H:%M UTC (your local time +2h)")
    msb_tf = label.split("/")[1]

    candle_ms = _get_candle_ms(label)
    candle_open_ts  = sfp["candle"]["open_time"] / 1000
    candle_close_ts = candle_open_ts + (candle_ms / 1000)
    candle_close_str = datetime.utcfromtimestamp(candle_close_ts).strftime("%H:%M UTC")

    msg = (
        f"{emoji} <b>{label} SFP DETECTED</b>\n"
        f"━━━━━━━━━━━━━━━━━━\n"
        f"🪙 <b>Symbol:</b> {symbol}\n"
        f"📐 <b>Direction:</b> {direction}\n"
        f"📍 <b>Swept Level:</b> {fmt(sfp['swept_level'])}\n"
        f"💵 <b>Close:</b> {fmt(sfp['candle']['close'])}\n"
        f"🕯 <b>Candle closed:</b> {candle_close_str}\n"

        f"━━━━━━━━━━━━━━━━━━\n"
        f"👀 Watching {msb_tf} for MSB + Breaker..."
    )
    _send(msg)
    print(f"[ALERT] {label} SFP sent for {symbol} {direction} | candle closed {candle_close_str}")


def alert_confluence_sfp(symbol: str, sfp_list: list[tuple]):
    ts = datetime.utcnow().strftime("%H:%M UTC (your local time +2h)")
    direction = sfp_list[-1][0]["direction"]
    emoji = "🔴" if direction == "BEARISH" else "🟢"
    blocks = "\n".join(_sfp_block(sfp, label) for sfp, label in sfp_list)

    msg = (
        f"⭐ {emoji} <b>CONFLUENCE SFP DETECTED</b> ⭐\n"
        f"━━━━━━━━━━━━━━━━━━\n"
        f"🪙 <b>Symbol:</b> {symbol}\n"
        f"📊 <b>Timeframes:</b> {', '.join(l for _, l in sfp_list)}\n"
        f"━━━━━━━━━━━━━━━━━━\n"
        f"{blocks}\n"
        f"━━━━━━━━━━━━━━━━━━\n"

        f"━━━━━━━━━━━━━━━━━━\n"
        f"🔥 <b>High confluence — priority alert!</b>"
    )
    _send(msg)
    print(f"[ALERT] CONFLUENCE SFP sent for {symbol}")


def alert_msb_breaker(symbol: str, sfp: dict, msb: dict, label: str):
    direction = msb["direction"]
    emoji = "🔴" if direction == "BEARISH" else "🟢"
    ts = datetime.utcnow().strftime("%H:%M UTC (your local time +2h)")
    action = "SELL LIMIT" if direction == "BEARISH" else "BUY LIMIT"
    zone_desc = "price rallies into zone" if direction == "BEARISH" else "price dips into zone"
    sfp_tf = label.split("/")[0]

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
        f"📌 <b>{sfp_tf} SFP Swept:</b> {fmt(sfp['swept_level'])}\n"

        f"━━━━━━━━━━━━━━━━━━\n"
        f"⚡️ <b>Open chart and set limit order now!</b>"
    )
    _send(msg)
    print(f"[ALERT] {label} MSB+Breaker sent for {symbol} {direction}")


def alert_confluence_msb(symbol: str, msb_list: list[tuple]):
    ts = datetime.utcnow().strftime("%H:%M UTC (your local time +2h)")
    direction = msb_list[-1][1]["direction"]
    emoji = "🔴" if direction == "BEARISH" else "🟢"
    action = "SELL LIMIT" if direction == "BEARISH" else "BUY LIMIT"

    blocks = []
    for sfp, msb, label in msb_list:
        sfp_tf = label.split("/")[0]
        blocks.append(
            f"📊 <b>{label}</b>\n"
            f"   🔓 MSB: {fmt(msb['msb_level'])}\n"
            f"   📦 Breaker: {fmt(msb['breaker_low'])} — {fmt(msb['breaker_high'])}\n"
            f"   📍 {sfp_tf} SFP Swept: {fmt(sfp['swept_level'])}"
        )

    msg = (
        f"⭐ {emoji} <b>CONFLUENCE MSB CONFIRMED</b> ⭐\n"
        f"━━━━━━━━━━━━━━━━━━\n"
        f"🪙 <b>Symbol:</b> {symbol}\n"
        f"📊 <b>Timeframes:</b> {', '.join(l for _, _, l in msb_list)}\n"
        f"━━━━━━━━━━━━━━━━━━\n"
        + "\n".join(blocks) + "\n"
        f"━━━━━━━━━━━━━━━━━━\n"
        f"📌 <b>Action:</b> {action}\n"

        f"━━━━━━━━━━━━━━━━━━\n"
        f"🔥 <b>High confluence — priority entry!</b>"
    )
    _send(msg)
    print(f"[ALERT] CONFLUENCE MSB sent for {symbol}")
