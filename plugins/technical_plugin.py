# plugins/technical_plugin.py
import time
import pandas as pd
import logging
from pycoingecko import CoinGeckoAPI
from ta.momentum import RSIIndicator
from ta.trend import MACD, SMAIndicator, ADXIndicator
from ta.volume import ChaikinMoneyFlowIndicator
from ta.volatility import BollingerBands, AverageTrueRange
# Note: The ML section is provided as a template.
# 例: MLの部分はテンプレートとして提供されています。

from config import SYMBOL, TIMEFRAME, MAX_RETRIES, feature_columns

logger = logging.getLogger(__name__)

# Use CoinGecko to fetch market data / コインゲッコーを利用して市場データを取得する
cg = CoinGeckoAPI()

def fetch_data(symbol=SYMBOL, timeframe=TIMEFRAME, limit=100):
    """
    Fetches OHLCV data using CoinGecko.
    For 'BTC/USDT', assumes coin id 'bitcoin' and obtains 1 day of data.
    Merges approximate volume data.
    
    コインゲッコーを利用してOHLCVデータを取得します。
    'BTC/USDT'の場合、コインID 'bitcoin' を仮定し、1日分のデータを取得します。
    ボリュームデータも統合されます。
    """
    coin_id = 'bitcoin' if symbol.upper().startswith('BTC') else 'bitcoin'
    vs_currency = 'usd'
    days = 1  # 1 day of data / 1日分のデータ
    try:
        ohlc_data = cg.get_coin_ohlc_by_id(id=coin_id, vs_currency=vs_currency, days=days)
        df = pd.DataFrame(ohlc_data, columns=['timestamp', 'open', 'high', 'low', 'close'])
        df['timestamp'] = pd.to_datetime(df['timestamp'], unit='ms')
        market_chart = cg.get_coin_market_chart_by_id(id=coin_id, vs_currency=vs_currency, days=days)
        vol_df = pd.DataFrame(market_chart.get('total_volumes', []), columns=['timestamp', 'volume'])
        vol_df['timestamp'] = pd.to_datetime(vol_df['timestamp'], unit='ms')
        df = pd.merge_asof(df.sort_values('timestamp'), vol_df.sort_values('timestamp'), on='timestamp')
        logger.info("Data fetched successfully from CoinGecko.")
        return df
    except Exception as e:
        logger.error(f"[Error in fetch_data] {e}. Retrying...")
        time.sleep(1)
        return None

def calculate_indicators(data):
    """
    Calculates technical indicators (RSI, MACD, SMA, Bollinger Bands, etc.) from the data.
    This is a template for indicator calculation—feel free to extend it.
    
    データからテクニカル指標（RSI、MACD、SMA、ボリンジャーバンドなど）を計算します。
    これはテンプレートですので、必要に応じて拡張してください。
    """
    close = data['close']
    high = data['high']
    low = data['low']
    volume = data['volume']

    cmf = ChaikinMoneyFlowIndicator(high, low, close, volume).chaikin_money_flow().iloc[-1]
    volume_level = "High" if cmf > 0.1 else "Low" if cmf < -0.1 else "Moderate"

    sma_10 = SMAIndicator(close, window=10).sma_indicator().iloc[-1]
    sma_25 = SMAIndicator(close, window=25).sma_indicator().iloc[-1]
    sma_50 = SMAIndicator(close, window=50).sma_indicator().iloc[-1]

    macd_indicator = MACD(close)
    macd = macd_indicator.macd().iloc[-1]
    macd_signal = macd_indicator.macd_signal().iloc[-1]

    rsi = RSIIndicator(close, window=14).rsi().iloc[-1]
    adx = ADXIndicator(high, low, close).adx().iloc[-1]

    bb_indicator = BollingerBands(close, window=20, window_dev=2)
    bb_low = bb_indicator.bollinger_lband().iloc[-1]
    bb_medium = bb_indicator.bollinger_mavg().iloc[-1]
    bb_high = bb_indicator.bollinger_hband().iloc[-1]

    # TEMPLATE: Insert additional or alternative indicator calculations here.
    # テンプレート: ここに追加または代替の指標計算を記述できます。

    indicators = {
        'price': close.iloc[-1],
        'rsi': rsi,
        'adx': adx,
        'macd': macd,
        'macd_signal': macd_signal,
        'sma_10': sma_10,
        'sma_25': sma_25,
        'sma_50': sma_50,
        'cmf': cmf,
        'volume_level': volume_level,
        'bb_low': bb_low,
        'bb_medium': bb_medium,
        'bb_high': bb_high,
        'prev_close': close.iloc[-2] if len(close) > 1 else None
    }
    return indicators

# TEMPLATE FOR ML MODEL TRAINING AND PREDICTION:
# The following functions are provided as a template.
# They do not include a complete trading strategy.
# 完全なトレーディング戦略は含まれていません。

def add_extra_features(data):
    """
    Adds extra features (SMA25, Bollinger Bands, ATR) to the DataFrame.
    
    DataFrameに追加の特徴（SMA25、ボリンジャーバンド、ATR）を追加します。
    """
    data = data.copy()
    data['sma_25'] = SMAIndicator(data['close'], window=25).sma_indicator()
    bb = BollingerBands(data['close'], window=20, window_dev=2)
    data['bb_low'] = bb.bollinger_lband()
    data['bb_medium'] = bb.bollinger_mavg()
    data['bb_high'] = bb.bollinger_hband()
    atr = AverageTrueRange(high=data['high'], low=data['low'], close=data['close'], window=14)
    data['atr'] = atr.average_true_range()
    return data

def train_ml_model(data):
    """
    Trains an ML model using historical data.
    This template function provides an example of model training.
    The full proprietary trading strategy is not disclosed here.
    
    過去のデータを使用してMLモデルをトレーニングします。
    これはテンプレート関数であり、完全な戦略は公開していません。
    """
    data = add_extra_features(data)
    features = data[feature_columns].pct_change().dropna()
    target = (features['close'] > 0).astype(int)
    # TEMPLATE: Insert your model training code here.
    # 例: ここにモデルのトレーニングコードを挿入してください。
    print("Template: Training model... (insert your strategy here)")
    return

# Global variable for smoothing predictions (template)
LAST_STABLE_PREDICTION = None

def predict_ml(data):
    """
    Predicts market direction using an ML model.
    If the probability is between 0.45 and 0.55, the last prediction is retained.
    This template function is provided for illustration; replace with your own prediction strategy.
    
    MLモデルを使用して市場の方向性を予測します。
    確率が0.45～0.55の場合、前回の予測を保持します。
    これはテンプレート関数です。独自の予測戦略に置き換えてください。
    """
    global LAST_STABLE_PREDICTION
    data = add_extra_features(data)
    features = data[feature_columns].pct_change().dropna().iloc[-1:][feature_columns]
    # TEMPLATE: Replace with your model's prediction method.
    # 例: ここに予測手法を挿入してください。
    print("Template: Predicting market direction... (insert your strategy here)")
    prob = [0.3, 0.7]  # Example probabilities for illustration / 例としての確率
    if 0.45 < prob[1] < 0.55 and LAST_STABLE_PREDICTION is not None:
        prediction = LAST_STABLE_PREDICTION
    else:
        prediction = 1 if prob[1] >= 0.55 else 0
        LAST_STABLE_PREDICTION = prediction
    return '👁‍🗨Market Direction: Expected Up 📈' if prediction == 1 else '👁‍🗨Market Direction: Expected Down 📉'
