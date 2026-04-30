# ============================================================
#  H1/M5 SFP Scanner — Configuration
# ============================================================

# --- Telegram ---
TELEGRAM_BOT_TOKEN = "8248929173:AAGtYvZUitIsyz3zxSpcFdG4IuTQfbO6myU"
TELEGRAM_CHAT_ID   = "771263170"

# --- Binance ---
BINANCE_BASE_URL = "https://fapi.binance.com"   # USDT Perps

# --- Strategy ---
SWING_LOOKBACK      = 50      # candles to look back for swing points
MSB_WATCH_HOURS     = 4       # hours to watch M5 after H1 SFP
SCAN_INTERVAL_SEC   = 60      # how often to scan (seconds)

# --- Symbols to scan (Binance USDT Perps) ---
SYMBOLS = [
    "AAVEUSDT",
    "ADAUSDT",
    "AIXBTUSDT",
    "ALGOUSDT",
    "APTUSDT",
    "ARBUSDT",
    "ASTERUSDT",
    "ATOMUSDT",
    "AVAXUSDT",
    "BCHUSDT",
    "BNBUSDT",
    "BONKUSDT",
    "BTCUSDT",
    "CRVUSDT",
    "DOGEUSDT",
    "DOTUSDT",
    "ETCUSDT",
    "ETHUSDT",
    "FARTCOINUSDT",
    "FILUSDT",
    "FLOKIUSDT",
    "GRASSUSDT",
    "HBARUSDT",
    "HYPEUSDT",
    "INJUSDT",
    "IPUSDT",
    "JTOUSDT",
    "JUPUSDT",
    "KAITOUSDT",
    "LDOUSDT",
    "LINKUSDT",
    "LITUSDT",
    "LTCUSDT",
    "MOODENGUSDT",
    "NEARUSDT",
    "ONDOUSDT",
    "OPUSDT",
    "ORDIUSDT",
    "PENGUUSDT",
    "PEPEUSDT",
    "PNUTUSDT",
    "POLUSDT",
    "POPCATUSDT",
    "PUMPUSDT",
    "RENDERUSDT",
    "SHIBUSDT",
    "SOLUSDT",
    "STXUSDT",
    "SUIUSDT",
    "TAOUSDT",
    "TIAUSDT",
    "TONUSDT",
    "TRUMPUSDT",
    "TRXUSDT",
    "UNIUSDT",
    "VIRTUALUSDT",
    "WIFUSDT",
    "WLDUSDT",
    "XRPUSDT",
    "ZECUSDT",
]
