import yfinance as yf
import pandas as pd
import logging
from datetime import datetime

logger = logging.getLogger(__name__)

# Map the Kotak Trading Symbol to Yahoo Finance ticker
# Nifty Futures are derived from Nifty 50 index spot. 
# We use Spot (^NSEI) for strategy calculation.
SYMBOL_MAP = {
    "NIFTY-I": "^NSEI",
    "BANKNIFTY-I": "^NSEBANK",
}

class DataEngine:
    def __init__(self, symbol, timeframe_minutes):
        self.kotak_symbol = symbol
        self.yf_ticker = SYMBOL_MAP.get(symbol, "^NSEI")
        
        # yfinance interval format
        self.interval = f"{timeframe_minutes}m"
        
        logger.info(f"Initialized DataEngine for {self.kotak_symbol} mapping to {self.yf_ticker} ({self.interval})")

    def fetch_ohlc(self, days=5):
        """
        Fetches historical OHLC data from Yahoo Finance.
        Returns a Pandas DataFrame with lowercase columns: ['datetime', 'open', 'high', 'low', 'close', 'volume']
        """
        try:
            # We need enough days to calculate the 180 SMA on a 5-minute chart
            # 1 day = ~75 candles (5-min). 180 / 75 = 2.4 days minimum. We fetch 5 days to be safe.
            period = f"{days}d"
            
            ticker = yf.Ticker(self.yf_ticker)
            df = ticker.history(period=period, interval=self.interval)
            
            if df.empty:
                logger.error(f"❌ No data returned for {self.yf_ticker}")
                return None
                
            # Reset index to get Datetime as a column
            df = df.reset_index()
            
            # Rename columns to match what strategy.py expects
            df = df.rename(columns={
                'Datetime': 'datetime',
                'Open': 'open',
                'High': 'high',
                'Low': 'low',
                'Close': 'close',
                'Volume': 'volume'
            })
            
            # Convert timezone-aware datetime to timezone-naive local time or just leave it
            # Strategy doesn't strictly depend on time zone, but useful for logging
            
            return df
            
        except Exception as e:
            logger.error(f"❌ Error fetching data from Yahoo Finance: {e}")
            return None
