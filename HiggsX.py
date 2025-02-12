# higgsx.py
import time
import threading
import asyncio
import logging
from plugins.technical_plugin import fetch_data, calculate_indicators, train_ml_model, predict_ml
from plugins.telegram_plugin import send_message, async_telegram_bot_loop
from config import SYMBOL, TIMEFRAME

logger = logging.getLogger(__name__)

# Global variable to store the last prediction (to avoid sending duplicate signals)
# 重複したシグナル送信を防ぐため、前回の予測を保持するグローバル変数
last_prediction = None

def market_monitor_loop():
    global last_prediction
    # Attempt to fetch data for initial model training
    # 初期モデルのトレーニングのため、データ取得を試みる
    data = None
    while data is None:
        data = fetch_data(SYMBOL, TIMEFRAME)
        if data is None:
            time.sleep(5)
    train_ml_model(data)
    
    # Main monitoring loop: executes every 15 seconds
    # 15秒ごとに実行されるメインの監視ループ
    while True:
        data = fetch_data(SYMBOL, TIMEFRAME)
        if data is None:
            time.sleep(15)
            continue
        indicators = calculate_indicators(data)
        ml_prediction = predict_ml(data)
        # If the prediction changes, send a signal via Telegram
        # 予測が変化した場合、Telegram経由でシグナルを送信する
        if ml_prediction != last_prediction:
            message = (
                f"📊 Current Price {SYMBOL}: ${indicators['price']:.2f}\n"
                f"RSI: {indicators['rsi']:.2f} | ADX: {indicators['adx']:.2f}\n"
                f"MACD: {indicators['macd']:.2f} (Signal: {indicators['macd_signal']:.2f})\n"
                f"SMA10: {indicators['sma_10']:.2f} | SMA25: {indicators['sma_25']:.2f} | SMA50: {indicators['sma_50']:.2f}\n"
                f"Volume: {indicators['volume_level']} (CMF: {indicators['cmf']:.2f})\n\n"
                f"Bollinger Bands:\n"
                f"Low - ${indicators['bb_low']:.2f}\n"
                f"Medium - ${indicators['bb_medium']:.2f}\n"
                f"High - ${indicators['bb_high']:.2f}\n\n"
                f"{ml_prediction}"
            )
            send_message(message)
            last_prediction = ml_prediction
        time.sleep(15)  # 15-second interval

if __name__ == "__main__":
    # Start the asynchronous Telegram bot loop in a background thread
    # 非同期のTelegramボットループをバックグラウンドスレッドで開始する
    def run_async_loop():
        asyncio.run(async_telegram_bot_loop())
    telegram_thread = threading.Thread(target=run_async_loop, daemon=True)
    telegram_thread.start()
    
    # Start the market monitoring loop
    # 市場監視ループを開始する
    market_monitor_loop()
