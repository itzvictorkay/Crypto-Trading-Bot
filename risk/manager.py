"""
risk/manager.py
----------------
Handles position sizing, stop-loss, and take-profit calculations.
Never risks more than MAX_RISK_PER_TRADE of account balance per trade.
"""

import logging

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
            amount = risk_amount / (current_price * self.config.STOP_LOSS_PCT)
            amount = round(amount, 6)

            logger.info(f"Position size: {amount} | Risk amount: {risk_amount:.2f} USDT")
            return amount
        except Exception as e:
            logger.error(f"Position sizing error: {e}")
            return 0.0

    def calculate_sl_tp(self, signal: str, entry_price: float):
        """Calculate stop-loss and take-profit levels."""
        if signal == 'BUY':
            sl = entry_price * (1 - self.config.STOP_LOSS_PCT)
            tp = entry_price * (1 + self.config.TAKE_PROFIT_PCT)
        else:
            sl = entry_price * (1 + self.config.STOP_LOSS_PCT)
            tp = entry_price * (1 - self.config.TAKE_PROFIT_PCT)

        sl, tp = round(sl, 4), round(tp, 4)
        logger.info(f"SL: {sl} | TP: {tp} | R:R = 1:{self.config.TAKE_PROFIT_PCT / self.config.STOP_LOSS_PCT:.1f}")
        return sl, tp
