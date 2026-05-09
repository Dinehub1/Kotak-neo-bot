import json
import pandas as pd
from datetime import datetime
from strategy import apply_swing_trend_strategy

# Read OHLCV from MCP tool
with open('/tmp/ohlcv.json', 'r') as f:
    data = json.load(f)

bars = data.get('bars', [])
if not bars:
    print("No bars found in data.")
    exit(1)

# Convert to DataFrame
df = pd.DataFrame(bars)
# Convert JS timestamp (seconds) to datetime
df['datetime'] = pd.to_datetime(df['time'], unit='s')

# Ensure we have required columns for strategy
# The MCP outputs: time, open, high, low, close, volume
df = apply_swing_trend_strategy(df, no=3)

# Filter for sell signals
sell_calls = df[df['sell_signal'] == True]

print(f"\n--- LAST {min(10, len(sell_calls))} SELL CALLS ON {data.get('symbol', 'NIFTY')} ---")
for idx, row in sell_calls.tail(10).iterrows():
    print(f"Time: {row['datetime']} | Price: {row['close']} | TSL: {row['tsl']}")

buy_calls = df[df['buy_signal'] == True]
print(f"\n--- LAST {min(10, len(buy_calls))} BUY CALLS ON {data.get('symbol', 'NIFTY')} ---")
for idx, row in buy_calls.tail(10).iterrows():
    print(f"Time: {row['datetime']} | Price: {row['close']} | TSL: {row['tsl']}")
