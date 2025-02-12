# plugins/telegram_plugin.py
import os
import re
import time
import io
import requests
import logging
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
import mplfinance as mpf
from config import SYMBOL, TELEGRAM_TOKEN, TELEGRAM_CHAT_ID, OPENAI_API_KEY, TIMEFRAME
from pycoingecko import CoinGeckoAPI

logger = logging.getLogger(__name__)

# Mapping for extracting valid timeframes from messages
# メッセージから有効なタイムフレームを抽出するためのマッピング
TIMEFRAME_MAPPING = {
    "1m": "1m",
    "3m": "3m",
    "5m": "5m",
    "10m": "5m",  # Example adjustment / 例: 調整
    "15m": "15m",
    "30m": "30m",
    "1h": "1h",
    "2h": "2h",
    "4h": "4h",
    "6h": "6h",
    "8h": "8h",
    "12h": "12h",
    "1d": "1d",
    "3d": "3d",
    "1w": "1w",
    "1M": "1M"
}

def extract_timeframe(text):
    """
    Extracts a valid timeframe from the given text.
    
    テキストから有効なタイムフレームを抽出します。
    """
    pattern = r'\b(\d+m|\d+h|\d+d|\d+w|\d+M)\b'
    matches = re.findall(pattern, text.lower())
    for match in matches:
        if match in TIMEFRAME_MAPPING:
            return TIMEFRAME_MAPPING[match]
    return "1h"

def send_graphic(data, chat_id, timeframe_input="1h", chart_type="line"):
    """
    Generates a chart from the DataFrame 'data' and sends it to Telegram.
    'chart_type' should be either 'line' or 'candlestick'.
    
    DataFrame 'data' からチャートを生成し、Telegramに送信します。
    'chart_type' は 'line' または 'candlestick' で指定してください。
    """
    try:
        support = data['close'].min()
        resistance = data['close'].max()
        sma20 = data['close'].rolling(window=20).mean()
        sma50 = data['close'].rolling(window=50).mean()

        buf = io.BytesIO()
        caption = f"Chart of {SYMBOL} - {timeframe_input}"

        if chart_type.lower() == "candlestick":
            mc = mpf.make_marketcolors(up='g', down='r', inherit=True)
            s  = mpf.make_mpf_style(marketcolors=mc, gridstyle="--")
            ap0 = mpf.make_addplot(sma20, color='blue', width=1.0, linestyle='-')
            ap1 = mpf.make_addplot(sma50, color='orange', width=1.0, linestyle='-')
            sr_support = [support] * len(data)
            sr_resistance = [resistance] * len(data)
            ap2 = mpf.make_addplot(sr_support, color='green', linestyle='--', width=0.8)
            ap3 = mpf.make_addplot(sr_resistance, color='red', linestyle='--', width=0.8)
            fig, axlist = mpf.plot(
                data,
                type='candle',
                style=s,
                title=caption,
                volume=False,
                addplot=[ap0, ap1, ap2, ap3],
                returnfig=True
            )
            fig.suptitle(caption, y=0.95, fontsize=14)
            fig.savefig(buf, dpi=100, format='png')
            plt.close(fig)
        else:
            plt.figure(figsize=(10, 6))
            plt.plot(data.index, data['close'], label="Price", color='black')
            plt.plot(data.index, sma20, label="SMA20", color='blue')
            plt.plot(data.index, sma50, label="SMA50", color='orange')
            plt.axhline(support, color='green', linestyle='--', label="Support")
            plt.axhline(resistance, color='red', linestyle='--', label="Resistance")
            plt.title(caption, fontsize=14)
            plt.xlabel("Time")
            plt.ylabel("Price")
            plt.legend()
            plt.grid(True, linestyle="--", alpha=0.7)
            plt.savefig(buf, format="png")
            plt.close()
        buf.seek(0)
        url = f"https://api.telegram.org/bot{TELEGRAM_TOKEN}/sendPhoto"
        files = {'photo': buf}
        data_payload = {'chat_id': chat_id, 'caption': caption}
        response = requests.post(url, data=data_payload, files=files)
        if response.status_code != 200:
            logger.error(f"Error sending chart: {response.text}")
    except Exception as e:
        logger.error(f"Error in send_graphic: {e}")

def send_message(message, chat_id=None):
    """
    Sends a text message to Telegram.
    
    Telegramにテキストメッセージを送信します。
    """
    if chat_id is None:
        chat_id = TELEGRAM_CHAT_ID
    url = f"https://api.telegram.org/bot{TELEGRAM_TOKEN}/sendMessage"
    payload = {'chat_id': chat_id, 'text': message, 'parse_mode': 'Markdown'}
    try:
        response = requests.post(url, json=payload)
        if response.status_code != 200:
            logger.error(f"Error sending message: {response.text}")
    except Exception as e:
        logger.error(f"Error in send_message: {e}")

def get_updates():
    """
    Retrieves updates from the Telegram bot.
    
    Telegramボットからアップデートを取得します。
    """
    url = f"https://api.telegram.org/bot{TELEGRAM_TOKEN}/getUpdates"
    try:
        response = requests.get(url)
        if response.status_code == 200:
            updates = response.json().get("result", [])
            return updates
        else:
            logger.error(f"Error getting updates: {response.text}")
            return []
    except Exception as e:
        logger.error(f"Error in get_updates: {e}")
        return []

async def async_telegram_bot_loop():
    """
    Asynchronous main loop to listen for messages every 5 seconds.
    
    5秒ごとにメッセージを非同期で監視するメインループです。
    """
    import asyncio
    last_update_id = None
    while True:
        try:
            updates = get_updates()
            if updates:
                for update in updates:
                    update_id = update.get("update_id")
                    if last_update_id is None or update_id > last_update_id:
                        handle_telegram_message(update)
                        last_update_id = update_id
            await asyncio.sleep(5)
        except Exception as e:
            logger.error(f"Error in async_telegram_bot_loop: {e}")
            await asyncio.sleep(10)

def handle_telegram_message(update):
    """
    Processes the received message.
    If a chart request is detected, generates and sends the chart.
    Otherwise, generates a template response (e.g., by consulting OpenAI).
    
    受信したメッセージを処理します。
    チャートリクエストが検出された場合、チャートを生成して送信します。
    それ以外の場合、テンプレート応答を生成します（例としてOpenAIへの問い合わせ）。
    """
    from plugins.technical_plugin import fetch_data, calculate_indicators  # Dynamic import to avoid circular dependencies / 循環依存を回避するための動的インポート
    import openai
    openai.api_key = OPENAI_API_KEY

    message_obj = update.get("message", {})
    message_text = message_obj.get("text", "").strip()
    chat_id = message_obj.get("chat", {}).get("id")
    username = message_obj.get("from", {}).get("username", "User")
    lower_msg = message_text.lower()

    # If a chart request is detected, generate and send the chart.
    # チャートリクエストが検出された場合、チャートを生成して送信します。
    if any(phrase in lower_msg for phrase in ["chart", "grafico", "グラフ"]):
        timeframe = extract_timeframe(lower_msg)
        chart_type = "line"
        if any(keyword in lower_msg for keyword in ["candlestick", "vela", "ローソク足"]):
            chart_type = "candlestick"
        data = fetch_data(SYMBOL, TIMEFRAME)
        if data is not None:
            send_graphic(data, chat_id, timeframe, chart_type)
        return

    # Otherwise, generate a template response.
    # それ以外の場合、テンプレート応答を生成します。
    data = fetch_data(SYMBOL, TIMEFRAME)
    if data is None:
        return
    indicators = calculate_indicators(data)
    context = (
        f"Hello agent @{username}, this is Higgs X speaking. My mission is to monitor the market for {SYMBOL}.\n\n"
        f"Technical indicators (template):\n"
        f"- Price: ${indicators['price']:.2f}\n"
        f"- RSI: {indicators['rsi']:.2f}\n"
        f"- MACD: {indicators['macd']:.2f} (Signal: {indicators['macd_signal']:.2f})\n"
        f"- SMA10: {indicators['sma_10']:.2f}, SMA25: {indicators['sma_25']:.2f}, SMA50: {indicators['sma_50']:.2f}\n"
        f"- Volume: {indicators['volume_level']} (CMF: {indicators['cmf']:.2f})\n"
        f"- Bollinger Bands: Low ${indicators['bb_low']:.2f}, Medium ${indicators['bb_medium']:.2f}, High ${indicators['bb_high']:.2f}\n\n"
        f"Question: {message_text}"
    )
    try:
        response = openai.ChatCompletion.create(
            model="gpt-3.5-turbo",
            messages=[
                {"role": "system", "content": (
                    "You are Higgs X, the agent responsible for monitoring the market. Respond concisely and address the user as 'agent @username'."
                )},
                {"role": "user", "content": context}
            ],
            max_tokens=500,
            temperature=0.7
        )
        answer = response["choices"][0]["message"]["content"].strip()
    except Exception as e:
        answer = f"⚠️ Error processing request: {e}"
    send_message(answer, chat_id)
