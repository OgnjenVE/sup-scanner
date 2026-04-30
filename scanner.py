"""
scanner.py  —  Main loop: scans coins every 60s for H1 SFP → M5 MSB + Breaker
Uses OKX USDT Perps (works from cloud servers without geo-blocking)
"""
import time
import traceback
from datetime import datetime, timezone

from config import SYMBOLS, SCAN_INTERVAL_SEC, MSB_WATCH_HOURS, SWING_LOOKBACK
from okx import get_candles, validate_symbol, to_okx_symbol
from strategy import detect_sfp, detect_msb_and_breaker
from telegram import alert_sfp, alert_msb_breaker


active_sfps: dict = {}
SFP_MAX_AGE_SECONDS = 3600


def now_ts() -> float:
    return datetime.now(timezone.utc).timestamp()


def validate_symbols(symbols: list[str]) -> list[str]:
    """Test each symbol against OKX on startup."""
    print("[INIT] Validating symbols against OKX...")
    valid, invalid = [], []
    for s in symbols:
        ok = validate_symbol(s)
        (valid if ok else invalid).append(s)
        time.sleep(0.1)

    if invalid:
        print(f"[INIT] Skipping {len(invalid)} invalid symbols: {invalid}")
    print(f"[INIT] Scanning {len(valid)} valid symbols.")
    return valid


def scan_h1(symbol: str):
    okx_sym = to_okx_symbol(symbol)
    candles = get_candles(okx_sym, "1h", limit=SWING_LOOKBACK + 10)
    if not candles:
        return

    sfp = detect_sfp(candles)
    if sfp is None:
        return

    sfp_candle_time = sfp["candle"]["open_time"]
    sfp_close_time_sec = (sfp_candle_time + 3_600_000) / 1000
    age_seconds = now_ts() - sfp_close_time_sec

    if age_seconds > SFP_MAX_AGE_SECONDS or age_seconds < 0:
        return

    if symbol in active_sfps:
        if active_sfps[symbol]["sfp"]["candle"]["open_time"] == sfp_candle_time:
            return

    active_sfps[symbol] = {
        "sfp":         sfp,
        "detected_at": now_ts(),
        "msb_alerted": False,
    }
    alert_sfp(symbol, sfp)


def scan_m5(symbol: str, state: dict) -> bool:
    sfp       = state["sfp"]
    detected  = state["detected_at"]
    direction = sfp["direction"]

    if (now_ts() - detected) / 3600 > MSB_WATCH_HOURS:
        print(f"[INFO] Watch window expired for {symbol}")
        return False

    if state["msb_alerted"]:
        return True

    okx_sym = to_okx_symbol(symbol)
    m5_limit = int(MSB_WATCH_HOURS * 60 / 5) + 10
    candles = get_candles(okx_sym, "5m", limit=m5_limit)
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
    print("  H1/M5 SFP Scanner — Starting Up (OKX)")
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
