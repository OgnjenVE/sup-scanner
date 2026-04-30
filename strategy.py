"""
strategy.py  —  SFP and MSB + Breaker detection logic
Ported from LuxAlgo Swing Failure Pattern indicator (CC BY-NC-SA 4.0)
"""
from config import SWING_LOOKBACK


# ──────────────────────────────────────────────
#  PIVOT HIGH / LOW  (LuxAlgo style)
#  ta.pivothigh(len, 1) means:
#    - look back `len` bars to the LEFT
#    - confirm with 1 bar to the RIGHT
#    - middle must be highest/lowest of all bars in the window
# ──────────────────────────────────────────────

def pivot_high(candles: list[dict], length: int = 5) -> float | None:
    """
    Returns the pivot high value at candles[-2] (last confirmed bar),
    or None if no pivot exists there.
    LuxAlgo uses pivothigh(len, 1):
      - candles[-2] is the pivot candidate
      - `length` bars to the left must all have lower highs
      - 1 bar to the right (candles[-1]) must have a lower high
    """
    idx = len(candles) - 2   # pivot candidate (last closed candle)
    if idx < length:
        return None

    candidate = candles[idx]["high"]

    # Check `length` bars to the left
    for i in range(1, length + 1):
        if candles[idx - i]["high"] >= candidate:
            return None

    # Check 1 bar to the right
    if candles[idx + 1]["high"] >= candidate:
        return None

    return candidate


def pivot_low(candles: list[dict], length: int = 5) -> float | None:
    """
    Returns the pivot low value at candles[-2], or None.
    """
    idx = len(candles) - 2
    if idx < length:
        return None

    candidate = candles[idx]["low"]

    for i in range(1, length + 1):
        if candles[idx - i]["low"] <= candidate:
            return None

    if candles[idx + 1]["low"] <= candidate:
        return None

    return candidate


# ──────────────────────────────────────────────
#  SFP STATE  (tracks most recent swing)
# ──────────────────────────────────────────────

class SFPState:
    def __init__(self):
        self.swing_high_price = None
        self.swing_high_bar   = None
        self.swing_low_price  = None
        self.swing_low_bar    = None

    def update(self, candles: list[dict], length: int = 5):
        """Update most recent swing high and low from candle history."""
        # Scan last SWING_LOOKBACK candles for the most recent pivot
        window = candles[-(SWING_LOOKBACK + length + 2):]

        # Find most recent pivot high
        for i in range(len(window) - 1, length, -1):
            sub = window[:i + 2] if i + 2 <= len(window) else window
            ph = _pivot_high_at(sub, length, i)
            if ph is not None:
                self.swing_high_price = ph
                self.swing_high_bar   = i
                break

        # Find most recent pivot low
        for i in range(len(window) - 1, length, -1):
            sub = window[:i + 2] if i + 2 <= len(window) else window
            pl = _pivot_low_at(sub, length, i)
            if pl is not None:
                self.swing_low_price = pl
                self.swing_low_bar   = i
                break


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


# ──────────────────────────────────────────────
#  SFP DETECTION  (H1)
#  Ported directly from LuxAlgo logic
# ──────────────────────────────────────────────

def detect_sfp(candles: list[dict], length: int = 5) -> dict | None:
    """
    Check the last CLOSED H1 candle for an SFP.
    candles[-1] is still forming, candles[-2] is the last closed candle.

    Bearish SFP (LuxAlgo):
      high > swing_high AND open < swing_high AND close < swing_high

    Bullish SFP (LuxAlgo):
      low < swing_low AND open > swing_low AND close > swing_low

    Swing = most recent pivothigh/pivotlow(length, 1) in last SWING_LOOKBACK bars.
    """
    if len(candles) < length + 4:
        return None

    last = candles[-2]   # last fully closed candle
    prior = candles[:-1] # everything up to but not including current forming candle

    # Find most recent swing high in prior candles
    swing_high = None
    for i in range(len(prior) - 2, length - 1, -1):
        ph = _pivot_high_at(prior, length, i)
        if ph is not None:
            swing_high = ph
            break

    # Find most recent swing low in prior candles
    swing_low = None
    for i in range(len(prior) - 2, length - 1, -1):
        pl = _pivot_low_at(prior, length, i)
        if pl is not None:
            swing_low = pl
            break

    # BEARISH SFP — wick above swing high, open AND close below it
    if swing_high is not None:
        if (last["high"] > swing_high and
            last["open"]  < swing_high and
            last["close"] < swing_high):
            return {
                "direction":   "BEARISH",
                "type":        "SFP",
                "swept_level": swing_high,
                "candle":      last,
            }

    # BULLISH SFP — wick below swing low, open AND close above it
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


# ──────────────────────────────────────────────
#  MSB + BREAKER DETECTION  (M5)
# ──────────────────────────────────────────────

def detect_msb_and_breaker(m5_candles: list[dict], sfp_direction: str) -> dict | None:
    if len(m5_candles) < 6:
        return None
    if sfp_direction == "BEARISH":
        return _bearish_msb_breaker(m5_candles)
    else:
        return _bullish_msb_breaker(m5_candles)


def _bearish_msb_breaker(candles: list[dict]) -> dict | None:
    swing_lows = []
    for i in range(2, len(candles) - 1):
        pl = _pivot_low_at(candles, 2, i)
        if pl is not None:
            swing_lows.append((i, pl))

    for sl_idx, swing_low in reversed(swing_lows):
        # Find candle that closes below the swing low (MSB)
        break_idx = None
        for i in range(sl_idx + 1, len(candles)):
            if candles[i]["close"] < swing_low:
                break_idx = i
                break

        if break_idx is None:
            continue

        # Find last up-close candle before the break (breaker)
        breaker_candle = None
        for i in range(break_idx - 1, sl_idx - 1, -1):
            if candles[i]["close"] > candles[i]["open"]:
                breaker_candle = candles[i]
                break

        if breaker_candle is None:
            continue

        breaker_high = breaker_candle["high"]
        breaker_low  = breaker_candle["low"]

        # Alert when current candle enters breaker zone from below
        current = candles[-1]
        if current["high"] >= breaker_low and current["close"] <= breaker_high:
            return {
                "direction":    "BEARISH",
                "type":         "MSB_BREAKER",
                "msb_level":    swing_low,
                "breaker_high": breaker_high,
                "breaker_low":  breaker_low,
                "breaker_candle": breaker_candle,
                "current_candle": current,
            }

    return None


def _bullish_msb_breaker(candles: list[dict]) -> dict | None:
    swing_highs = []
    for i in range(2, len(candles) - 1):
        ph = _pivot_high_at(candles, 2, i)
        if ph is not None:
            swing_highs.append((i, ph))

    for sh_idx, swing_high in reversed(swing_highs):
        # Find candle that closes above the swing high (MSB)
        break_idx = None
        for i in range(sh_idx + 1, len(candles)):
            if candles[i]["close"] > swing_high:
                break_idx = i
                break

        if break_idx is None:
            continue

        # Find last down-close candle before the break (breaker)
        breaker_candle = None
        for i in range(break_idx - 1, sh_idx - 1, -1):
            if candles[i]["close"] < candles[i]["open"]:
                breaker_candle = candles[i]
                break

        if breaker_candle is None:
            continue

        breaker_high = breaker_candle["high"]
        breaker_low  = breaker_candle["low"]

        # Alert when current candle enters breaker zone from above
        current = candles[-1]
        if current["low"] <= breaker_high and current["close"] >= breaker_low:
            return {
                "direction":    "BULLISH",
                "type":         "MSB_BREAKER",
                "msb_level":    swing_high,
                "breaker_high": breaker_high,
                "breaker_low":  breaker_low,
                "breaker_candle": breaker_candle,
                "current_candle": current,
            }

    return None
