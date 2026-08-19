"""
app/services/market_service.py
------------------------------
Service layer for market data operations.
Wraps existing DataFetcher with error handling, logging, and type hints.
Provides clean interface for LangChain tools to use.
"""

import logging
from typing import Dict, List, Optional, Tuple
from datetime import datetime, timedelta
import pandas as pd

from data.fetcher import DataFetcher
from config import BYBIT_API_KEY, BYBIT_API_SECRET, USE_TESTNET

logger = logging.getLogger(__name__)


class MarketService:
    """Service layer for crypto market data operations."""
    
    def __init__(self, fetcher: Optional[DataFetcher] = None):
        """
        Initialize MarketService.
        
        Args:
            fetcher: DataFetcher instance. If None, creates one using config.
        """
        if fetcher is None:
            self.fetcher = DataFetcher(
                api_key=BYBIT_API_KEY,
                api_secret=BYBIT_API_SECRET,
                use_testnet=USE_TESTNET,
                market_type='spot'
            )
        else:
            self.fetcher = fetcher
        
        logger.info("MarketService initialized")
    
    def get_current_price(self, symbol: str) -> Optional[float]:
        """
        Get current price for a symbol.
        
        Args:
            symbol: Trading pair (e.g., 'BTC/USDT')
            
        Returns:
            Current price as float, or None if error
            
        Example:
            >>> service = MarketService()
            >>> price = service.get_current_price('BTC/USDT')
            >>> print(f"BTC price: ${price:.2f}")
        """
        try:
            ticker = self.fetcher.fetch_ticker(symbol)
            if not ticker or 'last' not in ticker:
                logger.warning(f"No price data for {symbol}")
                return None
            
            price = ticker['last']
            logger.info(f"Current price for {symbol}: ${price:.2f}")
            return price
        except Exception as e:
            logger.error(f"Error fetching price for {symbol}: {e}")
            return None
    
    def get_market_data(
        self, 
        symbol: str, 
        timeframe: str = '1h',
        limit: int = 100
    ) -> Optional[pd.DataFrame]:
        """
        Get OHLCV market data for a symbol.
        
        Args:
            symbol: Trading pair (e.g., 'BTC/USDT')
            timeframe: Candle timeframe ('1m', '5m', '15m', '1h', '4h', '1d')
            limit: Number of candles to fetch (default 100)
            
        Returns:
            DataFrame with OHLCV data, or None if error
            
        Example:
            >>> service = MarketService()
            >>> df = service.get_market_data('ETH/USDT', timeframe='1h', limit=50)
            >>> print(f"Last price: {df['close'].iloc[-1]}")
        """
        try:
            if limit > 1000:
                logger.warning(f"Limiting candles to 1000 (requested {limit})")
                limit = 1000
            
            df = self.fetcher.fetch_ohlcv(symbol, timeframe=timeframe, limit=limit)
            
            if df.empty:
                logger.warning(f"No market data for {symbol} [{timeframe}]")
                return None
            
            logger.info(f"Retrieved {len(df)} candles for {symbol} [{timeframe}]")
            return df
        except Exception as e:
            logger.error(f"Error fetching market data for {symbol}: {e}")
            return None
    
    def get_volume_stats(self, symbol: str, timeframe: str = '1h') -> Optional[Dict]:
        """
        Get volume statistics for a symbol.
        
        Args:
            symbol: Trading pair (e.g., 'BTC/USDT')
            timeframe: Candle timeframe ('1h', '4h', '1d')
            
        Returns:
            Dict with volume stats (avg, max, min, total), or None if error
            
        Example:
            >>> service = MarketService()
            >>> stats = service.get_volume_stats('BTC/USDT')
            >>> print(f"Average volume: {stats['average_volume']:.0f}")
        """
        try:
            df = self.get_market_data(symbol, timeframe=timeframe, limit=50)
            
            if df is None or df.empty:
                logger.warning(f"Cannot calculate volume stats for {symbol}")
                return None
            
            stats = {
                'symbol': symbol,
                'timeframe': timeframe,
                'average_volume': float(df['volume'].mean()),
                'max_volume': float(df['volume'].max()),
                'min_volume': float(df['volume'].min()),
                'total_volume': float(df['volume'].sum()),
                'current_volume': float(df['volume'].iloc[-1]),
                'timestamp': datetime.now().isoformat()
            }
            
            logger.info(f"Volume stats for {symbol}: avg={stats['average_volume']:.0f}")
            return stats
        except Exception as e:
            logger.error(f"Error calculating volume stats: {e}")
            return None
    
    def get_price_comparison(self, symbols: List[str]) -> Optional[Dict]:
        """
        Get current prices for multiple symbols.
        
        Args:
            symbols: List of trading pairs (e.g., ['BTC/USDT', 'ETH/USDT'])
            
        Returns:
            Dict mapping symbol to price, or None if error
            
        Example:
            >>> service = MarketService()
            >>> prices = service.get_price_comparison(['BTC/USDT', 'ETH/USDT'])
            >>> for symbol, price in prices.items():
            ...     print(f"{symbol}: ${price:.2f}")
        """
        try:
            prices = {}
            for symbol in symbols:
                price = self.get_current_price(symbol)
                if price is not None:
                    prices[symbol] = price
            
            if not prices:
                logger.warning("Could not fetch prices for any symbol")
                return None
            
            logger.info(f"Price comparison: {len(prices)}/{len(symbols)} symbols fetched")
            return prices
        except Exception as e:
            logger.error(f"Error in price comparison: {e}")
            return None
    
    def get_price_change(
        self, 
        symbol: str, 
        period_hours: int = 24
    ) -> Optional[Dict]:
        """
        Calculate price change over a period.
        
        Args:
            symbol: Trading pair (e.g., 'BTC/USDT')
            period_hours: Hours to look back (default 24)
            
        Returns:
            Dict with price change metrics, or None if error
            
        Example:
            >>> service = MarketService()
            >>> change = service.get_price_change('BTC/USDT', period_hours=24)
            >>> print(f"24h change: {change['percent_change']:.2f}%")
        """
        try:
            # Determine timeframe based on period
            if period_hours <= 1:
                timeframe = '1m'
                limit = period_hours * 60
            elif period_hours <= 4:
                timeframe = '5m'
                limit = (period_hours * 60) // 5
            elif period_hours <= 24:
                timeframe = '1h'
                limit = period_hours
            else:
                timeframe = '1d'
                limit = period_hours // 24
            
            df = self.get_market_data(symbol, timeframe=timeframe, limit=limit)
            
            if df is None or len(df) < 2:
                logger.warning(f"Insufficient data for price change calculation")
                return None
            
            open_price = df['open'].iloc[0]
            close_price = df['close'].iloc[-1]
            high_price = df['high'].max()
            low_price = df['low'].min()
            
            change = close_price - open_price
            percent_change = (change / open_price) * 100
            
            result = {
                'symbol': symbol,
                'period_hours': period_hours,
                'open_price': float(open_price),
                'close_price': float(close_price),
                'high_price': float(high_price),
                'low_price': float(low_price),
                'change': float(change),
                'percent_change': float(percent_change),
                'timestamp': datetime.now().isoformat()
            }
            
            logger.info(f"Price change for {symbol}: {percent_change:+.2f}%")
            return result
        except Exception as e:
            logger.error(f"Error calculating price change: {e}")
            return None
    
    def get_support_resistance(
        self, 
        symbol: str,
        timeframe: str = '1h',
        lookback: int = 50
    ) -> Optional[Dict]:
        """
        Identify support and resistance levels (simple pivot points).
        
        Args:
            symbol: Trading pair
            timeframe: Candle timeframe
            lookback: Number of candles to analyze
            
        Returns:
            Dict with support/resistance levels, or None if error
        """
        try:
            df = self.get_market_data(symbol, timeframe=timeframe, limit=lookback)
            
            if df is None or df.empty:
                return None
            
            # Simple pivot calculation: average of highs and lows
            pivot = (df['high'].max() + df['low'].min() + df['close'].iloc[-1]) / 3
            resistance = (df['high'].max() * 2) - df['low'].min()
            support = (df['low'].min() * 2) - df['high'].max()
            
            result = {
                'symbol': symbol,
                'timeframe': timeframe,
                'support': float(support),
                'pivot': float(pivot),
                'resistance': float(resistance),
                'current_price': float(df['close'].iloc[-1]),
                'timestamp': datetime.now().isoformat()
            }
            
            logger.info(f"S/R for {symbol}: S={support:.2f}, R={resistance:.2f}")
            return result
        except Exception as e:
            logger.error(f"Error calculating support/resistance: {e}")
            return None
