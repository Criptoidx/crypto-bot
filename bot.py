import requests
import pandas as pd
import numpy as np
import time
import datetime
from ta.momentum import RSIIndicator, StochasticOscillator
from ta.trend import MACD
from ta.volatility import BollingerBands

TOKEN = '8046400418:AAG-5JhTeSNaRJ_ll6annp9z6qn1F9oE9SY'
CHAT_ID = '7960707136'
bot_activo = True

def send_message(message):
    url = f'https://api.telegram.org/bot{TOKEN}/sendMessage'
    payload = {'chat_id': CHAT_ID, 'text': message}
    requests.post(url, data=payload)

def get_prices():
    url = 'https://api.binance.com/api/v3/klines?symbol=BTCUSDT&interval=1m&limit=100'
    res = requests.get(url).json()
    df = pd.DataFrame(res, columns=[
        'timestamp', 'open', 'high', 'low', 'close', 'volume',
        'close_time', 'quote_asset_volume', 'number_of_trades',
        'taker_buy_base_asset_volume', 'taker_buy_quote_asset_volume', 'ignore'
    ])
    df['open'] = df['open'].astype(float)
    df['close'] = df['close'].astype(float)
    df['high'] = df['high'].astype(float)
    df['low'] = df['low'].astype(float)
    return df

def detect_three_white_soldiers(df):
    last = df.iloc[-4:]
    candles = last.iloc[1:]
    bullish = all([
        row['close'] > row['open'] and
        (row['close'] - row['open']) > (row['high'] - row['low']) * 0.5
        for _, row in candles.iterrows()
    ])
    increasing = candles['close'].is_monotonic_increasing
    return bullish and increasing

def detect_three_black_crows(df):
    last = df.iloc[-4:]
    candles = last.iloc[1:]
    bearish = all([
        row['close'] < row['open'] and
        (row['open'] - row['close']) > (row['high'] - row['low']) * 0.5
        for _, row in candles.iterrows()
    ])
    decreasing = candles['close'].is_monotonic_decreasing
    return bearish and decreasing

def get_last_command():
    url = f'https://api.telegram.org/bot{TOKEN}/getUpdates'
    res = requests.get(url).json()
    messages = res['result']
    if messages:
        last_msg = messages[-1]
        return last_msg['message'].get('text', '').lower()
    return ''

send_message("🤖 Bot de señales CRYPTO IDX activado...")

while True:
    try:
        cmd = get_last_command()
        if 'apagar' in cmd:
            bot_activo = False
            send_message("🛑 Bot desactivado")
        elif 'encender' in cmd:
            bot_activo = True
            send_message("✅ Bot activado")

        if bot_activo:
            df = get_prices()

            if len(df) < 20:
                time.sleep(60)
                continue

            close = df['close']
            high = df['high']
            low = df['low']

            rsi = RSIIndicator(close=close, window=14).rsi().iloc[-1]
            macd_obj = MACD(close=close)
            macd_val = macd_obj.macd().iloc[-1]
            macd_signal = macd_obj.macd_signal().iloc[-1]
            stoch = StochasticOscillator(high=high, low=low, close=close)
            stoch_val = stoch.stoch().iloc[-1]

            boll = BollingerBands(close=close)
            lower_band = boll.bollinger_lband().iloc[-1]
            upper_band = boll.bollinger_hband().iloc[-1]
            last_price = close.iloc[-1]

            signal = None
            call_conditions = [rsi < 40, macd_val > macd_signal, stoch_val < 30]
            put_conditions = [rsi > 60, macd_val < macd_signal, stoch_val > 70]
            if sum(call_conditions) >= 2:
                signal = "📈 Señal de COMPRA (CALL)"
            elif sum(put_conditions) >= 2:
                signal = "📉 Señal de VENTA (PUT)"

            extras = []
            if len(df) >= 4:
                if detect_three_white_soldiers(df):
                    extras.append("📈 Tres Soldados Blancos detectados (Patrón alcista)")
                if detect_three_black_crows(df):
                    extras.append("📉 Tres Cuervos Negros detectados (Patrón bajista)")

            if (last_price < lower_band and rsi < 30) or (last_price > upper_band and rsi > 70):
                ext
  
