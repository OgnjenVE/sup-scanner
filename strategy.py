"""
strategy.py  —  SFP and MSB + Breaker detection logic
Swing points based on XO/Williams Fractal logic (n=2, handles equal highs/lows)
"""


def _is_fractal_high(candles: list[dict], idx: int) -> bool:
    """XO Williams Fractal High — safe bounds checking on all patterns."""
    n_candles = len(candles)
    if idx < 2 or idx >= n_candles - 2:
        return False

    n = candles[idx]["high"]

    def h(offset):
        i = idx + offset
        if 0 <= i < n_candles:
            return candles[i]["high"]
        return None

    # Pattern 1: strict 2 each side
    if (h(-2) is not None and h(-1) is not None and h(1) is not None and h(2) is not None and
        h(-2) < n and h(-1) < n and h(1) < n and h(2) < n):
        return True
    # Pattern 2: one equal on right side
    if (h(-2) is not None and h(-1) is not None and h(1) is not None and h(2) is not None and h(3) is not None and
        h(-2) < n and h(-1) < n and h(1) == n and h(2) < n and h(3) < n):
        return True
    # Pattern 3
    if (h(-2) is not None and h(-1) is not None and h(1) is not None and h(2) is not None and h(3) is not None and h(4) is not None and
        h(-2) < n and h(-1) < n and h(1) <= n and h(2) == n and h(3) < n and h(4) < n):
        return True
    # Pattern 4
    if (h(-2) is not None and h(-1) is not None and h(1) is not None and h(2) is not None and
        h(3) is not None and h(4) is not None and h(5) is not None and
        h(-2) < n and h(-1) < n and h(1) <= n and h(2) == n and h(3) == n and h(4) < n and h(5) < n):
        return True
    # Pattern 5
    if (h(-2) is not None and h(-1) is not None and h(1) is not None and h(2) is not None and
        h(3) is not None and h(4) is not None and h(5) is not None and h(6) is not None and
        h(-2) < n and h(-1) < n and h(1) <= n and h(2) == n and h(3) <= n and
        h(4) == n and h(5) < n and h(6) < n):
        return True
    return False


def _is_fractal_low(candles: list[dict], idx: int) -> bool:
    """XO Williams Fractal Low — safe bounds checking on all patterns."""
    n_candles = len(candles)
    if idx < 2 or idx >= n_candles - 2:
        return False

    n = candles[idx]["low"]

    def l(offset):
        i = idx + offset
        if 0 <= i < n_candles:
            return candles[i]["low"]
        return None

    # Pattern 1
    if (l(-2) is not None and l(-1) is not None and l(1) is not None and l(2) is not None and
        l(-2) > n and l(-1) > n and l(1) > n and l(2) > n):
        return True
    # Pattern 2
    if (l(-2) is not None and l(-1) is not None and l(1) is not None and l(2) is not None and l(3) is not None and
        l(-2) > n and l(-1) > n and l(1) == n and l(2) > n and l(3) > n):
        return True
    # Pattern 3
    if (l(-2) is not None and l(-1) is not None and l(1) is not None and l(2) is not None and l(3) is not None and l(4) is not None and
        l(-2) > n and l(-1) > n and l(1) >= n and l(2) == n and l(3) > n and l(4) > n):
        return True
    # Pattern 4
    if (l(-2) is not None and l(-1) is not None and l(1) is not None and l(2) is not None and
        l(3) is not None and l(4) is not None and l(5) is not None and
        l(-2) > n and l(-1) > n and l(1) >= n and l(2) == n and l(3) == n and l(4) > n and l(5) > n):
        return True
    # Pattern 5
    if (l(-2) is not None and l(-1) is not None and l(1) is not None and l(2) is not None and
        l(3) is not None and l(4) is not None and l(5) is not None and l(6) is not None and
        l(-2) > n and l(-1) > n and l(1) >= n and l(2) == n and l(3) >= n and
        l(4) == n and l(5) > n and l(6) > n):
        return True
    return False


def find_latest_fractal_high(candles: list[dict], lookback: int) -> float | None:
    window = candles[-(lookback + 15):-1]
    for i in range(len(window) - 3, 2, -1):
        if _is_fractal_high(window, i):
            return window[i]["high"]
    return None


def find_latest_fractal_low(candles: list[dict], lookback: int) -> float | None:
    window = candles[-(lookback + 15):-1]
    for i in range(len(window) - 3, 2, -1):
        if _is_fractal_low(window, i):
            return window[i]["low"]
    return None


def find_fractal_highs(candles: list[dict]) -> list[tuple]:
    result = []
    for i in range(2, len(candles) - 2):
        if _is_fractal_high(candles, i):
            result.append((i, candles[i]["high"]))
    return result


def find_fractal_lows(candles: list[dict]) -> list[tuple]:
    result = []
    for i in range(2, len(candles) - 2):
        if _is_fractal_low(candles, i):
            result.append((i, candles[i]["low"]))
    return result


def detect_sfp(candles: list[dict], pivot_length: int, lookback: int) -> dict | None:
    if len(candles) < 15:
        return None

    last = candles[-2]

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
    if len(m_candles) < 10:
        return None
    if sfp_direction == "BEARISH":
        return _bearish_msb_breaker(m_candles)
    else:
        return _bullish_msb_breaker(m_candles)


def _bearish_msb_breaker(candles: list[dict]) -> dict | None:
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
