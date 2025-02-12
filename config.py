# config.py
import os
import logging

# Set up basic logging configuration
# ログ設定の基本構成
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(name)s: %(message)s",
    datefmt="%Y-%m-%d %H:%M:%S"
)

# Feature columns for the ML model / MLモデル用の特徴カラム
feature_columns = ['open', 'high', 'low', 'close', 'volume', 'sma_25', 'bb_low', 'bb_medium', 'bb_high']

# API keys and tokens (loaded from environment variables)
# 環境変数からAPIキーとトークンを取得します。
API_KEY = os.environ.get("BINANCE_API_KEY", "")
API_SECRET = os.environ.get("BINANCE_API_SECRET", "")
TELEGRAM_TOKEN = os.environ.get("TELEGRAM_TOKEN", "")
TELEGRAM_CHAT_ID = os.environ.get("TELEGRAM_CHAT_ID", "")
OPENAI_API_KEY = os.environ.get("OPENAI_API_KEY", "")

# Operation configuration / 動作設定
SYMBOL = os.environ.get("SYMBOL", "BTC/USDT")
TIMEFRAME = os.environ.get("TIMEFRAME", "1h")
MAX_RETRIES = int(os.environ.get("MAX_RETRIES", "5"))

# Global state (if needed) / グローバルな状態（必要に応じて）
last_prediction = None
is_always_on_top = False
