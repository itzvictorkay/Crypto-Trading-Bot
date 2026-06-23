import ccxt
import os
from dotenv import load_dotenv

load_dotenv()

def test_fetch_positions():
    api_key = os.getenv("BYBIT_API_KEY")
    api_secret = os.getenv("BYBIT_API_SECRET")
    
    exchange = ccxt.bybit({
        'apiKey': api_key,
        'secret': api_secret,
        'options': {
            'defaultType': 'swap',
        }
    })
    
    # Test linear
    try:
        print("Testing linear...")
        pos = exchange.fetch_positions(symbols=["BTC/USDT:USDT"], params={'category': 'linear'})
        print(f"Success! Found {len(pos)} positions.")
    except Exception as e:
        print(f"Linear failed: {e}")

    # Test inverse
    try:
        print("\nTesting inverse...")
        # BTCUSD is usually the inverse perpetual
        pos = exchange.fetch_positions(symbols=["BTC/USD:BTC"], params={'category': 'inverse'})
        print(f"Success! Found {len(pos)} positions.")
    except Exception as e:
        print(f"Inverse failed: {e}")

if __name__ == "__main__":
    test_fetch_positions()
