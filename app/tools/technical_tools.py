"""
app/tools/technical_tools.py
----------------------------
LangChain tools for technical indicator operations.
These tools allow the AI agent to request technical analysis (RSI, MACD, Moving Averages, BB).
"""

import logging
from typing import Optional
from langchain_core.tools import tool

from app.services.technical_service import TechnicalService

logger = logging.getLogger(__name__)

# Module-level service instance
_technical_service = None


def get_technical_service() -> TechnicalService:
    """Get or create TechnicalService instance."""
    global _technical_service
    if _technical_service is None:
        _technical_service = TechnicalService()
    return _technical_service


@tool
def calculate_rsi(symbol: str, timeframe: str = "1h") -> str:
    """
    Calculate the Relative Strength Index (RSI) for a trading pair.
    
    Args:
        symbol: Trading pair (e.g., 'BTC/USDT', 'ETH/USDT')
        timeframe: Candle timeframe ('15m', '30m', '1h', '4h', '1d', default '1h')
    
    Returns:
        RSI analysis summary string
    """
    try:
        service = get_technical_service()
        stats = service.analyze_indicators(symbol, timeframe=timeframe)
        
        if stats is None or stats.get("rsi") is None:
            return f"Error: Could not calculate RSI for {symbol} [{timeframe}]"
            
        rsi = stats["rsi"]
        
        # Interpret RSI status
        if rsi >= 70:
            status = "Overbought (Bearish reversal risk)"
        elif rsi <= 30:
            status = "Oversold (Bullish reversal risk)"
        else:
            status = "Neutral"
            
        return f"{symbol} [{timeframe}] RSI: {rsi:.2f} ({status})"
    except Exception as e:
        logger.error(f"Error in calculate_rsi: {e}")
        return f"Error calculating RSI: {str(e)}"


@tool
def calculate_macd(symbol: str, timeframe: str = "1h") -> str:
    """
    Calculate MACD and signal line crossover statistics for a trading pair.
    
    Args:
        symbol: Trading pair (e.g., 'BTC/USDT')
        timeframe: Candle timeframe ('15m', '1h', '4h', '1d', default '1h')
    
    Returns:
        MACD analysis summary string
    """
    try:
        service = get_technical_service()
        stats = service.analyze_indicators(symbol, timeframe=timeframe)
        
        if stats is None or stats.get("macd") is None:
            return f"Error: Could not calculate MACD for {symbol} [{timeframe}]"
            
        macd = stats["macd"]
        macd_signal = stats["macd_signal"]
        diff = macd - macd_signal
        crossover = "Bullish (MACD above Signal)" if diff > 0 else "Bearish (MACD below Signal)"
        
        return (
            f"{symbol} [{timeframe}] MACD Analysis:\n"
            f"  MACD line: {macd:.4f}\n"
            f"  Signal line: {macd_signal:.4f}\n"
            f"  Histogram: {diff:.4f} ({crossover})"
        )
    except Exception as e:
        logger.error(f"Error in calculate_macd: {e}")
        return f"Error calculating MACD: {str(e)}"


@tool
def calculate_moving_averages(symbol: str, timeframe: str = "1h") -> str:
    """
    Calculate moving averages (EMA fast, EMA slow, EMA 200) to determine trend direction.
    
    Args:
        symbol: Trading pair (e.g., 'BTC/USDT')
        timeframe: Candle timeframe ('15m', '1h', '4h', '1d', default '1h')
    
    Returns:
        Moving Averages analysis summary string
    """
    try:
        service = get_technical_service()
        stats = service.analyze_indicators(symbol, timeframe=timeframe)
        
        if stats is None or stats.get("ema_fast") is None:
            return f"Error: Could not calculate moving averages for {symbol} [{timeframe}]"
            
        ema_fast = stats["ema_fast"]
        ema_slow = stats["ema_slow"]
        ema_200 = stats["ema_200"]
        close_price = stats["close_price"]
        
        crossover = "Bullish Crossover (EMA Fast > EMA Slow)" if ema_fast > ema_slow else "Bearish Crossover (EMA Fast <= EMA Slow)"
        trend_200 = "Above 200 EMA (Long-term Bullish)" if (ema_200 and close_price > ema_200) else "Below 200 EMA (Long-term Bearish)"
        
        result = (
            f"{symbol} [{timeframe}] Close Price: ${close_price:,.2f}\n"
            f"  EMA Fast (Short-term): ${ema_fast:,.2f}\n"
            f"  EMA Slow (Medium-term): ${ema_slow:,.2f} ({crossover})\n"
        )
        if ema_200:
            result += f"  EMA 200 (Long-term trend): ${ema_200:,.2f} ({trend_200})"
            
        return result
    except Exception as e:
        logger.error(f"Error in calculate_moving_averages: {e}")
        return f"Error calculating Moving Averages: {str(e)}"


@tool
def calculate_bollinger_bands(symbol: str, timeframe: str = "1h") -> str:
    """
    Calculate Bollinger Bands values (Upper band, Lower band, Close price relationship).
    
    Args:
        symbol: Trading pair (e.g., 'BTC/USDT')
        timeframe: Candle timeframe ('15m', '1h', '4h', '1d', default '1h')
    
    Returns:
        Bollinger Bands analysis summary string
    """
    try:
        service = get_technical_service()
        stats = service.analyze_indicators(symbol, timeframe=timeframe)
        
        if stats is None or stats.get("bb_upper") is None:
            return f"Error: Could not calculate Bollinger Bands for {symbol} [{timeframe}]"
            
        bb_upper = stats["bb_upper"]
        bb_lower = stats["bb_lower"]
        close_price = stats["close_price"]
        
        # Relation to bands
        if close_price > bb_upper:
            position = "Over upper band (Highly Overbought)"
        elif close_price < bb_lower:
            position = "Under lower band (Highly Oversold)"
        else:
            pct = (close_price - bb_lower) / (bb_upper - bb_lower) * 100
            position = f"Between bands (at {pct:.1f}% range)"
            
        return (
            f"{symbol} [{timeframe}] Bollinger Bands Analysis:\n"
            f"  Upper Band: ${bb_upper:,.2f}\n"
            f"  Close Price: ${close_price:,.2f} ({position})\n"
            f"  Lower Band: ${bb_lower:,.2f}"
        )
    except Exception as e:
        logger.error(f"Error in calculate_bollinger_bands: {e}")
        return f"Error calculating Bollinger Bands: {str(e)}"


@tool
def calculate_market_indicators(symbol: str, timeframe: str = "1h") -> str:
    """
    Calculate all technical indicators (RSI, MACD, Moving Averages, Bollinger Bands, ATR) for a symbol.
    Provides a comprehensive market technical summary.
    
    Args:
        symbol: Trading pair (e.g., 'BTC/USDT')
        timeframe: Candle timeframe ('15m', '1h', '4h', '1d', default '1h')
    
    Returns:
        Comprehensive technical indicator summary string
    """
    try:
        service = get_technical_service()
        stats = service.analyze_indicators(symbol, timeframe=timeframe)
        
        if stats is None:
            return f"Error: Could not calculate indicators for {symbol} [{timeframe}]"
            
        rsi_status = "Oversold" if (stats["rsi"] and stats["rsi"] <= 30) else ("Overbought" if (stats["rsi"] and stats["rsi"] >= 70) else "Neutral")
        macd_crossover = "Bullish" if (stats["macd"] and stats["macd_signal"] and stats["macd"] > stats["macd_signal"]) else "Bearish"
        
        result = (
            f"=== Technical Analysis Report: {symbol} [{timeframe}] ===\n"
            f"Close Price: ${stats['close_price']:,.2f}\n"
            f"Trend Bias: {stats['trend'].upper()}\n"
            f"Confluence Signal: {stats['recommended_signal']}\n\n"
            f"Technical Metrics:\n"
            f"  - RSI: {stats['rsi']:.2f} ({rsi_status})\n"
            f"  - MACD: {stats['macd']:.4f} | Signal: {stats['macd_signal']:.4f} ({macd_crossover})\n"
            f"  - EMA Fast/Slow: ${stats['ema_fast']:,.2f} / ${stats['ema_slow']:,.2f}\n"
            f"  - EMA 200: ${stats['ema_200']:,.2f} if stats['ema_200'] else 'N/A'\n"
            f"  - Bollinger Bands: Low ${stats['bb_lower']:,.2f} | High ${stats['bb_upper']:,.2f}\n"
            f"  - ATR (Volatility): {stats['atr']:.4f}\n"
            f"  - Volume Trend: {stats['volume_trend'].upper()}"
        )
        
        return result
    except Exception as e:
        logger.error(f"Error in calculate_market_indicators: {e}")
        return f"Error calculating technical summary: {str(e)}"


# Export tools for registration
TECHNICAL_TOOLS = [
    calculate_rsi,
    calculate_macd,
    calculate_moving_averages,
    calculate_bollinger_bands,
    calculate_market_indicators,
]
