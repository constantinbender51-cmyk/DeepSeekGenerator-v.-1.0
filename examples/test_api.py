#!/usr/bin/env python3
"""
Example usage of Kraken Futures API
"""

import os
from dotenv import load_dotenv
from kraken_api import KrakenFuturesApi
from kraken_api.order_types import create_limit_order

# Load environment variables
load_dotenv()

def main():
    # Get API credentials from environment variables
    api_key = os.getenv('KRAKEN_API_KEY')
    api_secret = os.getenv('KRAKEN_API_SECRET')
    
    if not api_key or not api_secret:
        print("Please set KRAKEN_API_KEY and KRAKEN_API_SECRET environment variables")
        return
    
    # Initialize API client
    api = KrakenFuturesApi(api_key, api_secret)
    
    try:
        print("--- Testing Public GET Request (get_tickers) ---")
        tickers = api.get_tickers()
        print(f"Success! Found {len(tickers.get('tickers', []))} tickers")
        
        print("\n--- Testing Private GET Request (get_accounts) ---")
        accounts = api.get_accounts()
        print("Account information:", accounts)
        
        print("\n--- Testing Order Creation ---")
        # Create a limit order (will use far from market price to avoid execution)
        order_params = create_limit_order(
            symbol='pi_xbtusd',  # BTCUSD perpetual
            side='buy',
            size=0.001,  # Small size
            price=1000.00  # Far from market price to avoid execution
        )
        
        print("Order parameters:", order_params)
        
        # Uncomment to actually send order (be careful!)
        # print("\n--- Sending Test Order ---")
        # order_result = api.send_order(order_params)
        # print("Order result:", order_result)
        
        # if order_result.get('sendStatus', {}).get('order_id'):
        #     order_id = order_result['sendStatus']['order_id']
        #     print(f"\n--- Canceling Order {order_id} ---")
        #     cancel_result = api.cancel_order(order_id)
        #     print("Cancel result:", cancel_result)
        
    except Exception as e:
        print(f"Error: {e}")

if __name__ == "__main__":
    main()
