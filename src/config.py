import os
from dotenv import load_dotenv

load_dotenv()

TELEGRAM_BOT_TOKEN = os.getenv("TELEGRAM_BOT_TOKEN", "")
TELEGRAM_CHAT_ID = os.getenv("TELEGRAM_CHAT_ID", "")

BYBIT_BASE_URL = os.getenv("BYBIT_BASE_URL", "https://api.bybit.com")

# High quality filters (strict)
SCAN_INTERVAL_MINUTES = int(os.getenv("SCAN_INTERVAL_MINUTES", "15"))
MIN_TURNOVER_USDT = float(os.getenv("MIN_TURNOVER_USDT", "300000"))
MIN_VOLUME_USDT = float(os.getenv("MIN_VOLUME_USDT", "200000"))
MAX_SPREAD_PCT = float(os.getenv("MAX_SPREAD_PCT", "0.18"))
MIN_RR = float(os.getenv("MIN_RR", "1.8"))
RISK_PER_TRADE_PCT = float(os.getenv("RISK_PER_TRADE_PCT", "1.5"))

# Categories to scan
CATEGORIES = ["spot", "linear"]

# Preferred quote asset
PREFERRED_QUOTE = "USDC"

# Timeframes for structure
KLINE_INTERVAL = "15"
KLINE_LIMIT = 100
