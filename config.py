import os
from dotenv import load_dotenv

# Load environment variables from .env
load_dotenv()

# ==========================================
# CREDENTIALS
# ==========================================
CONSUMER_KEY = os.getenv("NEO_CONSUMER_KEY")
MOBILE_NUMBER = os.getenv("NEO_MOBILE_NUMBER")
UCC = os.getenv("NEO_UCC")
MPIN = os.getenv("NEO_MPIN")

# ==========================================
# TRADING PARAMETERS
# ==========================================
TRADING_SYMBOL = "NIFTY-I"       # The instrument you want to trade
EXCHANGE_SEGMENT = "nse_fo"      # 'nse_cm' for cash, 'nse_fo' for futures
QUANTITY = 25                    # Quantity per trade
ORDER_TYPE = "MKT"               # Market order ('MKT') or Limit ('L')
PRODUCT_TYPE = "MIS"             # 'MIS' (Intraday) or 'NRML' (Delivery)

# ==========================================
# DATA & TIMEFRAME PARAMETERS
# ==========================================
TIMEFRAME_MINUTES = 5            # Candlestick timeframe in minutes
POLL_INTERVAL_SECONDS = 30       # How often to fetch data and check strategy

# Optional: Add Stop Loss / Target parameters if needed in the future
# STOP_LOSS_PTS = 20
# TAKE_PROFIT_PTS = 40
