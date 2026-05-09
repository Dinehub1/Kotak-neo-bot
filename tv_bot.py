import os
import json
import subprocess
import time
from dotenv import load_dotenv
from neo_api_client import NeoAPI

# ==========================================
# BOT CONFIGURATION
# ==========================================
TRADING_SYMBOL = "NIFTY-I"       # The instrument you want to trade
EXCHANGE_SEGMENT = "nse_fo"      # 'nse_cm' for cash, 'nse_fo' for futures
QUANTITY = 25                    # Quantity per trade
ORDER_TYPE = "MKT"               # Market order ('MKT') or Limit ('L')
PRODUCT_TYPE = "MIS"             # 'MIS' (Intraday) or 'NRML' (Delivery)
INDICATOR_NAME = "SMA 9/50/180 | EMA 20 | BUY/SELL" # Must match TV exactly
# ==========================================

load_dotenv()
CONSUMER_KEY = os.getenv("NEO_CONSUMER_KEY")
MOBILE_NUMBER = os.getenv("NEO_MOBILE_NUMBER")
UCC = os.getenv("NEO_UCC")
MPIN = os.getenv("NEO_MPIN")

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
    client.totp_validate(mpin=MPIN)
    print("🎉 Successfully authenticated with Kotak Neo!\n")
    return client

def place_order(client, transaction_type, qty):
    print(f"📝 Placing {transaction_type} order for {qty} of {TRADING_SYMBOL}")
    try:
        resp = client.place_order(
            exchange_segment=EXCHANGE_SEGMENT,
            product=PRODUCT_TYPE,
            price="0", 
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
        print(f"✅ Order Response: {resp}\n")
        return True
    except Exception as e:
        print(f"❌ Error placing order: {e}\n")
        return False

def start_tv_stream():
    # Path to your TradingView MCP CLI
    cli_path = "/Users/mac/Documents/tarding view MCP new /tradingview-mcp/src/cli/index.js"
    cmd = ['node', cli_path, 'stream', 'values']
    
    print(f"Starting TradingView stream: {' '.join(cmd)}")
    process = subprocess.Popen(
        cmd, 
        stdout=subprocess.PIPE, 
        stderr=subprocess.STDOUT, 
        text=True,
        bufsize=1 # Line buffered
    )
    return process

def main():
    if not all([CONSUMER_KEY, MOBILE_NUMBER, UCC, MPIN]):
        print("❌ Missing Kotak credentials in .env file")
        return
        
    client = login()
    process = start_tv_stream()
    
    current_position = 0  # 0=Flat, >0=Long, <0=Short
    last_print_time = 0
    
    print("\n🚀 Bot is now listening to TradingView Desktop...")
    print("Make sure TradingView is open, in focus, and your chart has the indicator applied.")
    print("Press Ctrl+C to stop.\n")
    
    try:
        for line in iter(process.stdout.readline, ''):
            line = line.strip()
            if not line:
                continue
                
            try:
                # Try to parse the line as JSON
                data = json.loads(line)
                
                # Check if this data is from our specific indicator
                if data.get("study") == INDICATOR_NAME:
                    values = data.get("values", {})
                    
                    # Check if values is empty, which means Data Window is closed
                    if not values:
                        print(f"[{time.strftime('%H:%M:%S')}] ⚠️  Indicator found, but no values! Please open the 'Data Window' on the right sidebar of TradingView.")
                        last_print_time = current_time
                        continue
                    
                    # Print values every 10 seconds just to show it's alive
                    current_time = time.time()
                    if current_time - last_print_time > 10:
                        print(f"[{time.strftime('%H:%M:%S')}] Live Indicator Values: {values}")
                        last_print_time = current_time
                    
                    # Detect Buy/Sell signals. 
                    # plotshape(title="Buy") usually outputs a 'Buy' key in the Data Window when true.
                    # We check if it exists and is non-zero/true
                    buy_signal = values.get("Buy", 0)
                    sell_signal = values.get("Sell", 0)
                    
                    # Some data windows output NaN when false, or 1 when true
                    is_buy = buy_signal == 1 or buy_signal is True
                    is_sell = sell_signal == 1 or sell_signal is True
                    
                    if is_buy:
                        print(f"\n[{time.strftime('%H:%M:%S')}] 📈 BUY SIGNAL DETECTED FROM TRADINGVIEW!")
                        if current_position <= 0:
                            if current_position < 0:
                                print("🔄 Reversing: Closing Short Position...")
                                place_order(client, "B", QUANTITY)
                            print("📈 Opening Long Position...")
                            place_order(client, "B", QUANTITY)
                            current_position = QUANTITY
                            time.sleep(2) # Brief pause to prevent duplicate immediate orders
                            
                    elif is_sell:
                        print(f"\n[{time.strftime('%H:%M:%S')}] 📉 SELL SIGNAL DETECTED FROM TRADINGVIEW!")
                        if current_position >= 0:
                            if current_position > 0:
                                print("🔄 Reversing: Closing Long Position...")
                                place_order(client, "S", QUANTITY)
                            print("📉 Opening Short Position...")
                            place_order(client, "S", QUANTITY)
                            current_position = -QUANTITY
                            time.sleep(2) # Brief pause to prevent duplicate immediate orders
                            
            except json.JSONDecodeError:
                # If it's not JSON, it might be a status message or error from the MCP
                if "error" in line.lower() or "started" in line.lower() or "⚠" in line:
                    print(f"TV MCP Log: {line}")
                
    except KeyboardInterrupt:
        print("\n⏹️ Stopping bot and logging out...")
        process.terminate()
        client.logout()

if __name__ == "__main__":
    main()
