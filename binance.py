"""
binance.py  —  Fetch OHLCV candles from Binance USDT Perps
Tries multiple base URLs to handle geo-blocking on cloud servers.
"""
import requests
import time

BASE_URLS = [
    "https://fapi.binance.com",
    "https://fapi1.binance.com",
    "https://fapi2.binance.com",
    "https://fapi3.binance.com",
]

def get_candles(symbol: str, interval: str, limit: int = 100) -> list[dict]:
    for base_url in BASE_URLS:
        url = f"{base_url}/fapi/v1/klines"
        params = {"symbol": symbol, "interval": interval, "limit": limit}
        for attempt in range(2):
            try:
                r = requests.get(url, params=params, timeout=10)
                if r.status_code == 200:
                    return [
                        {
                            "open_time": c[0],
                            "open":      float(c[1]),
                            "high":      float(c[2]),
                            "low":       float(c[3]),
                            "close":     float(c[4]),
                            "volume":    float(c[5]),
                        }
                        for c in r.json()
                    ]
            except Exception:
                time.sleep(0.5)

    print(f"[WARN] All URLs failed for {symbol} {interval}")
    return []
