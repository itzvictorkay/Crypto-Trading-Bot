"""
app/services/technical_service.py
----------------------------------
Service layer for technical analysis operations.
Wraps the existing SignalEngine to calculate indicators (RSI, MACD, EMA, BB, ATR).
Provides structured responses for LangChain tools.
"""

import logging
from typing import Dict, Any, Optional
import pandas as pd

from app.services.market_service import MarketService
from analysis.signals import SignalEngine
import config

logger = logging.getLogger(__name__)


class TechnicalService:
    """Service layer for technical indicator analysis."""

    def __init__(self, market_service: Optional[MarketService] = None):
        """
        Initialize TechnicalService.
        
        Args:
            market_service: MarketService instance for fetching data.
        """
        self.market_service = market_service or MarketService()
        self.signal_engine = SignalEngine(config)
        logger.info("TechnicalService initialized")

    def analyze_indicators(self, symbol: str, timeframe: str = '1h') -> Optional[Dict[str, Any]]:
        """
        Calculate technical indicators for a symbol and return a structured summary.
        
        Args:
            symbol: Trading pair (e.g., 'BTC/USDT')
            timeframe: Candle timeframe ('1m', '5m', '15m', '1h', '4h', '1d')
            
        Returns:
            Dict containing current indicator values, or None if error
        """
        try:
            # Fetch candles (need enough history for indicators like 200 EMA)
            limit = max(250, config.CANDLE_LIMIT)
            df = self.market_service.get_market_data(symbol, timeframe=timeframe, limit=limit)
            
            if df is None or df.empty:
                logger.warning(f"Could not fetch candle data for {symbol} [{timeframe}] to calculate indicators")
                return None
            
            # Calculate indicators using existing engine
            df_with_indicators = self.signal_engine.calculate_indicators(df)
            
            if df_with_indicators.empty:
                logger.warning(f"Failed to calculate indicators for {symbol} [{timeframe}]")
                return None
                
            last_row = df_with_indicators.iloc[-1]
            
            # Parse signal confluence
            signal, raw_indicators = self.signal_engine.generate_signal(df_with_indicators)
            
            # Construct structured technical data
            result = {
                "symbol": symbol,
                "timeframe": timeframe,
                "close_price": float(last_row["close"]),
                "rsi": float(last_row["rsi"]) if "rsi" in last_row and not pd.isna(last_row["rsi"]) else None,
                "ema_fast": float(last_row["ema_fast"]) if "ema_fast" in last_row and not pd.isna(last_row["ema_fast"]) else None,
                "ema_slow": float(last_row["ema_slow"]) if "ema_slow" in last_row and not pd.isna(last_row["ema_slow"]) else None,
                "ema_200": float(last_row["ema_200"]) if "ema_200" in last_row and not pd.isna(last_row["ema_200"]) else None,
                "macd": float(last_row["macd"]) if "macd" in last_row and not pd.isna(last_row["macd"]) else None,
                "macd_signal": float(last_row["macd_signal"]) if "macd_signal" in last_row and not pd.isna(last_row["macd_signal"]) else None,
                "bb_upper": float(last_row["bb_upper"]) if "bb_upper" in last_row and not pd.isna(last_row["bb_upper"]) else None,
                "bb_lower": float(last_row["bb_lower"]) if "bb_lower" in last_row and not pd.isna(last_row["bb_lower"]) else None,
                "atr": float(last_row["atr"]) if "atr" in last_row and not pd.isna(last_row["atr"]) else None,
                "trend": "bullish" if raw_indicators.get("trend") == "UP" else "bearish",
                "recommended_signal": signal,
                "volume": float(last_row["volume"]),
                "avg_volume": float(last_row["avg_volume"]) if "avg_volume" in last_row and not pd.isna(last_row["avg_volume"]) else None,
            }
            
            # Volume status
            if result["avg_volume"] is not None:
                ratio = result["volume"] / result["avg_volume"]
                if ratio > 1.5:
                    result["volume_trend"] = "high"
                elif ratio < 0.5:
                    result["volume_trend"] = "low"
                else:
                    result["volume_trend"] = "normal"
            else:
                result["volume_trend"] = "unknown"
                
            logger.info(f"Technical indicators analysis completed for {symbol} [{timeframe}]")
            return result
            
        except Exception as e:
            logger.error(f"Error in TechnicalService.analyze_indicators for {symbol}: {e}", exc_info=True)
            return None
