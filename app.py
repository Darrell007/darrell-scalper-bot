import os
import time
import requests
import pandas as pd
from flask import Flask, request

app = Flask(__name__)

# === Your Telegram Bot Token ===
BOT_TOKEN = "7646470360:AAH25-iQhphoP5RmZK7vmLoP4yxlqU2R140"
TELEGRAM_API_URL = f"https://api.telegram.org/bot{BOT_TOKEN}/sendMessage"

# === Binance API for price data ===
def get_binance_klines(symbol="BTCUSDT", interval="15m", limit=100):
    url = f"https://api.binance.com/api/v3/klines"
    params = {"symbol": symbol, "interval": interval, "limit": limit}
    response = requests.get(url)
    data = response.json()
    df = pd.DataFrame(data, columns=[
        "open_time", "open", "high", "low", "close", "volume",
        "close_time", "quote_asset_volume", "num_trades",
        "taker_buy_base_volume", "taker_buy_quote_volume", "ignore"
    ])
    df["close"] = df["close"].astype(float)
    return df

# === Technical Indicators ===
def calculate_indicators(df):
    df["EMA_9"] = df["close"].ewm(span=9, adjust=False).mean()
    df["EMA_21"] = df["close"].ewm(span=21, adjust=False).mean()
    df["RSI"] = compute_rsi(df["close"], 14)
    df["MACD"], df["Signal"] = compute_macd(df["close"])
    return df

def compute_rsi(series, period=14):
    delta = series.diff()
    gain = delta.where(delta > 0, 0).rolling(window=period).mean()
    loss = -delta.where(delta < 0, 0).rolling(window=period).mean()
    rs = gain / loss
    rsi = 100 - (100 / (1 + rs))
    return rsi

def compute_macd(series):
    ema12 = series.ewm(span=12, adjust=False).mean()
    ema26 = series.ewm(span=26, adjust=False).mean()
    macd = ema12 - ema26
    signal = macd.ewm(span=9, adjust=False).mean()
    return macd, signal

# === Signal Generator ===
def generate_signal(df):
    last = df.iloc[-1]
    ema_cross = "BUY" if last["EMA_9"] > last["EMA_21"] else "SELL"
    macd_signal = "BUY" if last["MACD"] > last["Signal"] else "SELL"
    rsi_status = "BUY" if last["RSI"] < 30 else "SELL" if last["RSI"] > 70 else "HOLD"

    votes = [ema_cross, macd_signal, rsi_status]
    decision = max(set(votes), key=votes.count)
    return decision, round(last["RSI"], 2)

# === Send Telegram Message ===
def send_telegram_message(chat_id, pair, signal, rsi_value):
    text = f"📉 *{pair} Signal*\n" \
           f"Strategy: EMA + RSI + MACD\n" \
           f"Signal: *{signal}*\n" \
           f"RSI: {rsi_value}"
    payload = {
        "chat_id": chat_id,
        "text": text,
        "parse_mode": "Markdown"
    }
    requests.post(TELEGRAM_API_URL, data=payload)

# === Webhook Root ===
@app.route("/", methods=["GET"])
def home():
    return "Bot is running."

# === Telegram Webhook Handler ===
@app.route("/webhook", methods=["POST"])
def webhook():
    data = request.get_json()
    if "message" in data and "text" in data["message"]:
        text = data["message"]["text"]
        chat_id = data["message"]["chat"]["id"]

        if text.lower() == "/signal":
            for symbol in ["BTCUSDT", "XAUUSDT"]:
                df = get_binance_klines(symbol)
                df = calculate_indicators(df)
                signal, rsi = generate_signal(df)
                send_telegram_message(chat_id, symbol, signal, rsi)
                time.sleep(1)

            return "Signals sent", 200

    return "No valid message received", 200

# === Flask Local Run ===
if __name__ == "__main__":
    port = int(os.environ.get("PORT", 5000))
    app.run(host="0.0.0.0", port=port, debug=True)

 

