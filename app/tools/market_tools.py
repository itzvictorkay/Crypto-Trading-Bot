"""
app/tools/market_tools.py
-------------------------
LangChain tools for market data operations.
These tools allow Claude to fetch real-time crypto prices and OHLCV data.
"""

import logging
from typing import Optional
from langchain_core.tools import tool

from app.services.market_service import MarketService

logger = logging.getLogger(__name__)

# Initialize service (singleton-like for the module)
_market_service = None


def get_market_service() -> MarketService:
    """Get or create MarketService instance."""
    global _market_service
    if _market_service is None:
        _market_service = MarketService()
    return _market_service


@tool
def get_crypto_price(symbol: str) -> str:
    """
    Get the current price of a cryptocurrency.
    
    Args:
        symbol: Trading pair (e.g., 'BTC/USDT', 'ETH/USDT')
    
    Returns:
        Current price as a string, or error message
    
    Example:
        >>> get_crypto_price('BTC/USDT')
        'BTC/USDT: $45,230.50'
    """
    try:
        service = get_market_service()
        price = service.get_current_price(symbol)
        
        if price is None:
            return f"Error: Could not fetch price for {symbol}"
        
        return f"{symbol}: ${price:,.2f}"
    except Exception as e:
        logger.error(f"Error in get_crypto_price: {e}")
        return f"Error fetching price for {symbol}: {str(e)}"


@tool
def get_market_data(
    symbol: str,
    timeframe: str = "1h",
    limit: int = 50
) -> str:
    """
    Get historical OHLCV (Open, High, Low, Close, Volume) market data.
    
    Args:
        symbol: Trading pair (e.g., 'BTC/USDT')
        timeframe: Candle timeframe - '1m', '5m', '15m', '1h', '4h', '1d'
        limit: Number of candles to fetch (max 200, default 50)
    
    Returns:
        Market data summary as a string
    
    Example:
        >>> get_market_data('ETH/USDT', timeframe='1h', limit=20)
        'ETH/USDT [1h] - 20 candles fetched. Latest: Open: $2,450.00, Close: $2,465.00, High: $2,475.00, Low: $2,445.00'
    """
    try:
        if limit > 200:
            limit = 200
        if limit < 1:
            return "Error: limit must be at least 1"
        
        service = get_market_service()
        df = service.get_market_data(symbol, timeframe=timeframe, limit=limit)
        
        if df is None or df.empty:
            return f"Error: No market data available for {symbol} [{timeframe}]"
        
        latest = df.iloc[-1]
        oldest = df.iloc[0]
        
        result = (
            f"{symbol} [{timeframe}] - {len(df)} candles fetched\n"
            f"  Latest candle: O: ${latest['open']:,.2f} | H: ${latest['high']:,.2f} | "
            f"L: ${latest['low']:,.2f} | C: ${latest['close']:,.2f} | V: {latest['volume']:,.0f}\n"
            f"  Period range: ${oldest['low']:,.2f} - ${df['high'].max():,.2f}\n"
            f"  Average close: ${df['close'].mean():,.2f}"
        )
        
        return result
    except Exception as e:
        logger.error(f"Error in get_market_data: {e}")
        return f"Error fetching market data: {str(e)}"


@tool
def get_volume_stats(symbol: str, timeframe: str = "1h") -> str:
    """
    Get volume statistics for a trading pair.
    
    Args:
        symbol: Trading pair (e.g., 'BTC/USDT')
        timeframe: Candle timeframe ('1h', '4h', '1d')
    
    Returns:
        Volume statistics as a string
    
    Example:
        >>> get_volume_stats('BTC/USDT', timeframe='1h')
        'BTC/USDT [1h] - Avg: 1,234,567 | Current: 1,456,789 | Max: 2,345,678'
    """
    try:
        service = get_market_service()
        stats = service.get_volume_stats(symbol, timeframe=timeframe)
        
        if stats is None:
            return f"Error: Could not calculate volume stats for {symbol}"
        
        result = (
            f"{symbol} [{timeframe}]\n"
            f"  Current: {stats['current_volume']:,.0f}\n"
            f"  Average: {stats['average_volume']:,.0f}\n"
            f"  Max: {stats['max_volume']:,.0f}\n"
            f"  Min: {stats['min_volume']:,.0f}\n"
            f"  Total (50 candles): {stats['total_volume']:,.0f}"
        )
        
        return result
    except Exception as e:
        logger.error(f"Error in get_volume_stats: {e}")
        return f"Error fetching volume stats: {str(e)}"


@tool
def get_price_comparison(symbols: str) -> str:
    """
    Compare current prices across multiple cryptocurrencies.
    
    Args:
        symbols: Comma-separated trading pairs (e.g., 'BTC/USDT,ETH/USDT,SOL/USDT')
    
    Returns:
        Price comparison summary as a string
    
    Example:
        >>> get_price_comparison('BTC/USDT,ETH/USDT')
        'BTC/USDT: $45,230.50 | ETH/USDT: $2,465.25'
    """
    try:
        # Parse comma-separated symbols
        symbol_list = [s.strip() for s in symbols.split(',')]
        
        if not symbol_list:
            return "Error: No symbols provided"
        
        if len(symbol_list) > 10:
            return "Error: Maximum 10 symbols allowed"
        
        service = get_market_service()
        prices = service.get_price_comparison(symbol_list)
        
        if prices is None or not prices:
            return "Error: Could not fetch prices for any symbol"
        
        # Format results
        price_lines = [f"{symbol}: ${price:,.2f}" for symbol, price in prices.items()]
        result = "Price Comparison:\n  " + "\n  ".join(price_lines)
        
        if len(prices) < len(symbol_list):
            missing = set(symbol_list) - set(prices.keys())
            result += f"\n(Failed to fetch: {', '.join(missing)})"
        
        return result
    except Exception as e:
        logger.error(f"Error in get_price_comparison: {e}")
        return f"Error comparing prices: {str(e)}"


@tool
def get_price_change(symbol: str, period_hours: int = 24) -> str:
    """
    Calculate price change over a specified period.
    
    Args:
        symbol: Trading pair (e.g., 'BTC/USDT')
        period_hours: Hours to look back (1, 4, 24, etc.)
    
    Returns:
        Price change statistics as a string
    
    Example:
        >>> get_price_change('ETH/USDT', period_hours=24)
        'ETH/USDT 24h Change: +2.5% ($60.50) | Open: $2,400 | Close: $2,460'
    """
    try:
        if period_hours < 1:
            return "Error: period_hours must be at least 1"
        
        service = get_market_service()
        change_data = service.get_price_change(symbol, period_hours=period_hours)
        
        if change_data is None:
            return f"Error: Could not calculate price change for {symbol}"
        
        direction = "📈" if change_data['percent_change'] >= 0 else "📉"
        
        result = (
            f"{symbol} {period_hours}h Change: {direction} {change_data['percent_change']:+.2f}% "
            f"(${change_data['change']:+,.2f})\n"
            f"  Open: ${change_data['open_price']:,.2f}\n"
            f"  Close: ${change_data['close_price']:,.2f}\n"
            f"  High: ${change_data['high_price']:,.2f}\n"
            f"  Low: ${change_data['low_price']:,.2f}"
        )
        
        return result
    except Exception as e:
        logger.error(f"Error in get_price_change: {e}")
        return f"Error calculating price change: {str(e)}"


@tool
def get_support_resistance(
    symbol: str,
    timeframe: str = "1h"
) -> str:
    """
    Identify support and resistance levels for a trading pair.
    
    Args:
        symbol: Trading pair (e.g., 'BTC/USDT')
        timeframe: Candle timeframe ('1h', '4h', '1d')
    
    Returns:
        Support/resistance levels as a string
    
    Example:
        >>> get_support_resistance('BTC/USDT')
        'BTC/USDT Support: $45,000 | Pivot: $45,500 | Resistance: $46,000'
    """
    try:
        service = get_market_service()
        sr_data = service.get_support_resistance(symbol, timeframe=timeframe)
        
        if sr_data is None:
            return f"Error: Could not calculate support/resistance for {symbol}"
        
        current = sr_data['current_price']
        support = sr_data['support']
        pivot = sr_data['pivot']
        resistance = sr_data['resistance']
        
        # Determine position relative to levels
        if current > resistance:
            position = "⬆️ Above resistance"
        elif current < support:
            position = "⬇️ Below support"
        else:
            position = "➡️ Between support and resistance"
        
        result = (
            f"{symbol} [{timeframe}] {position}\n"
            f"  Support: ${support:,.2f}\n"
            f"  Pivot: ${pivot:,.2f}\n"
            f"  Resistance: ${resistance:,.2f}\n"
            f"  Current: ${current:,.2f}"
        )
        
        return result
    except Exception as e:
        logger.error(f"Error in get_support_resistance: {e}")
        return f"Error calculating support/resistance: {str(e)}"


# List of all market tools for registration
MARKET_TOOLS = [
    get_crypto_price,
    get_market_data,
    get_volume_stats,
    get_price_comparison,
    get_price_change,
    get_support_resistance,
]
