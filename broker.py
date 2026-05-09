import os
import pyotp
import logging
from neo_api_client import NeoAPI
import config

logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

class KotakBroker:
    def __init__(self):
        self.client = NeoAPI(
            environment='prod',
            access_token=None,
            neo_fin_key=None,
            consumer_key=config.CONSUMER_KEY
        )

    def login(self):
        logger.info("Initializing Kotak Neo Login...")
        
        # Check if TOTP Secret is available for auto-login
        totp_secret = os.getenv("NEO_TOTP_SECRET")
        if totp_secret:
            logger.info("Auto-generating TOTP code...")
            totp = pyotp.TOTP(totp_secret)
            totp_code = totp.now()
        else:
            totp_code = input(f"\n🔑 Enter current 6-digit TOTP code for {config.UCC}: ").strip()
            
        logger.info("Starting TOTP Login...")
        self.client.totp_login(mobile_number=config.MOBILE_NUMBER, ucc=config.UCC, totp=totp_code)
        
        logger.info("Validating MPIN...")
        self.client.totp_validate(mpin=config.MPIN)
        
        logger.info("🎉 Successfully authenticated with Kotak Neo!")

    def place_order(self, transaction_type, qty, symbol=config.TRADING_SYMBOL, order_type=config.ORDER_TYPE, product=config.PRODUCT_TYPE, segment=config.EXCHANGE_SEGMENT):
        logger.info(f"📝 Placing {transaction_type} order for {qty} of {symbol}")
        try:
            resp = self.client.place_order(
                exchange_segment=segment,
                product=product,
                price="0", # Market order defaults to 0
                order_type=order_type,
                quantity=str(qty),
                validity="DAY",
                trading_symbol=symbol,
                transaction_type=transaction_type,
                amo="NO",
                disclosed_quantity="0",
                market_protection="0",
                pf="N",
                trigger_price="0"
            )
            logger.info(f"✅ Order placed successfully: {resp.get('nOrdNo') if isinstance(resp, dict) else resp}")
            return True, resp
        except Exception as e:
            logger.error(f"❌ Error placing order: {e}")
            return False, str(e)

    def get_current_position(self, symbol=config.TRADING_SYMBOL):
        """
        Fetches the current open quantity for a specific symbol from Kotak's position book.
        Returns 0 if flat, positive for long, negative for short.
        """
        try:
            # client.positions() returns a dict with 'data' being a list of positions
            positions_response = self.client.positions()
            
            if isinstance(positions_response, dict) and 'data' in positions_response:
                positions = positions_response['data']
                
                # Filter positions by symbol
                for pos in positions:
                    if pos.get('trdSym') == symbol:
                        # Depending on Kotak API, the net quantity might be under 'flQ' or 'netQty'
                        # It is typically 'flQ' or 'buyQty' - 'sellQty'. 
                        # We will compute based on typical Kotak Neo response:
                        buy_qty = int(pos.get('buyQty', 0))
                        sell_qty = int(pos.get('sellQty', 0))
                        net_qty = buy_qty - sell_qty
                        
                        logger.info(f"📊 Current position for {symbol}: {net_qty}")
                        return net_qty
                        
                logger.info(f"📊 No open positions found for {symbol}. Position is 0.")
                return 0
            else:
                logger.warning(f"⚠️ Could not parse positions data: {positions_response}")
                return 0
                
        except Exception as e:
            logger.error(f"❌ Error fetching positions: {e}")
            # If we fail, return None to indicate an error, rather than blindly assuming 0
            return None
