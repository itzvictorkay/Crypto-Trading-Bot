"""
data/fetcher.py
---------------
Fetches OHLCV market data from Bybit via ccxt.
Supports both testnet and live environments.
"""

import ccxt
import pandas as pd
import logging

logger = logging.getLogger(__name__)


class DataFetcher:
    def __init__(self, api_key: str, api_secret: str, use_testnet: bool = True, market_type: str = 'spot'):
        self.exchange = ccxt.bybit({
            'apiKey': api_key,
            'secret': api_secret,
            'enableRateLimit': True,
            'options': {
                'defaultType': market_type,
                'recvWindow': 10000,
            }
        })

        if use_testnet:
            self.exchange.set_sandbox_mode(True)
            logger.info("Running on Bybit TESTNET")
        else:
            logger.info("Running on Bybit LIVE")

        # Pre-load markets to avoid internal lazy-loading errors
        try:
            self.exchange.load_markets()
        except Exception as e:
            logger.warning(f"Initial market load failed (will retry): {e}")

    def fetch_ohlcv(self, symbol: str, timeframe: str = '1h', limit: int = 200) -> pd.DataFrame:
        """Fetch OHLCV candles and return as a DataFrame."""
        try:
            ohlcv = self.exchange.fetch_ohlcv(symbol, timeframe=timeframe, limit=limit)
            df = pd.DataFrame(ohlcv, columns=['timestamp', 'open', 'high', 'low', 'close', 'volume'])
            df['timestamp'] = pd.to_datetime(df['timestamp'], unit='ms')
            df.set_index('timestamp', inplace=True)
            logger.info(f"Fetched {len(df)} candles for {symbol} [{timeframe}]")
            return df
        except Exception as e:
            logger.error(f"Error fetching OHLCV data: {e}")
            return pd.DataFrame()

    def fetch_ticker(self, symbol: str) -> dict:
        """Fetch current ticker info."""
        try:
            return self.exchange.fetch_ticker(symbol)
        except Exception as e:
            logger.error(f"Error fetching ticker: {e}")
            return {}
