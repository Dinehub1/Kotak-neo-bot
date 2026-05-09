import pandas as pd
import numpy as np

def apply_swing_trend_strategy(df: pd.DataFrame, no: int = 3) -> pd.DataFrame:
    """
    Applies the TradingView SMA 9/50/180 | EMA 20 | BUY/SELL strategy logic.
    Expects a DataFrame with 'high', 'low', 'close' columns (lowercase).
    """
    # 1. SMA and EMA calculations
    df['sma1'] = df['close'].rolling(window=9).mean()
    df['sma2'] = df['close'].rolling(window=50).mean()
    df['sma3'] = df['close'].rolling(window=180).mean()
    df['ema1'] = df['close'].ewm(span=20, adjust=False).mean()

    # 2. BUY/SELL Swing Logic
    # res = highest(high, no)
    df['res'] = df['high'].rolling(window=no).max()
    
    # sup = lowest(low, no)
    df['sup'] = df['low'].rolling(window=no).min()
    
    # avd = iff(close > res[1], 1, iff(close < sup[1], -1, 0))
    df['res_prev'] = df['res'].shift(1)
    df['sup_prev'] = df['sup'].shift(1)
    
    conditions = [
        df['close'] > df['res_prev'],
        df['close'] < df['sup_prev']
    ]
    choices = [1, -1]
    df['avd'] = np.select(conditions, choices, default=0)
    
    # avn = valuewhen(avd != 0, avd, 0)
    # We replace 0 with NaN, then forward-fill to get the last non-zero direction
    df['avn'] = df['avd'].replace(0, np.nan).ffill().fillna(0)
    
    # tsl = iff(avn == 1, sup, res)
    df['tsl'] = np.where(df['avn'] == 1, df['sup'], df['res'])
    
    # Buy = crossover(close, tsl)
    # Sell = crossunder(close, tsl)
    df['close_prev'] = df['close'].shift(1)
    df['tsl_prev'] = df['tsl'].shift(1)
    
    df['buy_signal'] = (df['close'] > df['tsl']) & (df['close_prev'] <= df['tsl_prev'])
    df['sell_signal'] = (df['close'] < df['tsl']) & (df['close_prev'] >= df['tsl_prev'])
    
    return df

if __name__ == "__main__":
    # Test with dummy data to verify it runs without errors
    data = {
        'high': [100, 102, 101, 105, 107, 106, 108, 104, 102, 100],
        'low': [98, 99, 97, 100, 104, 103, 105, 100, 98, 95],
        'close': [99, 101, 98, 104, 106, 105, 107, 101, 100, 96]
    }
    df = pd.DataFrame(data)
    df = apply_swing_trend_strategy(df, no=3)
    print(df[['close', 'res', 'sup', 'avd', 'avn', 'tsl', 'buy_signal', 'sell_signal']])
