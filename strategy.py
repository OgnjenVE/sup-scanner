"""
strategy.py  —  SFP and MSB + Breaker detection logic
Ported from LuxAlgo Swing Failure Pattern indicator (CC BY-NC-SA 4.0)
"""
from config import SWING_LOOKBACK, PIVOT_LENGTH, M5_PIVOT_LENGTH


def _pivot_high_at(candles: list[dict], length: int, idx: int) -> float | None:
    if idx < length or idx >= len(candles) - 1:
        return None
    candidate = candles[idx]["high"]
    for i in range(1, length + 1):
        if candles[idx - i]["high"] >= candidate:
            return None
    if candles[idx + 1]["high"] >= candidate:
        return None
    return candidate


def _pivot_low_at(candles: list[dict], length: int, idx: int) -> float | None:
    if idx < length or idx >= len(candles) - 1:
        return None
    candidate = candles[idx]["low"]
    for i in range(1, length + 1):
        if candles[idx - i]["low"] <= candidate:
            return None
    if candles[idx + 1]["low"] <= candidate:
        return None
    return candidate


def detect_sfp(candles: list[dict], length: int = PIVOT_LENGTH) -> dict | None:
    """
    Check the last CLOSED H1 candle for an SFP.
    Bearish SFP: high > swing_high AND open < swing_high AND close < swing_high
    Bullish SFP: low  < swing_low  AND open > swing_low  AND close > swing_low
    """
    if len(candles) < length + 4:
        return None

    last  = candles[-2]
    prior = candles[:-1]

    swing_high = None
    for i in range(len(prior) - 2, length - 1, -1):
        ph = _pivot_high_at(prior, length, i)
        if ph is not None:
            swing_high = ph
            break

    swing_low = None
    for i in range(len(prior) - 2, length - 1, -1):
        pl = _pivot_low_at(prior, length, i)
        if pl is not None:
            swing_low = pl
            break

    # BEARISH SFP
    if swing_high is not None:
        if (last["high"]  > swing_high and
            last["open"]  < swing_high and
            last["close"] < swing_high):
            return {
                "direction":   "BEARISH",
                "type":        "SFP",
                "swept_level": swing_high,
                "candle":      last,
            }

    # BULLISH SFP
    if swing_low is not None:
        if (last["low"]   < swing_low and
            last["open"]  > swing_low and
            last["close"] > swing_low):
            return {
                "direction":   "BULLISH",
                "type":        "SFP",
                "swept_level": swing_low,
                "candle":      last,
            }

    return None


def detect_msb_and_breaker(m5_candles: list[dict], sfp_direction: str) -> dict | None:
    if len(m5_candles) < M5_PIVOT_LENGTH * 2 + 2:
        return None
    if sfp_direction == "BEARISH":
        return _bearish_msb_breaker(m5_candles)
    else:
        return _bullish_msb_breaker(m5_candles)


def _bearish_msb_breaker(candles: list[dict]) -> dict | None:
    """
    Find significant M5 swing lows using M5_PIVOT_LENGTH.
    Alert fires when last closed candle breaks below a swing low (MSB).
    Breaker = last bullish candle before the break.
    """
    swing_lows = []
    for i in range(M5_PIVOT_LENGTH, len(candles) - 1):
        pl = _pivot_low_at(candles, M5_PIVOT_LENGTH, i)
        if pl is not None:
            swing_lows.append((i, pl))

    current = candles[-2]  # last closed M5 candle

    for sl_idx, swing_low in reversed(swing_lows):
        if sl_idx >= len(candles) - 2:
            continue

        if current["close"] < swing_low:
            # Find last bullish candle before the break (breaker)
            breaker_candle = None
            for i in range(len(candles) - 3, sl_idx - 1, -1):
                if candles[i]["close"] > candles[i]["open"]:
                    breaker_candle = candles[i]
                    break

            if breaker_candle is None:
                continue

            return {
                "direction":    "BEARISH",
                "type":         "MSB_BREAKER",
                "msb_level":    swing_low,
                "breaker_high": breaker_candle["high"],
                "breaker_low":  breaker_candle["low"],
                "current_candle": current,
            }
    return None


def _bullish_msb_breaker(candles: list[dict]) -> dict | None:
    """
    Find significant M5 swing highs using M5_PIVOT_LENGTH.
    Alert fires when last closed candle breaks above a swing high (MSB).
    Breaker = last bearish candle before the break.
    """
    swing_highs = []
    for i in range(M5_PIVOT_LENGTH, len(candles) - 1):
        ph = _pivot_high_at(candles, M5_PIVOT_LENGTH, i)
        if ph is not None:
            swing_highs.append((i, ph))

    current = candles[-2]  # last closed M5 candle

    for sh_idx, swing_high in reversed(swing_highs):
        if sh_idx >= len(candles) - 2:
            continue

        if current["close"] > swing_high:
            # Find last bearish candle before the break (breaker)
            breaker_candle = None
            for i in range(len(candles) - 3, sh_idx - 1, -1):
                if candles[i]["close"] < candles[i]["open"]:
                    breaker_candle = candles[i]
                    break

            if breaker_candle is None:
                continue

            return {
                "direction":    "BULLISH",
                "type":         "MSB_BREAKER",
                "msb_level":    swing_high,
                "breaker_high": breaker_candle["high"],
                "breaker_low":  breaker_candle["low"],
                "current_candle": current,
            }
    return None
