"""
scanner.py  —  Multi-timeframe SFP Scanner
Timeframe pairs: H1/M5, 4H/15M, Daily/4H
Data sources: OKX (primary) → Bybit (fallback)
"""
import time
import traceback
from datetime import datetime, timezone

from config import SYMBOLS, SCAN_INTERVAL_SEC, TIMEFRAME_CONFIGS
import okx
import bybit
from strategy import detect_sfp, detect_msb_and_breaker
from telegram import alert_sfp, alert_msb_breaker


# active_sfps: { (symbol, label): { sfp, detected_at, msb_alerted } }
active_sfps: dict = {}
symbol_source: dict = {}

SFP_ALERT_MAX_AGE = SCAN_INTERVAL_SEC * 2   # 120s freshness window


def now_ts() -> float:
    return datetime.now(timezone.utc).timestamp()


def get_candles_any(symbol: str, interval: str, limit: int) -> list[dict]:
    source = symbol_source.get(symbol, "okx")
    if source == "okx":
        okx_sym = okx.to_okx_symbol(symbol)
        candles = okx.get_candles(okx_sym, interval, limit)
        if candles:
            return candles
        candles = bybit.get_candles(symbol, interval, limit)
        if candles:
            symbol_source[symbol] = "bybit"
            print(f"[INFO] {symbol} switched to Bybit")
            return candles
    else:
        candles = bybit.get_candles(symbol, interval, limit)
        if candles:
            return candles
        okx_sym = okx.to_okx_symbol(symbol)
        candles = okx.get_candles(okx_sym, interval, limit)
        if candles:
            symbol_source[symbol] = "okx"
            return candles
    return []


def validate_symbols(symbols: list[str]) -> list[str]:
    print("[INIT] Validating symbols (OKX → Bybit fallback)...")
    valid, invalid = [], []
    for s in symbols:
        if okx.validate_symbol(s):
            valid.append(s)
            symbol_source[s] = "okx"
        elif bybit.validate_symbol(s):
            valid.append(s)
            symbol_source[s] = "bybit"
            print(f"  [INFO] {s} → Bybit")
        else:
            invalid.append(s)
        time.sleep(0.1)

    if invalid:
        print(f"[INIT] Skipping {len(invalid)} not found: {invalid}")
    okx_c   = sum(1 for v in symbol_source.values() if v == "okx")
    bybit_c = sum(1 for v in symbol_source.values() if v == "bybit")
    print(f"[INIT] {len(valid)} valid — OKX: {okx_c} | Bybit: {bybit_c}")
    return valid


def scan_sfp(symbol: str, tf_config: dict):
    """Scan one symbol on the SFP timeframe."""
    label       = tf_config["label"]
    sfp_tf      = tf_config["sfp_tf"]
    sfp_pivot   = tf_config["sfp_pivot"]
    sfp_lookback= tf_config["sfp_lookback"]
    candle_ms   = tf_config["sfp_candle_ms"]
    watch_hours = tf_config["watch_hours"]

    limit = sfp_lookback + sfp_pivot + 5
    candles = get_candles_any(symbol, sfp_tf, limit)
    if not candles:
        return

    sfp = detect_sfp(candles, sfp_pivot, sfp_lookback)
    if sfp is None:
        return

    sfp_candle_time    = sfp["candle"]["open_time"]
    sfp_close_time_sec = (sfp_candle_time + candle_ms) / 1000
    age_seconds        = now_ts() - sfp_close_time_sec

    if age_seconds < 0 or age_seconds > SFP_ALERT_MAX_AGE:
        return

    key = (symbol, label)
    if key in active_sfps:
        if active_sfps[key]["sfp"]["candle"]["open_time"] == sfp_candle_time:
            return

    active_sfps[key] = {
        "sfp":         sfp,
        "detected_at": now_ts(),
        "msb_alerted": False,
        "tf_config":   tf_config,
    }
    alert_sfp(symbol, sfp, label)


def scan_msb(symbol: str, state: dict) -> bool:
    """Watch MSB timeframe after SFP detected."""
    sfp       = state["sfp"]
    detected  = state["detected_at"]
    tf_config = state["tf_config"]
    label     = tf_config["label"]
    msb_tf    = tf_config["msb_tf"]
    msb_pivot = tf_config["msb_pivot"]
    watch_h   = tf_config["watch_hours"]

    if (now_ts() - detected) / 3600 > watch_h:
        print(f"[INFO] {label} watch expired for {symbol}")
        return False

    if state["msb_alerted"]:
        return True

    # Calculate how many MSB candles to fetch
    candle_minutes = {"5m": 5, "15m": 15, "4h": 240}.get(msb_tf, 60)
    msb_limit = int(watch_h * 60 / candle_minutes) + 10

    candles = get_candles_any(symbol, msb_tf, msb_limit)
    if not candles:
        return True

    candles_after = [c for c in candles if c["open_time"] >= detected * 1000]
    if len(candles_after) < msb_pivot * 2 + 2:
        return True

    msb = detect_msb_and_breaker(candles_after, sfp["direction"], msb_pivot)
    if msb:
        alert_msb_breaker(symbol, sfp, msb, label)
        state["msb_alerted"] = True

    return True


def run():
    print("=" * 55)
    print("  Multi-TF SFP Scanner — Starting Up")
    print(f"  Symbols configured : {len(SYMBOLS)}")
    print(f"  Timeframe pairs    : {[c['label'] for c in TIMEFRAME_CONFIGS]}")
    print(f"  SFP freshness      : {SFP_ALERT_MAX_AGE}s")
    print(f"  Data sources       : OKX → Bybit fallback")
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
            print(f"[{ts}] Scanning {len(valid_symbols)} symbols x {len(TIMEFRAME_CONFIGS)} TFs...")

            # Scan SFP for all symbols and all timeframe configs
            for tf_config in TIMEFRAME_CONFIGS:
                for symbol in valid_symbols:
                    try:
                        scan_sfp(symbol, tf_config)
                    except Exception:
                        print(f"[ERROR] SFP scan failed {symbol} {tf_config['label']}:")
                        traceback.print_exc()
                    time.sleep(0.05)

            # Scan MSB for all active watches
            to_remove = []
            for key, state in list(active_sfps.items()):
                symbol, label = key
                try:
                    keep = scan_msb(symbol, state)
                    if not keep:
                        to_remove.append(key)
                except Exception:
                    print(f"[ERROR] MSB scan failed {symbol} {label}:")
                    traceback.print_exc()
                time.sleep(0.05)

            for k in to_remove:
                del active_sfps[k]

            elapsed = time.time() - scan_start
            watching = [f"{s}({l})" for s, l in active_sfps.keys()] or ["none"]
            print(f"[INFO] Done in {elapsed:.1f}s | Watching: {', '.join(watching)}")

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
