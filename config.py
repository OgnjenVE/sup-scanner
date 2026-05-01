# ============================================================
#  H1/M5 SFP Scanner — Configuration
# ============================================================
import os

# --- Telegram ---
TELEGRAM_BOT_TOKEN = os.getenv("TELEGRAM_BOT_TOKEN", "YOUR_BOT_TOKEN_HERE")
TELEGRAM_CHAT_ID   = os.getenv("TELEGRAM_CHAT_ID",   "YOUR_CHAT_ID_HERE")

# --- Strategy ---
# How many H1 candles to look back for swing points (~1 day = 24, ~2 days = 48)
SWING_LOOKBACK      = 30     # look back 30 candles (~30 hours)
# How many candles each side must be lower/higher for a valid swing point
# Must be less than SWING_LOOKBACK / 2
PIVOT_LENGTH        = 10     # 10 candles each side = significant structural swing
MSB_WATCH_HOURS     = 4      # hours to watch M5 after H1 SFP
SCAN_INTERVAL_SEC   = 60     # how often to scan (seconds)

# --- Symbols to scan ---
SYMBOLS = [
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
]

# M5 pivot length for MSB detection (candles each side)
# Higher = only significant M5 swing points qualify as MSB levels
M5_PIVOT_LENGTH     = 5
