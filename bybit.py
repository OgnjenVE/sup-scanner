"""
bybit.py  —  Fetch OHLCV candles from Bybit USDT Perps as fallback
"""
import requests
import time

BASE_URL = "https://api.bybit.com"

INTERVAL_MAP = {
    "1h": "60",
    "5m": "5",
}

def get_candles(symbol: str, interval: str, limit: int = 100) -> list[dict]:
    """
    Fetch candles from Bybit.
    symbol format: BTCUSDT (same as config)
    Returns list of { open_time, open, high, low, close, volume }
    """
    bybit_interval = INTERVAL_MAP.get(interval, interval)
    url = f"{BASE_URL}/v5/market/kline"
    params = {
        "category": "linear",
        "symbol":   symbol,
        "interval": bybit_interval,
        "limit":    str(limit),
    }

    for attempt in range(3):
        try:
            r = requests.get(url, params=params, timeout=10)
            if r.status_code == 200:
                data = r.json()
                if data.get("retCode") == 0:
                    candles = []
                    # Bybit returns newest first — reverse to oldest first
                    for c in reversed(data["result"]["list"]):
                        candles.append({
                            "open_time": int(c[0]),
                            "open":      float(c[1]),
                            "high":      float(c[2]),
                            "low":       float(c[3]),
                            "close":     float(c[4]),
                            "volume":    float(c[5]),
                        })
                    return candles
        except Exception as e:
            if attempt == 2:
                print(f"[WARN] Bybit failed for {symbol} {interval}: {e}")
            time.sleep(0.5)

    return []


def validate_symbol(symbol: str) -> bool:
    """Check if symbol exists on Bybit linear perps."""
    try:
        r = requests.get(
            f"{BASE_URL}/v5/market/kline",
            params={"category": "linear", "symbol": symbol, "interval": "60", "limit": "1"},
            timeout=5
        )
        if r.status_code == 200:
            data = r.json()
            return data.get("retCode") == 0 and len(data["result"]["list"]) > 0
    except Exception:
        pass
    return False
