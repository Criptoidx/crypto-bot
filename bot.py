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
    requests.post(url, data={'chat_id': CHAT_ID, 'text': message})

def get_prices():
    url = 'https://api.binance.com/api/v3/klines?symbol=BTCUSDT&interval=1m&limit=100'
    res = requests.get(url).json()
    df = pd.DataFrame(res, columns=[
        'timestamp', 'open', 'high', 'low', 'close', 'volume',
        'close_time', 'quote_asset_volume', 'number_of_trades',
        'taker_buy_base_asset_volume', 'taker_buy_quote_asset_volume', 'ignore'
    ])
    for col in ['open', 'high', 'low', 'close']:
        df[col] = df[col].astype(float)
    return df

def detect_three_white_soldiers(df):
    last = df.iloc[-4:]
    candles = last.iloc[1:]
    bullish = all([
        row['close'] > row['open'] and
        (row['close'] - row['open']) > (row['high'] - row['low']) * 0.5
        for _, row in candles.iterrows()
    ])
    return bullish and candles['close'].is_monotonic_increasing

def detect_three_black_crows(df):
    last = df.iloc[-4:]
    candles = last.iloc[1:]
    bearish = all([
        row['close'] < row['open'] and
        (row['open'] - row['close']) > (row['high'] - row['low']) * 0.5
        for _, row in candles.iterrows()
    ])
    return bearish and candles['close'].is_monotonic_decreasing

def get_last_command():
    res = requests.get(f'https://api.telegram.org/bot{TOKEN}/getUpdates').json()
    if res.get('result'):
        return res['result'][-1]['message'].get('text', '').lower()
    return ''

# Mensaje de inicio
send_message("🤖 Bot de señales CRYPTO IDX iniciado")

while True:
    try:
        cmd = get_last_command()
        if 'apagar' in cmd:
            bot_activo = False
            send_message("🛑 Bot desactivado")
        if 'encender' in cmd:
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

            # Indicadores
            rsi = RSIIndicator(close=close, window=14).rsi().iloc[-1]
            macd_obj = MACD(close=close)
            macd_val = macd_obj.macd().iloc[-1]
            macd_signal = macd_obj.macd_signal().iloc[-1]
            stoch_val = StochasticOscillator(high=high, low=low, close=close).stoch().iloc[-1]
            lower_band = BollingerBands(close=close).bollinger_lband().iloc[-1]
            upper_band = BollingerBands(close=close).bollinger_hband().iloc[-1]
            last_price = close.iloc[-1]

            # Señales flexibles
            signal = None
            if sum([rsi < 40, macd_val > macd_signal, stoch_val < 30]) >= 2:
                signal = "📈 Señal de COMPRA (CALL)"
            if sum([rsi > 60, macd_val < macd_signal, stoch_val > 70]) >= 2:
                signal = "📉 Señal de VENTA (PUT)"

            extras = []
            if detect_three_white_soldiers(df):
                extras.append("📈 Tres Soldados Blancos detectados (Patrón alcista)")
            if detect_three_black_crows(df):
                extras.append("📉 Tres Cuervos Negros detectados (Patrón bajista)")
            if (last_price < lower_band and rsi < 30) or (last_price > upper_band and rsi > 70):
                extras.append("💥 Retroceso en zona de rebote")
            if ((macd_val > macd_signal and macd_obj.macd().iloc[-2] < macd_obj.macd_signal().iloc[-2]) or
                (macd_val < macd_signal and macd_obj.macd().iloc[-2] > macd_obj.macd_signal().iloc[-2])):
                extras.append("🔁 Cambio de tendencia detectado")

            # Enviar solo si hay señal o patrón
            if signal or extras:
                now = datetime.datetime.now().strftime('%H:%M:%S')
                msg = f"""
⏰ {now}
📊 RSI: {round(rsi, 2)}
📉 MACD: {round(macd_val, 2)} | Signal: {round(macd_signal, 2)}
🔄 Estocástico: {round(stoch_val, 2)}
💵 Precio: {last_price}
📉 BBands: {round(lower_band, 2)} - {round(upper_band, 2)}

{signal if signal else ''}
{chr(10).join(extras)}
"""
                send_message(msg)

        time.sleep(600)

    except Exception as e:
        send_message(f"⚠️ Error: {e}")
        time.sleep(60)
        
