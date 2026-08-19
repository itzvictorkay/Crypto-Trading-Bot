import ccxt
import os
from dotenv import load_dotenv

load_dotenv()

exchange = ccxt.bybit({
    'apiKey': os.getenv("BYBIT_API_KEY"),
    'secret': os.getenv("BYBIT_API_SECRET"),
    'options': {
        'defaultType': 'linear',
    }
})

symbol = 'MNT/USDT:USDT'
category = 'linear'

try:
    print(f"Fetching positions for {symbol}...")
    positions = exchange.fetch_positions(symbols=[symbol], params={'category': category})
    for pos in positions:
        print(f"Found Position: Symbol={pos['symbol']}, Side={pos['side']}, Contracts={pos['contracts']}, Size={pos.get('size')}")
        if pos['symbol'] == symbol:
            print("MATCH found!")
except Exception as e:
    print(f"Error: {e}")
