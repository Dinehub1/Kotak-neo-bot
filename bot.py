import os
import time
import pandas as pd
from dotenv import load_dotenv
from neo_api_client import NeoAPI
from strategy import apply_swing_trend_strategy

# ==========================================
# BOT CONFIGURATION
# ==========================================
# Change these variables based on your preference
TRADING_SYMBOL = "NIFTY-I"       # The instrument you want to trade
EXCHANGE_SEGMENT = "nse_fo"      # e.g., 'nse_cm' for cash, 'nse_fo' for futures
QUANTITY = 25                    # Quantity per trade
ORDER_TYPE = "MKT"               # Market order ('MKT') or Limit ('L')
PRODUCT_TYPE = "MIS"             # 'MIS' (Intraday) or 'NRML' (Delivery)
TIMEFRAME_MINUTES = 5            # Interval for building candles (e.g., 5 min)
# ==========================================

load_dotenv()
CONSUMER_KEY = os.getenv("NEO_CONSUMER_KEY")
MOBILE_NUMBER = os.getenv("NEO_MOBILE_NUMBER")
UCC = os.getenv("NEO_UCC")
MPIN = os.getenv("NEO_MPIN")

# State management
current_position = 0  # 0: Flat, >0: Long, <0: Short
historical_data = []  # Will hold historical OHLC candles

def login():
    print("Initializing Kotak Neo Client...")
    client = NeoAPI(
        environment='prod',
        access_token=None,
        neo_fin_key=None,
        consumer_key=CONSUMER_KEY
    )
    
    totp_code = input(f"\n🔑 Enter current 6-digit TOTP code for {UCC}: ").strip()
    
    print("\nStarting TOTP Login...")
    client.totp_login(mobile_number=MOBILE_NUMBER, ucc=UCC, totp=totp_code)
    
    print("Validating MPIN...")
    client.totp_validate(mpin=MPIN)
    
    print("🎉 Successfully authenticated!")
    return client

def place_order(client, transaction_type, qty):
    print(f"📝 Placing {transaction_type} order for {qty} of {TRADING_SYMBOL}")
    try:
        # Note: Depending on whether you need a specific instrument token, you might
        # need to search for the scrip first.
        resp = client.place_order(
            exchange_segment=EXCHANGE_SEGMENT,
            product=PRODUCT_TYPE,
            price="0", # Market order
            order_type=ORDER_TYPE,
            quantity=str(qty),
            validity="DAY",
            trading_symbol=TRADING_SYMBOL,
            transaction_type=transaction_type,
            amo="NO",
            disclosed_quantity="0",
            market_protection="0",
            pf="N",
            trigger_price="0"
        )
        print(f"✅ Order Response: {resp}")
        return True
    except Exception as e:
        print(f"❌ Error placing order: {e}")
        return False

def on_signal(client, signal_type):
    global current_position
    
    if signal_type == "BUY":
        if current_position < 0:
            print("🔄 Closing Short Position...")
            place_order(client, "B", QUANTITY)
            current_position = 0
            
        if current_position == 0:
            print("📈 Opening Long Position...")
            place_order(client, "B", QUANTITY)
            current_position = QUANTITY
            
    elif signal_type == "SELL":
        if current_position > 0:
            print("🔄 Closing Long Position...")
            place_order(client, "S", QUANTITY)
            current_position = 0
            
        if current_position == 0:
            print("📉 Opening Short Position...")
            place_order(client, "S", QUANTITY)
            current_position = -QUANTITY

def on_message(message):
    """
    Callback for live websocket data. 
    Here you would aggregate tick data into candles based on TIMEFRAME_MINUTES.
    For demonstration, we print the incoming message.
    """
    # print(f"Live Data: {message}")
    pass

def on_error(error_message):
    print(f"WebSocket Error: {error_message}")

def main():
    if not all([CONSUMER_KEY, MOBILE_NUMBER, UCC, MPIN]):
        print("❌ Missing credentials in .env file")
        return
        
    client = login()
    
    # Optional: Setup Websocket
    client.on_message = on_message
    client.on_error = on_error
    
    # You would normally subscribe to your specific instrument token here:
    # client.subscribe(instrument_tokens=[{"instrument_token": "...", "exchange_segment": EXCHANGE_SEGMENT}])
    
    print("\n🚀 Bot is now running. Waiting for data and signals...")
    print("Press Ctrl+C to stop.")
    
    try:
        while True:
            # Main strategy loop
            # 1. Fetch latest data / build latest candle
            # df = get_latest_data(client)
            
            # 2. Apply strategy
            # df = apply_swing_trend_strategy(df)
            
            # 3. Check latest signal
            # latest_row = df.iloc[-1]
            # if latest_row['buy_signal']:
            #     on_signal(client, "BUY")
            # elif latest_row['sell_signal']:
            #     on_signal(client, "SELL")
                
            time.sleep(5) # Avoid spamming loop
            
    except KeyboardInterrupt:
        print("\n⏹️ Stopping bot and logging out...")
        client.logout()

if __name__ == "__main__":
    main()
