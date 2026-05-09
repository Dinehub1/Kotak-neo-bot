import time
import logging
from datetime import datetime

import config
from broker import KotakBroker
from data_engine import DataEngine
from strategy import apply_swing_trend_strategy

logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

def on_signal(broker, current_position, signal_type):
    """
    Executes trades based on the signal and current position.
    Returns the new assumed position.
    """
    new_position = current_position
    qty = config.QUANTITY
    
    if signal_type == "BUY":
        if current_position < 0:
            logger.info("🔄 Closing Short Position...")
            success, _ = broker.place_order("B", qty)
            if success:
                new_position = 0
                time.sleep(1) # Brief pause before opening new position
            else:
                return new_position
                
        if new_position == 0:
            logger.info("📈 Opening Long Position...")
            success, _ = broker.place_order("B", qty)
            if success:
                new_position = qty
                
    elif signal_type == "SELL":
        if current_position > 0:
            logger.info("🔄 Closing Long Position...")
            success, _ = broker.place_order("S", qty)
            if success:
                new_position = 0
                time.sleep(1) # Brief pause before opening new position
            else:
                return new_position
                
        if new_position == 0:
            logger.info("📉 Opening Short Position...")
            success, _ = broker.place_order("S", qty)
            if success:
                new_position = -qty
                
    return new_position

def main():
    logger.info("🚀 Starting Native Python Trading Bot...")
    
    # Initialize broker and login
    broker = KotakBroker()
    try:
        broker.login()
    except Exception as e:
        logger.error(f"❌ Login failed: {e}")
        return

    # Sync position
    current_position = broker.get_current_position()
    if current_position is None:
        logger.warning("⚠️ Could not fetch actual position. Defaulting to 0.")
        current_position = 0
        
    logger.info(f"📌 Starting position for {config.TRADING_SYMBOL}: {current_position}")

    # Initialize data engine
    engine = DataEngine(symbol=config.TRADING_SYMBOL, timeframe_minutes=config.TIMEFRAME_MINUTES)
    
    last_processed_candle_time = None

    logger.info(f"⏳ Entering polling loop (Interval: {config.POLL_INTERVAL_SECONDS}s). Press Ctrl+C to stop.")
    
    try:
        while True:
            # 1. Fetch latest data
            df = engine.fetch_ohlc(days=3)
            
            if df is not None and not df.empty:
                # 2. Apply strategy
                # Strategy expects 'high', 'low', 'close' columns
                df = apply_swing_trend_strategy(df, no=3)
                
                # 3. Get the latest closed candle
                # Depending on Yahoo Finance, the absolute last row might be the currently forming candle.
                # To be safe, signals are usually acted upon when a candle closes.
                # We will check the last row for signals.
                latest_row = df.iloc[-1]
                latest_time = latest_row['datetime']
                
                # Check if we have a new signal on a candle we haven't processed yet
                if last_processed_candle_time is None or latest_time > last_processed_candle_time:
                    buy_sig = bool(latest_row.get('buy_signal', False))
                    sell_sig = bool(latest_row.get('sell_signal', False))
                    
                    if buy_sig or sell_sig:
                        logger.info(f"🔔 Signal detected at {latest_time} | Price: {latest_row['close']}")
                        
                        if buy_sig:
                            current_position = on_signal(broker, current_position, "BUY")
                        elif sell_sig:
                            current_position = on_signal(broker, current_position, "SELL")
                            
                        last_processed_candle_time = latest_time
            
            time.sleep(config.POLL_INTERVAL_SECONDS)
            
    except KeyboardInterrupt:
        logger.info("\n⏹️ Stopping bot...")
        try:
            broker.client.logout()
            logger.info("Logged out successfully.")
        except:
            pass

if __name__ == "__main__":
    main()
