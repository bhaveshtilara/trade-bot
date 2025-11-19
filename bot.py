
import logging
import sys
import os
import argparse
from dotenv import load_dotenv

from binance import Client
from binance.exceptions import BinanceAPIException, BinanceOrderException
from binance.enums import *

load_dotenv()
def setup_logging():
    logger = logging.getLogger('TradingBot')
    logger.setLevel(logging.DEBUG)

    file_handler = logging.FileHandler('trading_log.log')
    file_handler.setLevel(logging.DEBUG)

    console_handler = logging.StreamHandler(sys.stdout)
    console_handler.setLevel(logging.INFO)

    formatter = logging.Formatter(
        '%(asctime)s - %(name)s - %(levelname)s - %(message)s'
    )
    file_handler.setFormatter(formatter)
    console_handler.setFormatter(formatter)

    if not logger.handlers:
        logger.addHandler(file_handler)
        logger.addHandler(console_handler)
    
    return logger

LOGGER = setup_logging()


class BasicBot:
    def __init__(self, api_key, api_secret, testnet=True):
        self.logger = LOGGER
        self.logger.info("Initializing BasicBot...")
        
        try:
            self.client = Client(
                api_key=api_key, 
                api_secret=api_secret, 
                tld='com', 
                testnet=testnet 
            )
            self.client.futures_ping()
            self.logger.info("Binance Client initialized successfully and connected to Testnet.")
        except Exception as e:
            self.logger.error(f"Error initializing Binance Client: {e}")
            raise


    def place_order(self, symbol: str, side: str, order_type: str, quantity: float, price: float = None):
        """
        Places a trading order on the Binance Futures Testnet.
        """
        self.logger.info(
            f"Attempting order: Side={side}, Type={order_type}, Symbol={symbol}, Qty={quantity}"
            + (f", Price={price}" if price else "")
        )

        params = {
            'symbol': symbol,
            'side': side,
            'type': order_type,
            'quantity': quantity,
            'timeInForce': TIME_IN_FORCE_GTC,
        }
        
        if order_type == ORDER_TYPE_LIMIT:
            if price is None:
                self.logger.error("LIMIT order requires a 'price' parameter.")
                print("Order Failed: LIMIT order requires a target price.")
                return None
            params['price'] = price
        
        try:
            response = self.client.futures_create_order(**params)
            
            self.logger.info(f"Order placed successfully. Status: {response.get('status')}")
            self.logger.debug(f"API Response (Success): {response}")
            print("\nOrder Placed Successfully:")
            print(f"   Order ID: {response.get('orderId')}")
            print(f"   Status: {response.get('status')}")
            print(f"   Type: {response.get('type')}")
            
            return response

        except BinanceAPIException as e:
            self.logger.error(f"Binance API Error (Code {e.code}): {e.message}")
            print(f"\nOrder Failed (API Error): {e.message}")
            return None
            
        except BinanceOrderException as e: 
            self.logger.error(f"Binance Order Error (Code {e.code}): {e.message}")
            print(f"\n Order Failed (Order Error): {e.message}")
            return None
        


def validate_and_parse_args():
    """
    Sets up the command-line argument parser and validates the inputs.
    """
    parser = argparse.ArgumentParser(
        description="Simplified Binance Futures Trading Bot (Testnet)",
    )
    
    parser.add_argument('--symbol', type=str, required=True, help="Trading pair (e.g., BTCUSDT)")
    parser.add_argument('--side', type=str, choices=['BUY', 'SELL'], required=True, help="Order side (BUY or SELL)")
    parser.add_argument('--type', type=str, choices=['MARKET', 'LIMIT'], required=True, help="Order type (MARKET or LIMIT)")
    parser.add_argument('--qty', type=float, required=True, help="Quantity of asset to trade (e.g., 0.001)")
    
    parser.add_argument('--price', type=float, required=False, help="Price for LIMIT orders")
    
    args = parser.parse_args()
    
    if args.qty <= 0:
        LOGGER.error("Quantity must be greater than zero.")
        sys.exit(1)
        
    if args.type == 'LIMIT' and (args.price is None or args.price <= 0):
        LOGGER.error("LIMIT orders require a positive --price.")
        sys.exit(1)
            
    return args

def main():
    """Main function to run the bot."""
    args = validate_and_parse_args()
    
    API_KEY = os.getenv("API_KEY")
    API_SECRET = os.getenv("API_SECRET")
    
    if not API_KEY or not API_SECRET:
        LOGGER.error("API keys not loaded. Check your .env file.")
        print("Error: API_KEY or API_SECRET not found.")
        sys.exit(1)

    try:
        bot = BasicBot(api_key=API_KEY, api_secret=API_SECRET, testnet=True)
        
        bot.place_order(
            symbol=args.symbol.upper(),
            side=args.side.upper(),
            order_type=args.type.upper(),
            quantity=args.qty,
            price=args.price
        )
        
    except Exception as e:
        LOGGER.critical(f"Main execution failed: {e}")
        sys.exit(1)


if __name__ == "__main__":
    main()