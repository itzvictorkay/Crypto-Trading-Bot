"""
app/services/risk_service.py
----------------------------
Service layer for risk analysis and portfolio management.
Wraps the existing RiskManager class to calculate position sizing, SL/TP levels,
and assess balance details for LangChain tools.
"""

import logging
from typing import Dict, Any, Optional

from app.services.market_service import MarketService
from risk.manager import RiskManager
import config

logger = logging.getLogger(__name__)


class RiskService:
    """Service layer for computing trade risk, position sizing, and stop-loss/take-profit levels."""

    def __init__(self, market_service: Optional[MarketService] = None):
        """
        Initialize RiskService.
        
        Args:
            market_service: Optional MarketService instance.
        """
        self.market_service = market_service or MarketService()
        # Reuse existing fetcher exchange from MarketService to keep configurations consistent
        self.risk_manager = RiskManager(
            exchange=self.market_service.fetcher.exchange,
            config=config
        )
        logger.info("RiskService initialized")

    def get_portfolio_balance(self) -> Dict[str, Any]:
        """
        Retrieve account balance details.
        
        Returns:
            Dict containing USDT balance and other details
        """
        try:
            usdt_balance = self.risk_manager.get_balance()
            return {
                "available_usdt": usdt_balance,
                "max_risk_amount": usdt_balance * config.MAX_RISK_PER_TRADE,
                "max_trade_cap": usdt_balance * config.MAX_BALANCE_USAGE_PCT
            }
        except Exception as e:
            logger.error(f"Error fetching portfolio balance: {e}")
            return {
                "available_usdt": 0.0,
                "max_risk_amount": 0.0,
                "max_trade_cap": 0.0,
                "error": str(e)
            }

    def assess_trade_risk(
        self, 
        symbol: str, 
        current_price: float, 
        signal: str, 
        atr: Optional[float] = None
    ) -> Dict[str, Any]:
        """
        Calculate risk parameters for a potential trade setup.
        
        Args:
            symbol: Trading pair (e.g. 'BTC/USDT')
            current_price: Current market price
            signal: Trade direction ('BUY' or 'SELL')
            atr: Average True Range for volatility stops (optional)
            
        Returns:
            Dict containing position size, stop-loss, take-profit, and risk ratio
        """
        try:
            # 1. Position size calculation
            position_size = self.risk_manager.calculate_position_size(symbol, current_price)
            
            # 2. Stop-loss & Take-profit calculation
            sl, tp = self.risk_manager.calculate_sl_tp(signal, current_price, atr=atr)
            
            # 3. Check for existing position
            has_pos = self.risk_manager.has_open_position(symbol, current_price)
            
            # 4. Calculate reward-to-risk ratio
            risk_dist = abs(current_price - sl)
            reward_dist = abs(tp - current_price)
            rr_ratio = reward_dist / risk_dist if risk_dist > 0 else 0.0
            
            return {
                "symbol": symbol,
                "signal": signal,
                "current_price": current_price,
                "position_size": position_size,
                "total_cost_usdt": position_size * current_price,
                "stop_loss": sl,
                "take_profit": tp,
                "reward_risk_ratio": rr_ratio,
                "has_existing_position": has_pos,
                "atr_used": atr is not None and config.USE_ATR_STOP
            }
        except Exception as e:
            logger.error(f"Error assessing trade risk for {symbol}: {e}")
            return {
                "symbol": symbol,
                "error": str(e)
            }
