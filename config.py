# ============================================================
#  SFP Scanner — Configuration
# ============================================================
import os

# --- Telegram ---
TELEGRAM_BOT_TOKEN = os.getenv("TELEGRAM_BOT_TOKEN", "YOUR_BOT_TOKEN_HERE")
TELEGRAM_CHAT_ID   = os.getenv("TELEGRAM_CHAT_ID",   "YOUR_CHAT_ID_HERE")

# --- Symbols to scan ---
SYMBOLS = [
    # Crypto USDT Perps
    "AAVEUSDT", "ADAUSDT", "AIXBTUSDT", "ALGOUSDT", "APTUSDT",
    "ARBUSDT", "ASTERUSDT", "ATOMUSDT", "AVAXUSDT", "BCHUSDT",
    "BNBUSDT", "BONKUSDT", "BTCUSDT", "CRVUSDT", "DOGEUSDT",
    "DOTUSDT", "ETCUSDT", "ETHUSDT", "FARTCOINUSDT", "FILUSDT",
    "FLOKIUSDT", "GRASSUSDT", "HBARUSDT", "HYPEUSDT", "INJUSDT",
    "IPUSDT", "JTOUSDT", "JUPUSDT", "KAITOUSDT", "LDOUSDT",
    "LINKUSDT", "LITUSDT", "LTCUSDT", "MOODENGUSDT", "NEARUSDT",
    "ONDOUSDT", "OPUSDT", "ORDIUSDT", "PENGUUSDT", "PEPEUSDT",
    "PNUTUSDT", "POLUSDT", "POPCATUSDT", "PUMPUSDT", "RENDERUSDT",
    "SHIBUSDT", "SOLUSDT", "STXUSDT", "SUIUSDT", "TAOUSDT",
    "TIAUSDT", "TONUSDT", "TRUMPUSDT", "TRXUSDT", "UNIUSDT",
    "VIRTUALUSDT", "WIFUSDT", "WLDUSDT", "XRPUSDT", "ZECUSDT",

    # Stock Perpetuals (Bybit TradFi)
    "METAUSDT",   # Meta (Facebook)
    "AAPLUSDT",   # Apple
    "TSLAUSDT",   # Tesla
    "NVDAUSDT",   # NVIDIA
    "AMZNUSDT",   # Amazon
    "GOOGLUSDT",  # Alphabet (Google)
    "MSFTUSDT",   # Microsoft
    "COINUSDT",   # Coinbase
    "MSTRUSDT",   # MicroStrategy
    "NFLXUSDT",   # Netflix
    "AMDUSDT",    # AMD
    "INTCUSDT",   # Intel
    "UBERUSDT",   # Uber
    "ABNBUSDT",   # Airbnb
    "SOFIUSDT",   # SoFi
    "IONQUSDT",   # IonQ
    "PLTRUSDT",   # Palantir
    "RKLBUSDT",   # Rocket Lab
    "SNDKUSDT",   # SoundHound
    "AMDUDT",     # AMD (alt ticker)
]

# ============================================================
#  TIMEFRAME CONFIGURATIONS
# ============================================================
TIMEFRAME_CONFIGS = [
    {
        "label":         "H1/M5",
        "sfp_tf":        "1h",
        "msb_tf":        "5m",
        "sfp_pivot":     10,
        "msb_pivot":     5,
        "sfp_lookback":  30,
        "watch_hours":   4,
        "sfp_candle_ms": 3_600_000,
    },
    {
        "label":         "4H/15M",
        "sfp_tf":        "4h",
        "msb_tf":        "15m",
        "sfp_pivot":     6,
        "msb_pivot":     4,
        "sfp_lookback":  30,
        "watch_hours":   12,
        "sfp_candle_ms": 14_400_000,
    },
    {
        "label":         "Daily/4H",
        "sfp_tf":        "1D",
        "msb_tf":        "4h",
        "sfp_pivot":     5,
        "msb_pivot":     3,
        "sfp_lookback":  30,
        "watch_hours":   72,
        "sfp_candle_ms": 86_400_000,
    },
]

SCAN_INTERVAL_SEC = 60
