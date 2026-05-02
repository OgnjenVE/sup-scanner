"""
strategy.py  —  SFP and MSB + Breaker detection logic
Swing points based on XO/Williams Fractal logic (n=2, handles equal highs/lows)
"""


def _is_fractal_high(candles: list[dict], idx: int) -> bool:
    """
    XO Williams Fractal High at idx (n=2):
    high[idx] must be highest of 5-bar window with allowance for equal highs.
    Ported directly from XO_Swingpoints Pine Script.
    """
    if idx < 4 or idx >= len(candles) - 2:
        return False

    h = [candles[idx + i]["high"] for i in range(-4, 3)]
    # h[4] = high[n] (the candidate), indices shifted: h[0]=n+4 ... h[4]=n ... h[6]=n-2
    # Pine: high[n+2] < high[n], high[n+1] < high[n], high[n-1] < high[n], high[n-2] < high[n]
    n = candles[idx]["high"]

    # Pattern 1: strict 2 each side
    if (candles[idx-2]["high"] < n and candles[idx-1]["high"] < n and
        candles[idx+1]["high"] < n and candles[idx+2]["high"] < n):
        return True
    # Pattern 2: one equal on right
    if (idx >= 5 and
        candles[idx-2]["high"] < n and candles[idx-1]["high"] < n and
        candles[idx+1]["high"] == n and
        candles[idx+2]["high"] < n and candles[idx+3]["high"] < n):
        return True
    # Pattern 3: two equal on right
    if (idx >= 6 and
        candles[idx-2]["high"] < n and candles[idx-1]["high"] < n and
        candles[idx+1]["high"] <= n and candles[idx+2]["high"] == n and
        candles[idx+3]["high"] < n and candles[idx+4]["high"] < n):
        return True
    # Pattern 4: three equal on right
    if (idx >= 7 and
        candles[idx-2]["high"] < n and candles[idx-1]["high"] < n and
        candles[idx+1]["high"] <= n and candles[idx+2]["high"] == n and
        candles[idx+3]["high"] == n and
        candles[idx+4]["high"] < n and candles[idx+5]["high"] < n):
        return True
    # Pattern 5: four equal on right
    if (idx >= 8 and
        candles[idx-2]["high"] < n and candles[idx-1]["high"] < n and
        candles[idx+1]["high"] <= n and candles[idx+2]["high"] == n and
        candles[idx+3]["high"] <= n and candles[idx+4]["high"] == n and
        candles[idx+5]["high"] < n and candles[idx+6]["high"] < n):
        return True
    return False


def _is_fractal_low(candles: list[dict], idx: int) -> bool:
    """
    XO Williams Fractal Low at idx (n=2).
    """
    if idx < 4 or idx >= len(candles) - 2:
        return False

    n = candles[idx]["low"]

    # Pattern 1: strict 2 each side
    if (candles[idx-2]["low"] > n and candles[idx-1]["low"] > n and
        candles[idx+1]["low"] > n and candles[idx+2]["low"] > n):
        return True
    # Pattern 2
    if (idx >= 5 and
        candles[idx-2]["low"] > n and candles[idx-1]["low"] > n and
        candles[idx+1]["low"] == n and
        candles[idx+2]["low"] > n and candles[idx+3]["low"] > n):
        return True
    # Pattern 3
    if (idx >= 6 and
        candles[idx-2]["low"] > n and candles[idx-1]["low"] > n and
        candles[idx+1]["low"] >= n and candles[idx+2]["low"] == n and
        candles[idx+3]["low"] > n and candles[idx+4]["low"] > n):
        return True
    # Pattern 4
    if (idx >= 7 and
        candles[idx-2]["low"] > n and candles[idx-1]["low"] > n and
        candles[idx+1]["low"] >= n and candles[idx+2]["low"] == n and
        candles[idx+3]["low"] == n and
        candles[idx+4]["low"] > n and candles[idx+5]["low"] > n):
        return True
    # Pattern 5
    if (idx >= 8 and
        candles[idx-2]["low"] > n and candles[idx-1]["low"] > n and
        candles[idx+1]["low"] >= n and candles[idx+2]["low"] == n and
        candles[idx+3]["low"] >= n and candles[idx+4]["low"] == n and
        candles[idx+5]["low"] > n and candles[idx+6]["low"] > n):
        return True
    return False


def find_latest_fractal_high(candles: list[dict], lookback: int) -> float | None:
    """Find the most recent fractal high within lookback candles."""
    window = candles[-(lookback + 10):-1]  # exclude current forming candle
    for i in range(len(window) - 3, 3, -1):
        if _is_fractal_high(window, i):
            return window[i]["high"]
    return None


def find_latest_fractal_low(candles: list[dict], lookback: int) -> float | None:
    """Find the most recent fractal low within lookback candles."""
    window = candles[-(lookback + 10):-1]
    for i in range(len(window) - 3, 3, -1):
        if _is_fractal_low(window, i):
            return window[i]["low"]
    return None


def find_fractal_highs(candles: list[dict]) -> list[tuple]:
    """Find all fractal highs in candles. Returns list of (idx, price)."""
    result = []
    for i in range(4, len(candles) - 2):
        if _is_fractal_high(candles, i):
            result.append((i, candles[i]["high"]))
    return result


def find_fractal_lows(candles: list[dict]) -> list[tuple]:
    """Find all fractal lows in candles. Returns list of (idx, price)."""
    result = []
    for i in range(4, len(candles) - 2):
        if _is_fractal_low(candles, i):
            result.append((i, candles[i]["low"]))
    return result


def detect_sfp(candles: list[dict], pivot_length: int, lookback: int) -> dict | None:
    """
    Check the last CLOSED candle for an SFP using XO fractal swing points.
    Bearish SFP: wick above fractal high, open AND close below it
    Bullish SFP: wick below fractal low,  open AND close above it
    """
    if len(candles) < 10:
        return None

    last = candles[-2]   # last fully closed candle

    swing_high = find_latest_fractal_high(candles, lookback)
    swing_low  = find_latest_fractal_low(candles, lookback)

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
    """MSB detection using XO fractal swing points on lower timeframe."""
    if len(m_candles) < 10:
        return None
    if sfp_direction == "BEARISH":
        return _bearish_msb_breaker(m_candles)
    else:
        return _bullish_msb_breaker(m_candles)


def _bearish_msb_breaker(candles: list[dict]) -> dict | None:
    """
    Bearish MSB: last closed candle breaks below a fractal low.
    Breaker = last bullish candle before the break.
    """
    fractal_lows = find_fractal_lows(candles)
    current = candles[-2]

    for fl_idx, fl_price in reversed(fractal_lows):
        if fl_idx >= len(candles) - 2:
            continue
        if current["close"] < fl_price:
            breaker_candle = None
            for i in range(len(candles) - 3, fl_idx - 1, -1):
                if candles[i]["close"] > candles[i]["open"]:
                    breaker_candle = candles[i]
                    break
            if breaker_candle is None:
                continue
            return {
                "direction":    "BEARISH",
                "type":         "MSB_BREAKER",
                "msb_level":    fl_price,
                "breaker_high": breaker_candle["high"],
                "breaker_low":  breaker_candle["low"],
                "current_candle": current,
            }
    return None


def _bullish_msb_breaker(candles: list[dict]) -> dict | None:
    """
    Bullish MSB: last closed candle breaks above a fractal high.
    Breaker = last bearish candle before the break.
    """
    fractal_highs = find_fractal_highs(candles)
    current = candles[-2]

    for fh_idx, fh_price in reversed(fractal_highs):
        if fh_idx >= len(candles) - 2:
            continue
        if current["close"] > fh_price:
            breaker_candle = None
            for i in range(len(candles) - 3, fh_idx - 1, -1):
                if candles[i]["close"] < candles[i]["open"]:
                    breaker_candle = candles[i]
                    break
            if breaker_candle is None:
                continue
            return {
                "direction":    "BULLISH",
                "type":         "MSB_BREAKER",
                "msb_level":    fh_price,
                "breaker_high": breaker_candle["high"],
                "breaker_low":  breaker_candle["low"],
                "current_candle": current,
            }
    return None
