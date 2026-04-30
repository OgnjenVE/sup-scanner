"""
scanner.py  —  Main loop: scans coins every 60s for H1 SFP → M5 MSB + Breaker
"""
import time
import traceback
from datetime import datetime, timezone

import requests
from config import SYMBOLS, SCAN_INTERVAL_SEC, MSB_WATCH_HOURS, SWING_LOOKBACK, BINANCE_BASE_URL
from binance import get_candles
from strategy import detect_sfp, detect_msb_and_breaker
from telegram import alert_sfp, alert_msb_breaker


# ── State tracking ──────────────────────────────────────────
active_sfps: dict = {}

# One H1 candle = 3600 seconds. Only alert SFPs fresher than this.
SFP_MAX_AGE_SECONDS = 3600


def now_ts() -> float:
    return datetime.now(timezone.utc).timestamp()


def validate_symbols(symbols: list[str]) -> list[str]:
    """Test each symbol against Binance futures on startup. Skip invalid ones."""
    print("[INIT] Validating symbols against Binance futures...")
    valid, invalid = [], []
    for s in symbols:
        try:
            r = requests.get(
                f"{BINANCE_BASE_URL}/fapi/v1/klines",
                params={"symbol": s, "interval": "1h", "limit": 3},
                timeout=5
            )
            (valid if r.status_code == 200 else invalid).append(s)
        except Exception:
            invalid.append(s)
        time.sleep(0.05)

    if invalid:
        print(f"[INIT] Skipping {len(invalid)} symbols not on Binance futures: {invalid}")
    print(f"[INIT] Scanning {len(valid)} valid symbols.")
    return valid


def scan_h1(symbol: str):
    """
    Check if a new H1 SFP has formed on the last CLOSED candle.
    Only fires if the SFP candle closed within the last SFP_MAX_AGE_SECONDS.
    This ensures:
      - Real-time: alert fires within 60s of candle close
      - Restart-safe: old SFPs that already played out are ignored
    """
    candles = get_candles(symbol, "1h", limit=SWING_LOOKBACK + 10)
    if not candles:
        return

    sfp = detect_sfp(candles)
    if sfp is None:
        return

    sfp_candle_time = sfp["candle"]["open_time"]  # milliseconds

    # ── Freshness check ──────────────────────────────────────
    # SFP candle open_time is in ms. The candle CLOSES at open_time + 3600000ms.
    sfp_close_time_sec = (sfp_candle_time + 3_600_000) / 1000
    age_seconds = now_ts() - sfp_close_time_sec

    if age_seconds > SFP_MAX_AGE_SECONDS:
        # SFP is older than 1 H1 candle — skip, already played out
        return

    if age_seconds < 0:
        # Candle hasn't closed yet — skip
        return

    # ── Dedup check ─────────────────────────────────────────
    if symbol in active_sfps:
        existing_time = active_sfps[symbol]["sfp"]["candle"]["open_time"]
        if sfp_candle_time == existing_time:
            return   # already alerted this candle

    # ── Fresh new SFP — fire alert immediately ───────────────
    active_sfps[symbol] = {
        "sfp":         sfp,
        "detected_at": now_ts(),
        "msb_alerted": False,
    }
    alert_sfp(symbol, sfp)


def scan_m5(symbol: str, state: dict) -> bool:
    """
    For symbols with an active H1 SFP, check M5 for MSB + Breaker.
    Returns False when the watch window has expired.
    """
    sfp       = state["sfp"]
    detected  = state["detected_at"]
    direction = sfp["direction"]

    elapsed_hours = (now_ts() - detected) / 3600
    if elapsed_hours > MSB_WATCH_HOURS:
        print(f"[INFO] Watch window expired for {symbol}")
        return False

    if state["msb_alerted"]:
        return True

    m5_limit = int(MSB_WATCH_HOURS * 60 / 5) + 10
    candles = get_candles(symbol, "5m", limit=m5_limit)
    if not candles:
        return True

    candles_after = [c for c in candles if c["open_time"] >= detected * 1000]
    if len(candles_after) < 6:
        return True

    msb = detect_msb_and_breaker(candles_after, direction)
    if msb:
        alert_msb_breaker(symbol, sfp, msb)
        state["msb_alerted"] = True

    return True


def run():
    print("=" * 55)
    print("  H1/M5 SFP Scanner — Starting Up")
    print(f"  Configured symbols : {len(SYMBOLS)}")
    print(f"  SFP freshness window: {SFP_MAX_AGE_SECONDS}s (1 H1 candle)")
    print(f"  MSB watch window   : {MSB_WATCH_HOURS}h")
    print("=" * 55)

    valid_symbols = validate_symbols(SYMBOLS)
    if not valid_symbols:
        print("[ERROR] No valid symbols found.")
        return

    print("\n[READY] Scanner running. Ctrl+C to stop.\n")

    while True:
        try:
            scan_start = time.time()
            ts = datetime.now(timezone.utc).strftime("%Y-%m-%d %H:%M:%S UTC")
            print(f"[{ts}] Scanning {len(valid_symbols)} symbols...")

            for symbol in valid_symbols:
                try:
                    scan_h1(symbol)
                except Exception:
                    print(f"[ERROR] H1 scan failed for {symbol}:")
                    traceback.print_exc()
                time.sleep(0.1)

            to_remove = []
            for symbol, state in list(active_sfps.items()):
                try:
                    keep = scan_m5(symbol, state)
                    if not keep:
                        to_remove.append(symbol)
                except Exception:
                    print(f"[ERROR] M5 scan failed for {symbol}:")
                    traceback.print_exc()
                time.sleep(0.1)

            for s in to_remove:
                del active_sfps[s]

            elapsed = time.time() - scan_start
            watching = list(active_sfps.keys()) or ["none"]
            print(f"[INFO] Done in {elapsed:.1f}s | Watching M5: {', '.join(watching)}")

            time.sleep(max(0, SCAN_INTERVAL_SEC - elapsed))

        except KeyboardInterrupt:
            print("\n[INFO] Scanner stopped.")
            break
        except Exception:
            print("[ERROR] Unexpected error:")
            traceback.print_exc()
            time.sleep(10)


if __name__ == "__main__":
    run()
