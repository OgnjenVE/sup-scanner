"""
scanner.py  —  Multi-timeframe SFP Scanner
Timeframe pairs: H1/M5, 4H/15M, Daily/4H
Data sources: OKX (primary) → Bybit (fallback)
Confluence detection: fires special alert when multiple TFs align
"""
import time
import traceback
from datetime import datetime, timezone

from config import SYMBOLS, SCAN_INTERVAL_SEC, TIMEFRAME_CONFIGS
import okx
import bybit
from strategy import detect_sfp, detect_msb_and_breaker
from telegram import alert_sfp, alert_msb_breaker, alert_confluence_sfp, alert_confluence_msb


# active_sfps: { (symbol, label): { sfp, detected_at, msb_alerted, tf_config } }
active_sfps: dict = {}
symbol_source: dict = {}

SFP_ALERT_MAX_AGE = SCAN_INTERVAL_SEC * 2


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


def scan_all_sfps(valid_symbols: list[str]):
    """
    Scan all symbols across all timeframes for SFPs.
    Detect confluence when multiple TFs fire on the same symbol.
    """
    # Collect all new SFPs this cycle: { symbol: [(sfp, label, tf_config)] }
    new_sfps: dict = {}

    for tf_config in TIMEFRAME_CONFIGS:
        label        = tf_config["label"]
        sfp_tf       = tf_config["sfp_tf"]
        sfp_pivot    = tf_config["sfp_pivot"]
        sfp_lookback = tf_config["sfp_lookback"]
        candle_ms    = tf_config["sfp_candle_ms"]

        limit = sfp_lookback + 20
        for symbol in valid_symbols:
            try:
                candles = get_candles_any(symbol, sfp_tf, limit)
                if not candles:
                    continue

                sfp = detect_sfp(candles, sfp_pivot, sfp_lookback)
                if sfp is None:
                    continue

                sfp_candle_time    = sfp["candle"]["open_time"]
                sfp_close_time_sec = (sfp_candle_time + candle_ms) / 1000
                age_seconds        = now_ts() - sfp_close_time_sec

                if age_seconds < 0 or age_seconds > SFP_ALERT_MAX_AGE:
                    continue

                key = (symbol, label)
                if key in active_sfps:
                    if active_sfps[key]["sfp"]["candle"]["open_time"] == sfp_candle_time:
                        continue  # already alerted

                # New SFP found — add to active watches
                active_sfps[key] = {
                    "sfp":         sfp,
                    "detected_at": now_ts(),
                    "msb_alerted": False,
                    "tf_config":   tf_config,
                }

                # Track for confluence detection
                if symbol not in new_sfps:
                    new_sfps[symbol] = []
                new_sfps[symbol].append((sfp, label, tf_config))

            except Exception:
                print(f"[ERROR] SFP scan failed {symbol} {label}:")
                traceback.print_exc()
            time.sleep(0.05)

    # Fire alerts — confluence if multiple TFs, individual if single
    for symbol, sfp_entries in new_sfps.items():
        if len(sfp_entries) >= 2:
            # Check all same direction for cleaner confluence
            directions = set(sfp["direction"] for sfp, _, _ in sfp_entries)
            if len(directions) == 1:
                # All same direction — fire confluence alert
                alert_confluence_sfp(symbol, [(sfp, label) for sfp, label, _ in sfp_entries])
            else:
                # Different directions — fire separately
                for sfp, label, _ in sfp_entries:
                    alert_sfp(symbol, sfp, label)
        else:
            sfp, label, _ = sfp_entries[0]
            alert_sfp(symbol, sfp, label)


def scan_all_msbs():
    """
    Scan MSB timeframe for all active SFP watches.
    Detect confluence when multiple TFs confirm MSB on same symbol.
    """
    # Collect new MSB confirmations: { symbol: [(sfp, msb, label)] }
    new_msbs: dict = {}

    to_remove = []
    for key, state in list(active_sfps.items()):
        symbol, label = key
        sfp       = state["sfp"]
        detected  = state["detected_at"]
        tf_config = state["tf_config"]
        msb_tf    = tf_config["msb_tf"]
        msb_pivot = tf_config["msb_pivot"]
        watch_h   = tf_config["watch_hours"]

        if (now_ts() - detected) / 3600 > watch_h:
            print(f"[INFO] {label} watch expired for {symbol}")
            to_remove.append(key)
            continue

        if state["msb_alerted"]:
            continue

        candle_minutes = {"5m": 5, "15m": 15, "4h": 240}.get(msb_tf, 60)
        msb_limit = int(watch_h * 60 / candle_minutes) + 10

        try:
            candles = get_candles_any(symbol, msb_tf, msb_limit)
            if not candles:
                continue

            candles_after = [c for c in candles if c["open_time"] >= detected * 1000]
            if len(candles_after) < 10:
                continue

            msb = detect_msb_and_breaker(candles_after, sfp["direction"], msb_pivot)
            if msb:
                state["msb_alerted"] = True
                if symbol not in new_msbs:
                    new_msbs[symbol] = []
                new_msbs[symbol].append((sfp, msb, label))

        except Exception:
            print(f"[ERROR] MSB scan failed {symbol} {label}:")
            traceback.print_exc()
        time.sleep(0.05)

    for k in to_remove:
        del active_sfps[k]

    # Fire MSB alerts — confluence if multiple TFs, individual if single
    for symbol, msb_entries in new_msbs.items():
        if len(msb_entries) >= 2:
            directions = set(msb["direction"] for _, msb, _ in msb_entries)
            if len(directions) == 1:
                alert_confluence_msb(symbol, msb_entries)
            else:
                for sfp, msb, label in msb_entries:
                    alert_msb_breaker(symbol, sfp, msb, label)
        else:
            sfp, msb, label = msb_entries[0]
            alert_msb_breaker(symbol, sfp, msb, label)


def run():
    print("=" * 55)
    print("  Multi-TF SFP Scanner — Starting Up")
    print(f"  Symbols configured : {len(SYMBOLS)}")
    print(f"  Timeframe pairs    : {[c['label'] for c in TIMEFRAME_CONFIGS]}")
    print(f"  SFP freshness      : {SFP_ALERT_MAX_AGE}s")
    print(f"  Data sources       : OKX → Bybit fallback")
    print(f"  Confluence alerts  : enabled")
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
            print(f"[{ts}] Scanning {len(valid_symbols)} x {len(TIMEFRAME_CONFIGS)} TFs...")

            scan_all_sfps(valid_symbols)
            scan_all_msbs()

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
