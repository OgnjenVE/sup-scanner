# ============================================================
#  SFP Scanner — Configuration
# ============================================================
import os

# --- Telegram ---
TELEGRAM_BOT_TOKEN = os.getenv("TELEGRAM_BOT_TOKEN", "YOUR_BOT_TOKEN_HERE")
TELEGRAM_CHAT_ID   = os.getenv("TELEGRAM_CHAT_ID",   "YOUR_CHAT_ID_HERE")

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

# ============================================================
#  TIMEFRAME CONFIGURATIONS
#  Each entry defines one complete SFP setup:
#    sfp_tf       — timeframe to scan for SFP
#    msb_tf       — timeframe to watch for MSB + Breaker
#    sfp_pivot    — candles each side for H1/4H/Daily swing detection
#    msb_pivot    — candles each side for MSB swing detection
#    sfp_lookback — how many candles back to look for swing points
#    watch_hours  — how long to watch MSB tf after SFP fires
#    sfp_candle_ms— candle duration in milliseconds (for freshness check)
#    label        — display name in Telegram alerts
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
        "sfp_candle_ms": 3_600_000,       # 1 hour in ms
    },
    {
        "label":         "4H/15M",
        "sfp_tf":        "4h",
        "msb_tf":        "15m",
        "sfp_pivot":     6,
        "msb_pivot":     4,
        "sfp_lookback":  30,
        "watch_hours":   12,
        "sfp_candle_ms": 14_400_000,      # 4 hours in ms
    },
    {
        "label":         "Daily/4H",
        "sfp_tf":        "1D",
        "msb_tf":        "4h",
        "sfp_pivot":     5,
        "msb_pivot":     3,
        "sfp_lookback":  30,
        "watch_hours":   72,              # 3 days
        "sfp_candle_ms": 86_400_000,      # 1 day in ms
    },
]

SCAN_INTERVAL_SEC = 60
