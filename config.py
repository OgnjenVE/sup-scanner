# ============================================================
#  H1/M5 SFP Scanner — Configuration
# ============================================================
import os

# --- Telegram ---
TELEGRAM_BOT_TOKEN = os.getenv("TELEGRAM_BOT_TOKEN", "YOUR_BOT_TOKEN_HERE")
TELEGRAM_CHAT_ID   = os.getenv("TELEGRAM_CHAT_ID",   "YOUR_CHAT_ID_HERE")

# --- Strategy ---
SWING_LOOKBACK      = 50     # candles to look back for swing points
PIVOT_LENGTH        = 10     # candles each side required for a valid swing point
                             # 5  = picks up minor swings (too sensitive)
                             # 10 = significant swings only (recommended)
                             # 20 = only major structural highs/lows
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
