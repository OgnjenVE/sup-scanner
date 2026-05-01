"""
strategy.py  —  SFP and MSB + Breaker detection logic
Ported from LuxAlgo Swing Failure Pattern indicator (CC BY-NC-SA 4.0)
"""


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


def detect_sfp(candles: list[dict], pivot_length: int, lookback: int) -> dict | None:
    """
    Check the last CLOSED candle for an SFP.
    Bearish SFP: high > swing_high AND open < swing_high AND close < swing_high
    Bullish SFP: low  < swing_low  AND open > swing_low  AND close > swing_low
    """
    if len(candles) < pivot_length + 4:
        return None

    last  = candles[-2]   # last fully closed candle
    prior = candles[-(lookback + pivot_length + 2):-1]  # lookback window

    swing_high = None
    for i in range(len(prior) - 2, pivot_length - 1, -1):
        ph = _pivot_high_at(prior, pivot_length, i)
        if ph is not None:
            swing_high = ph
            break

    swing_low = None
    for i in range(len(prior) - 2, pivot_length - 1, -1):
        pl = _pivot_low_at(prior, pivot_length, i)
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


def detect_msb_and_breaker(m_candles: list[dict], sfp_direction: str,
                            msb_pivot: int) -> dict | None:
    if len(m_candles) < msb_pivot * 2 + 2:
        return None
    if sfp_direction == "BEARISH":
        return _bearish_msb_breaker(m_candles, msb_pivot)
    else:
        return _bullish_msb_breaker(m_candles, msb_pivot)


def _bearish_msb_breaker(candles: list[dict], pivot_length: int) -> dict | None:
    swing_lows = []
    for i in range(pivot_length, len(candles) - 1):
        pl = _pivot_low_at(candles, pivot_length, i)
        if pl is not None:
            swing_lows.append((i, pl))

    current = candles[-2]

    for sl_idx, swing_low in reversed(swing_lows):
        if sl_idx >= len(candles) - 2:
            continue
        if current["close"] < swing_low:
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


def _bullish_msb_breaker(candles: list[dict], pivot_length: int) -> dict | None:
    swing_highs = []
    for i in range(pivot_length, len(candles) - 1):
        ph = _pivot_high_at(candles, pivot_length, i)
        if ph is not None:
            swing_highs.append((i, ph))

    current = candles[-2]

    for sh_idx, swing_high in reversed(swing_highs):
        if sh_idx >= len(candles) - 2:
            continue
        if current["close"] > swing_high:
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
