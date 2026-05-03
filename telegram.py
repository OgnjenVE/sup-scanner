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
    for tf in TIMEFRAME_CONFIGS:
        if tf["label"] == label:
            return tf["sfp_candle_ms"]
    return 3_600_000


def _trend_emoji(trend: str) -> str:
    return "📈" if trend == "BULLISH" else "📉" if trend == "BEARISH" else "➡️"


def _calc_trade(sfp: dict, msb: dict) -> dict:
    """Calculate entry, SL and TP1 (2R) from breaker zone and SFP wick."""
    direction = msb["direction"]
    entry = (msb["breaker_high"] + msb["breaker_low"]) / 2
    sl    = sfp["wick_tip"]  # tip of SFP wick
    risk  = abs(entry - sl)
    if direction == "BULLISH":
        tp1 = entry + (risk * 2)
    else:
        tp1 = entry - (risk * 2)
    rr = round(abs(tp1 - entry) / risk, 1) if risk > 0 else 0
    return {"entry": entry, "sl": sl, "tp1": tp1, "rr": rr}


def _sfp_block(sfp: dict, label: str) -> str:
    direction = sfp["direction"]
    emoji = "🔴" if direction == "BEARISH" else "🟢"
    msb_tf = label.split("/")[1]
    candle_ms = _get_candle_ms(label)
    candle_close_str = datetime.utcfromtimestamp(
        sfp["candle"]["open_time"] / 1000 + candle_ms / 1000
    ).strftime("%H:%M UTC")
    trend = sfp.get("trend", "NEUTRAL")
    swing_label = sfp.get("swing_label", "")
    return (
        f"{emoji} <b>{label}</b> — {direction} ({swing_label})\n"
        f"   📍 Swept: {fmt(sfp['swept_level'])}\n"
        f"   💵 Close: {fmt(sfp['candle']['close'])}\n"
        f"   🕯 Candle closed: {candle_close_str}\n"
        f"   {_trend_emoji(trend)} Trend: {trend}\n"
        f"   👀 Watching {msb_tf} for MSB + Breaker"
    )


def alert_sfp(symbol: str, sfp: dict, label: str):
    direction = sfp["direction"]
    emoji = "🔴" if direction == "BEARISH" else "🟢"
    msb_tf = label.split("/")[1]
    candle_ms = _get_candle_ms(label)
    candle_close_str = datetime.utcfromtimestamp(
        sfp["candle"]["open_time"] / 1000 + candle_ms / 1000
    ).strftime("%H:%M UTC")
    trend = sfp.get("trend", "NEUTRAL")
    swing_label = sfp.get("swing_label", "")

    msg = (
        f"{emoji} <b>{label} SFP DETECTED</b>\n"
        f"━━━━━━━━━━━━━━━━━━\n"
        f"🪙 <b>Symbol:</b> {symbol}\n"
        f"📐 <b>Direction:</b> {direction}\n"
        f"🏷 <b>Swing:</b> {swing_label}\n"
        f"📍 <b>Swept Level:</b> {fmt(sfp['swept_level'])}\n"
        f"💵 <b>Close:</b> {fmt(sfp['candle']['close'])}\n"
        f"🕯 <b>Candle closed:</b> {candle_close_str}\n"
        f"{_trend_emoji(trend)} <b>Trend:</b> {trend}\n"
        f"━━━━━━━━━━━━━━━━━━\n"
        f"👀 Watching {msb_tf} for MSB + Breaker..."
    )
    _send(msg)
    print(f"[ALERT] {label} SFP {swing_label} sent for {symbol} {direction} | candle {candle_close_str}")


def alert_confluence_sfp(symbol: str, sfp_list: list[tuple]):
    direction = sfp_list[-1][0]["direction"]
    emoji = "🔴" if direction == "BEARISH" else "🟢"
    blocks = "\n".join(_sfp_block(sfp, label) for sfp, label in sfp_list)
    ts = datetime.utcnow().strftime("%H:%M UTC")

    msg = (
        f"⭐ {emoji} <b>CONFLUENCE SFP DETECTED</b> ⭐\n"
        f"━━━━━━━━━━━━━━━━━━\n"
        f"🪙 <b>Symbol:</b> {symbol}\n"
        f"📊 <b>Timeframes:</b> {', '.join(l for _, l in sfp_list)}\n"
        f"━━━━━━━━━━━━━━━━━━\n"
        f"{blocks}\n"
        f"━━━━━━━━━━━━━━━━━━\n"
        f"🔥 <b>High confluence — priority alert!</b>"
    )
    _send(msg)
    print(f"[ALERT] CONFLUENCE SFP sent for {symbol}")


def alert_msb_breaker(symbol: str, sfp: dict, msb: dict, label: str):
    direction = msb["direction"]
    emoji = "🔴" if direction == "BEARISH" else "🟢"
    sfp_tf = label.split("/")[0]
    trend = sfp.get("trend", "NEUTRAL")
    swing_label = sfp.get("swing_label", "")

    trade = _calc_trade(sfp, msb)
    action = "BUY LIMIT" if direction == "BULLISH" else "SELL LIMIT"
    zone_desc = "price dips into zone" if direction == "BULLISH" else "price rallies into zone"

    msg = (
        f"{emoji} <b>{label} MSB CONFIRMED — SET YOUR ORDER</b>\n"
        f"━━━━━━━━━━━━━━━━━━\n"
        f"🪙 <b>Symbol:</b> {symbol}\n"
        f"📐 <b>Direction:</b> {direction}\n"
        f"🏷 <b>Swing:</b> {swing_label}\n"
        f"🔓 <b>MSB Level Broken:</b> {fmt(msb['msb_level'])}\n"
        f"{_trend_emoji(trend)} <b>Trend:</b> {trend}\n"
        f"━━━━━━━━━━━━━━━━━━\n"
        f"📦 <b>BREAKER ZONE:</b> {fmt(msb['breaker_low'])} — {fmt(msb['breaker_high'])}\n"
        f"━━━━━━━━━━━━━━━━━━\n"
        f"📌 <b>Action:</b> {action} when {zone_desc}\n"
        f"🎯 <b>Entry:</b>  {fmt(trade['entry'])}\n"
        f"🛑 <b>Stop:</b>   {fmt(trade['sl'])} (SFP wick)\n"
        f"✅ <b>TP1 (2R):</b> {fmt(trade['tp1'])}\n"
        f"━━━━━━━━━━━━━━━━━━\n"
        f"📍 <b>{sfp_tf} SFP Swept:</b> {fmt(sfp['swept_level'])}\n"
        f"━━━━━━━━━━━━━━━━━━\n"
        f"⚡️ <b>Open chart and set limit order now!</b>"
    )
    _send(msg)
    print(f"[ALERT] {label} MSB+Breaker sent for {symbol} {direction}")


def alert_confluence_msb(symbol: str, msb_list: list[tuple]):
    direction = msb_list[-1][1]["direction"]
    emoji = "🔴" if direction == "BEARISH" else "🟢"
    action = "SELL LIMIT" if direction == "BEARISH" else "BUY LIMIT"

    blocks = []
    for sfp, msb, label in msb_list:
        sfp_tf = label.split("/")[0]
        trade = _calc_trade(sfp, msb)
        swing_label = sfp.get("swing_label", "")
        blocks.append(
            f"📊 <b>{label}</b> ({swing_label})\n"
            f"   🔓 MSB: {fmt(msb['msb_level'])}\n"
            f"   📦 Breaker: {fmt(msb['breaker_low'])} — {fmt(msb['breaker_high'])}\n"
            f"   🎯 Entry: {fmt(trade['entry'])}  🛑 SL: {fmt(trade['sl'])}  ✅ TP1: {fmt(trade['tp1'])}\n"
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
        f"🔥 <b>High confluence — priority entry!</b>"
    )
    _send(msg)
    print(f"[ALERT] CONFLUENCE MSB sent for {symbol}")
