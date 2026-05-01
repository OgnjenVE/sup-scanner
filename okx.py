"""
okx.py  —  Fetch OHLCV candles from OKX USDT Perps
"""
import requests
import time

BASE_URL = "https://www.okx.com"

INTERVAL_MAP = {
    "1h": "1H",
    "5m": "5m",
}

def get_candles(symbol: str, interval: str, limit: int = 100) -> list[dict]:
    okx_interval = INTERVAL_MAP.get(interval, interval)
    url = f"{BASE_URL}/api/v5/market/candles"
    params = {"instId": symbol, "bar": okx_interval, "limit": str(limit)}

    for attempt in range(3):
        try:
            r = requests.get(url, params=params, timeout=10)
            if r.status_code == 200:
                data = r.json()
                if data.get("code") == "0" and len(data.get("data", [])) > 0:
                    candles = []
                    for c in reversed(data["data"]):
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
                print(f"[WARN] OKX failed for {symbol} {interval}: {e}")
            time.sleep(0.5)
    return []


def to_okx_symbol(usdt_symbol: str) -> str:
    """Convert BTCUSDT → BTC-USDT-SWAP"""
    base = usdt_symbol.replace("USDT", "")
    return f"{base}-USDT-SWAP"


def validate_symbol(usdt_symbol: str) -> bool:
    """
    Validate by actually fetching candles and checking data is returned.
    A 200 response with empty data means symbol doesn't exist.
    """
    okx_sym = to_okx_symbol(usdt_symbol)
    candles = get_candles(okx_sym, "1h", limit=3)
    return len(candles) > 0
