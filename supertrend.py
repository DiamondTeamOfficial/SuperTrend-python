import ccxt
from datetime import datetime
import pandas as pd
import time
import ta
import matplotlib.pyplot as plt
def calculate_supertrend(df, period=11, multiplier=2.8, change_atr_method=True):
    hl2 = (df['high'] + df['low']) / 2
    tr = pd.concat([
        df['high'] - df['low'],
        abs(df['high'] - df['close'].shift(1)),
        abs(df['low'] - df['close'].shift(1))
    ], axis=1).max(axis=1)
    if change_atr_method:
        df['tr'] = tr
        atr = ta.volatility.average_true_range(df['high'], df['low'], df['close'], window=period)
    else:
        atr = tr.rolling(window=period).mean()
    upperband = hl2 - (multiplier * atr)
    lowerband = hl2 + (multiplier * atr)
    final_upperband = upperband.copy()
    final_lowerband = lowerband.copy()
    trend = [1]
    signals = [None]
    for i in range(1, len(df)):
        if df['close'][i - 1] > final_upperband[i - 1]:
            final_upperband[i] = max(upperband[i], final_upperband[i - 1])
        else:
            final_upperband[i] = upperband[i]
        if df['close'][i - 1] < final_lowerband[i - 1]:
            final_lowerband[i] = min(lowerband[i], final_lowerband[i - 1])
        else:
            final_lowerband[i] = lowerband[i]
        if trend[i - 1] == -1 and df['close'][i] > final_lowerband[i - 1]:
            trend.append(1)
            signals.append("BUY")
        elif trend[i - 1] == 1 and df['close'][i] < final_upperband[i - 1]:
            trend.append(-1)
            signals.append("SELL")
        else:
            trend.append(trend[i - 1])
            signals.append(None)
    df['supertrend'] = [final_lowerband[i] if trend[i] == 1 else final_upperband[i] for i in range(len(df))]
    df['trend'] = trend
    df['signal'] = signals
    return df
exchange = ccxt.huobi()
symbol = 'BTC/USDT'
timeframe = '15m'
limit = 500
last_checked_candle_time = None
while True:
    try:
        ohlcv = exchange.fetch_ohlcv(symbol, timeframe=timeframe, limit=limit)
        df = pd.DataFrame(ohlcv, columns=['timestamp', 'open', 'high', 'low', 'close', 'volume'])
        df['timestamp'] = pd.to_datetime(df['timestamp'], unit='ms')
        current_candle_time = df.iloc[-1]['timestamp']
        if current_candle_time != last_checked_candle_time:
            last_checked_candle_time = current_candle_time
            df = calculate_supertrend(df, period=11, multiplier=2.8, change_atr_method=True)
            signal_row = df.iloc[-3]
            is_prev_candle_buy = signal_row['signal'] == 'BUY'
            is_prev_candle_sell = signal_row['signal'] == 'SELL'
            print("-----------------------------")
            print(f"Time: {signal_row['timestamp']}")
            print(f"BTC Price (Close): {signal_row['close']} USDT")
            print(f"Supertrend: {signal_row['supertrend']:.2f} | Trend: {'UP' if signal_row['trend'] == 1 else 'DOWN'}")
            if is_prev_candle_buy:
                print("BUY")
            elif is_prev_candle_sell:
                print("SELL")
            else:
                print("No signal")
            recent_signals = df[df['signal'].notna()][['timestamp', 'signal', 'close']].tail(2)
            print("\nLast 2 Supertrend Signals:")
            print(recent_signals.to_string(index=False))
            plt.figure(figsize=(16, 8))
            plt.plot(df['timestamp'], df['close'], label='Close Price', color='blue')
            plt.plot(df['timestamp'], df['supertrend'], label='Supertrend', color='green')
            buy_signals = df[df['signal'] == 'BUY']
            sell_signals = df[df['signal'] == 'SELL']
            plt.scatter(buy_signals['timestamp'], buy_signals['close'], label='BUY Signal', color='lime', marker='^', s=100)
            plt.scatter(sell_signals['timestamp'], sell_signals['close'], label='SELL Signal', color='red', marker='v', s=100)
            plt.title('BTC/USDT 15m Supertrend Chart')
            plt.xlabel('Time')
            plt.ylabel('Price (USDT)')
            plt.legend()
            plt.xticks(rotation=45)
            plt.grid(True)
            plt.tight_layout()
            plt.show()
        time.sleep(60)
    except Exception as e:
        print("Error fetching data or calculating:", e)
        time.sleep(60)