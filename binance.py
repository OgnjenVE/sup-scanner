"""
binance.py  —  Fetch OHLCV candles from Binance USDT Perps
"""
import requests
import time
from config import BINANCE_BASE_URL


def get_candles(symbol: str, interval: str, limit: int = 100) -> list[dict]:
    """
    Returns a list of candle dicts:
      { open, high, low, close, volume, open_time }
    Interval examples: '1h', '5m'
    """
    url = f"{BINANCE_BASE_URL}/fapi/v1/klines"
    params = {"symbol": symbol, "interval": interval, "limit": limit}

    for attempt in range(3):
        try:
            r = requests.get(url, params=params, timeout=10)
            r.raise_for_status()
            raw = r.json()
            candles = []
            for c in raw:
                candles.append({
                    "open_time": c[0],
                    "open":      float(c[1]),
                    "high":      float(c[2]),
                    "low":       float(c[3]),
                    "close":     float(c[4]),
                    "volume":    float(c[5]),
                })
            return candles
        except Exception as e:
            if attempt == 2:
                print(f"[WARN] Failed to fetch {symbol} {interval}: {e}")
                return []
            time.sleep(1)
    return []
