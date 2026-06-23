import ccxt

print("CCXT version:", ccxt.__version__)

# Let's test with no keys first
print("\n--- Test 1: fetch_ohlcv without API keys ---")
exchange = ccxt.bybit({
    'enableRateLimit': True,
    'options': {
        'defaultType': 'swap',
    }
})
try:
    ohlcv = exchange.fetch_ohlcv("BTC/USDT:USDT", timeframe='15m', limit=5)
    print("Success without keys! Fetched", len(ohlcv), "candles.")
except Exception as e:
    print("Failed without keys:", e)

# Let's test with the user's keys from .env but on Testnet
print("\n--- Test 2: fetch_ohlcv with keys on TESTNET ---")
exchange_testnet = ccxt.bybit({
    'apiKey': 'nIfNWhJ07fIsJTuPML',
    'secret': '58AEZ3NiO6YDimVyR1MAhnSYaRpwMLWAO8PC',
    'enableRateLimit': True,
    'options': {
        'defaultType': 'swap',
    }
})
exchange_testnet.set_sandbox_mode(True)
try:
    ohlcv = exchange_testnet.fetch_ohlcv("BTC/USDT:USDT", timeframe='15m', limit=5)
    print("Success on testnet! Fetched", len(ohlcv), "candles.")
except Exception as e:
    print("Failed on testnet:", e)

# Let's test with the user's keys on Live
print("\n--- Test 3: fetch_ohlcv with keys on LIVE ---")
exchange_live = ccxt.bybit({
    'apiKey': 'nIfNWhJ07fIsJTuPML',
    'secret': '58AEZ3NiO6YDimVyR1MAhnSYaRpwMLWAO8PC',
    'enableRateLimit': True,
    'options': {
        'defaultType': 'swap',
    }
})
try:
    ohlcv = exchange_live.fetch_ohlcv("BTC/USDT:USDT", timeframe='15m', limit=5)
    print("Success on live! Fetched", len(ohlcv), "candles.")
except Exception as e:
    print("Failed on live:", e)
