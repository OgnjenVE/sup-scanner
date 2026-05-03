"""
strategy.py  —  SFP and MSB + Breaker detection logic
Swing points: XO/Williams Fractal (n=2)
Significance: XO swing point labels (HH/HL/LH/LL)
Trend: XO Macro Trend (EMA 12/25)
"""


# ──────────────────────────────────────────────
#  WILLIAMS FRACTAL DETECTION (XO style)
# ──────────────────────────────────────────────

def _is_fractal_high(candles: list[dict], idx: int) -> bool:
    n_candles = len(candles)
    if idx < 2 or idx >= n_candles - 2:
        return False
    n = candles[idx]["high"]
    def h(o):
        i = idx + o
        return candles[i]["high"] if 0 <= i < n_candles else None

    if all(h(o) is not None for o in [-2,-1,1,2]) and h(-2)<n and h(-1)<n and h(1)<n and h(2)<n:
        return True
    if all(h(o) is not None for o in [-2,-1,1,2,3]) and h(-2)<n and h(-1)<n and h(1)==n and h(2)<n and h(3)<n:
        return True
    if all(h(o) is not None for o in [-2,-1,1,2,3,4]) and h(-2)<n and h(-1)<n and h(1)<=n and h(2)==n and h(3)<n and h(4)<n:
        return True
    if all(h(o) is not None for o in [-2,-1,1,2,3,4,5]) and h(-2)<n and h(-1)<n and h(1)<=n and h(2)==n and h(3)==n and h(4)<n and h(5)<n:
        return True
    if all(h(o) is not None for o in [-2,-1,1,2,3,4,5,6]) and h(-2)<n and h(-1)<n and h(1)<=n and h(2)==n and h(3)<=n and h(4)==n and h(5)<n and h(6)<n:
        return True
    return False


def _is_fractal_low(candles: list[dict], idx: int) -> bool:
    n_candles = len(candles)
    if idx < 2 or idx >= n_candles - 2:
        return False
    n = candles[idx]["low"]
    def l(o):
        i = idx + o
        return candles[i]["low"] if 0 <= i < n_candles else None

    if all(l(o) is not None for o in [-2,-1,1,2]) and l(-2)>n and l(-1)>n and l(1)>n and l(2)>n:
        return True
    if all(l(o) is not None for o in [-2,-1,1,2,3]) and l(-2)>n and l(-1)>n and l(1)==n and l(2)>n and l(3)>n:
        return True
    if all(l(o) is not None for o in [-2,-1,1,2,3,4]) and l(-2)>n and l(-1)>n and l(1)>=n and l(2)==n and l(3)>n and l(4)>n:
        return True
    if all(l(o) is not None for o in [-2,-1,1,2,3,4,5]) and l(-2)>n and l(-1)>n and l(1)>=n and l(2)==n and l(3)==n and l(4)>n and l(5)>n:
        return True
    if all(l(o) is not None for o in [-2,-1,1,2,3,4,5,6]) and l(-2)>n and l(-1)>n and l(1)>=n and l(2)==n and l(3)>=n and l(4)==n and l(5)>n and l(6)>n:
        return True
    return False


# ──────────────────────────────────────────────
#  SWING POINT LABELS (XO style: HH/HL/LH/LL)
# ──────────────────────────────────────────────

def get_fractal_highs(candles: list[dict]) -> list[tuple]:
    """Returns list of (idx, price) for all fractal highs."""
    return [(i, candles[i]["high"]) for i in range(2, len(candles)-2)
            if _is_fractal_high(candles, i)]


def get_fractal_lows(candles: list[dict]) -> list[tuple]:
    """Returns list of (idx, price) for all fractal lows."""
    return [(i, candles[i]["low"]) for i in range(2, len(candles)-2)
            if _is_fractal_low(candles, i)]


def get_swing_label_high(candles: list[dict], lookback: int) -> tuple | None:
    """
    Returns (price, label) of the most recent fractal high with its XO label.
    HH = higher than previous fractal high
    LH = lower than previous fractal high
    """
    window = candles[-(lookback + 15):-1]
    highs = get_fractal_highs(window)
    if len(highs) < 2:
        return None
    price = highs[-1][1]
    prev  = highs[-2][1]
    label = "HH" if price > prev else "LH" if price < prev else "EH"
    return (price, label)


def get_swing_label_low(candles: list[dict], lookback: int) -> tuple | None:
    """
    Returns (price, label) of the most recent fractal low with its XO label.
    LL = lower than previous fractal low
    HL = higher than previous fractal low
    """
    window = candles[-(lookback + 15):-1]
    lows = get_fractal_lows(window)
    if len(lows) < 2:
        return None
    price = lows[-1][1]
    prev  = lows[-2][1]
    label = "LL" if price < prev else "HL" if price > prev else "EL"
    return (price, label)


# ──────────────────────────────────────────────
#  XO MACRO TREND (EMA 12/25)
# ──────────────────────────────────────────────

def _ema(values: list[float], period: int) -> list[float]:
    """Calculate EMA for a list of values."""
    if len(values) < period:
        return []
    k = 2 / (period + 1)
    ema = [sum(values[:period]) / period]
    for v in values[period:]:
        ema.append(v * k + ema[-1] * (1 - k))
    return ema


def get_trend(candles: list[dict], fast: int = 12, slow: int = 25) -> str:
    """
    XO Macro Trend: EMA12 vs EMA25.
    Returns 'BULLISH', 'BEARISH', or 'NEUTRAL'
    """
    closes = [c["close"] for c in candles]
    if len(closes) < slow + 5:
        return "NEUTRAL"
    fast_ema = _ema(closes, fast)
    slow_ema = _ema(closes, slow)
    if not fast_ema or not slow_ema:
        return "NEUTRAL"
    # Align lengths
    min_len = min(len(fast_ema), len(slow_ema))
    f = fast_ema[-1]
    s = slow_ema[-1]
    if f > s:
        return "BULLISH"
    elif f < s:
        return "BEARISH"
    return "NEUTRAL"


# ──────────────────────────────────────────────
#  SFP DETECTION with significance filter
# ──────────────────────────────────────────────

def detect_sfp(candles: list[dict], pivot_length: int, lookback: int) -> dict | None:
    """
    SFP detection using XO fractal swing points.
    Significance filter: only fire on LL/HL for bullish, HH/LH for bearish.
    Also returns trend context from XO Macro Trend.
    """
    if len(candles) < 15:
        return None

    last = candles[-2]  # last fully closed candle

    swing_high_data = get_swing_label_high(candles, lookback)
    swing_low_data  = get_swing_label_low(candles, lookback)
    trend = get_trend(candles)

    # BEARISH SFP — only on HH or LH (any significant high)
    if swing_high_data is not None:
        swing_high, sh_label = swing_high_data
        if (last["high"]  > swing_high and
            last["open"]  < swing_high and
            last["close"] < swing_high):
            # Significance filter: require HH or LH (not just any fractal)
            if sh_label in ("HH", "LH"):
                return {
                    "direction":    "BEARISH",
                    "type":         "SFP",
                    "swept_level":  swing_high,
                    "swing_label":  sh_label,
                    "wick_tip":     last["high"],
                    "candle":       last,
                    "trend":        trend,
                }

    # BULLISH SFP — only on LL or HL (any significant low)
    if swing_low_data is not None:
        swing_low, sl_label = swing_low_data
        if (last["low"]   < swing_low and
            last["open"]  > swing_low and
            last["close"] > swing_low):
            # Significance filter: require LL or HL
            if sl_label in ("LL", "HL"):
                return {
                    "direction":    "BULLISH",
                    "type":         "SFP",
                    "swept_level":  swing_low,
                    "swing_label":  sl_label,
                    "wick_tip":     last["low"],
                    "candle":       last,
                    "trend":        trend,
                }

    return None


# ──────────────────────────────────────────────
#  MSB + BREAKER DETECTION
# ──────────────────────────────────────────────

def detect_msb_and_breaker(m_candles: list[dict], sfp_direction: str,
                            msb_pivot: int) -> dict | None:
    if len(m_candles) < 10:
        return None
    if sfp_direction == "BEARISH":
        return _bearish_msb_breaker(m_candles)
    else:
        return _bullish_msb_breaker(m_candles)


def _bearish_msb_breaker(candles: list[dict]) -> dict | None:
    fractal_lows = get_fractal_lows(candles)
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
    fractal_highs = get_fractal_highs(candles)
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
