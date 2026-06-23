"""
config.py
----------
All settings loaded from .env file. Never hard-code keys here.
"""

import os
from dotenv import load_dotenv

load_dotenv()

# ── Exchange ──────────────────────────────────────
BYBIT_API_KEY    = os.getenv("BYBIT_API_KEY", "")
BYBIT_API_SECRET = os.getenv("BYBIT_API_SECRET", "")
USE_TESTNET      = os.getenv("USE_TESTNET", "true").lower() == "true"

# ── Trading ───────────────────────────────────────
SYMBOL       = os.getenv("SYMBOL", "BTC/USDT")
SYMBOLS      = os.getenv("SYMBOLS", SYMBOL)
TIMEFRAMES   = os.getenv("TIMEFRAMES", "15m,30m,1h")
MIN_TIMEFRAME_CONFLUENCE = int(os.getenv("MIN_TIMEFRAME_CONFLUENCE", "2"))
TIMEFRAME    = os.getenv("TIMEFRAME", "1h")
MARKET_TYPE  = os.getenv("MARKET_TYPE", "spot")
CANDLE_LIMIT = int(os.getenv("CANDLE_LIMIT", "250"))
LOOP_INTERVAL = int(os.getenv("LOOP_INTERVAL", "3600"))

# ── Risk Management ───────────────────────────────
MAX_RISK_PER_TRADE = float(os.getenv("MAX_RISK_PER_TRADE", "0.01"))
STOP_LOSS_PCT      = float(os.getenv("STOP_LOSS_PCT", "0.02"))
TAKE_PROFIT_PCT    = float(os.getenv("TAKE_PROFIT_PCT", "0.04"))

# ── Indicators ────────────────────────────────────
RSI_PERIOD   = int(os.getenv("RSI_PERIOD", "14"))
RSI_OVERSOLD = float(os.getenv("RSI_OVERSOLD", "30"))
RSI_OVERBOUGHT = float(os.getenv("RSI_OVERBOUGHT", "70"))

EMA_FAST = int(os.getenv("EMA_FAST", "20"))
EMA_SLOW = int(os.getenv("EMA_SLOW", "50"))

MACD_FAST   = int(os.getenv("MACD_FAST", "12"))
MACD_SLOW   = int(os.getenv("MACD_SLOW", "26"))
MACD_SIGNAL = int(os.getenv("MACD_SIGNAL", "9"))

BB_PERIOD = int(os.getenv("BB_PERIOD", "20"))
BB_STD    = float(os.getenv("BB_STD", "2.0"))

MIN_SIGNAL_CONFLUENCE = int(os.getenv("MIN_SIGNAL_CONFLUENCE", "3"))

USE_TREND_FILTER = os.getenv("USE_TREND_FILTER", "true").lower() == "true"
DISABLE_VOLUME_FILTER = os.getenv("DISABLE_VOLUME_FILTER", "false").lower() == "true"
VOLUME_THRESHOLD_PCT = float(os.getenv("VOLUME_THRESHOLD_PCT", "0.5"))

# ── Telegram ──────────────────────────────────────
TELEGRAM_TOKEN   = os.getenv("TELEGRAM_TOKEN", "")
TELEGRAM_CHAT_ID = os.getenv("TELEGRAM_CHAT_ID", "")
TELEGRAM_ENABLED = os.getenv("TELEGRAM_ENABLED", "true").lower() == "true"

# ── Sentiment (Claude AI) ─────────────────────────
ANTHROPIC_API_KEY = os.getenv("ANTHROPIC_API_KEY", "")
CRYPTOPANIC_KEY   = os.getenv("CRYPTOPANIC_KEY", "")
SENTIMENT_ENABLED = os.getenv("SENTIMENT_ENABLED", "false").lower() == "true"

# ── Logging ───────────────────────────────────────
LOG_FILE  = os.getenv("LOG_FILE", "bot.log")
LOG_LEVEL = os.getenv("LOG_LEVEL", "INFO")
