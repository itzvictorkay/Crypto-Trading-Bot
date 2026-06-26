"""
risk/manager.py
----------------
Handles position sizing, stop-loss, and take-profit calculations.
Never risks more than MAX_RISK_PER_TRADE of account balance per trade.
"""

import logging
import math

logger = logging.getLogger(__name__)


class RiskManager:
    def __init__(self, exchange, config):
        self.exchange = exchange
        self.config = config

    def get_balance(self) -> float:
        """Fetch available USDT balance."""
        try:
            balance = self.exchange.fetch_balance()
            usdt = float(balance.get('USDT', {}).get('free', 0))
            logger.info(f"Available balance: {usdt:.2f} USDT")
            return usdt
        except Exception as e:
            logger.error(f"Error fetching balance: {e}")
            return 0.0

    def get_base_balance(self, symbol: str) -> float:
        """Fetch available balance of the base currency."""
        try:
            base_currency = symbol.split('/')[0]
            balance = self.exchange.fetch_balance()
            base_amt = float(balance.get(base_currency, {}).get('free', 0))
            return base_amt
        except Exception as e:
            logger.error(f"Error fetching base balance for {symbol}: {e}")
            return 0.0

    def has_open_position(self, symbol: str, current_price: float) -> bool:
        """Check if we already hold the asset (value > $5 to ignore dust)."""
        base_amt = self.get_base_balance(symbol)
        usdt_value = base_amt * current_price
        if usdt_value > 5.0:
            logger.info(f"Open position detected: {base_amt} {symbol.split('/')[0]} (Value: ~${usdt_value:.2f})")
            return True
        return False

    def calculate_position_size(self, symbol: str, current_price: float) -> float:
        """
        Calculate safe position size.
        Formula: (balance * risk%) / (entry * stop_loss%)
        """
        try:
            balance = self.get_balance()
            if balance <= 0:
                logger.warning("Zero balance — cannot size position.")
                return 0.0

            risk_amount = balance * self.config.MAX_RISK_PER_TRADE
            
            # Risk-based sizing: how much to buy so that if SL is hit, we lose risk_amount
            size_by_risk = risk_amount / (current_price * self.config.STOP_LOSS_PCT)
            
            # Balance-cap sizing: never use more than X% of total wallet for ONE trade
            size_by_cap = (balance * self.config.MAX_BALANCE_USAGE_PCT) / current_price
            
            # Use the more conservative of the two
            amount = min(size_by_risk, size_by_cap)
            amount = round(amount, 6)

            logger.info(f"Position size: {amount} (Risk-limited: {size_by_risk:.4f}, Cap-limited: {size_by_cap:.4f})")
            return amount
        except Exception as e:
            logger.error(f"Position sizing error: {e}")
            return 0.0

    def calculate_sl_tp(self, signal: str, entry_price: float, atr: float = None):
        """
        Calculate stop-loss and take-profit levels.
        If ATR is provided and USE_ATR_STOP is True, uses dynamic levels.
        Otherwise falls back to fixed percentages.
        """
        if self.config.USE_ATR_STOP and atr and not math.isnan(atr):
            sl_dist = atr * self.config.ATR_SL_MULTIPLIER
            tp_dist = atr * self.config.ATR_TP_MULTIPLIER
            
            if signal == 'BUY':
                sl = entry_price - sl_dist
                tp = entry_price + tp_dist
            else:
                sl = entry_price + sl_dist
                tp = entry_price - tp_dist
            
            logger.info(f"Using ATR-based SL/TP: ATR={atr:.4f} | R:R={self.config.ATR_TP_MULTIPLIER/self.config.ATR_SL_MULTIPLIER:.1f}")
        else:
            if signal == 'BUY':
                sl = entry_price * (1 - self.config.STOP_LOSS_PCT)
                tp = entry_price * (1 + self.config.TAKE_PROFIT_PCT)
            else:
                sl = entry_price * (1 + self.config.STOP_LOSS_PCT)
                tp = entry_price * (1 - self.config.TAKE_PROFIT_PCT)
            
            logger.info(f"Using FIXED % SL/TP: R:R={self.config.TAKE_PROFIT_PCT/self.config.STOP_LOSS_PCT:.1f}")

        sl, tp = round(sl, 4), round(tp, 4)
        return sl, tp
