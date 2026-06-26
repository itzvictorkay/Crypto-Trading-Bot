"""
trading/executor.py
--------------------
Handles all order placement on Bybit via ccxt.
Supports market orders, stop-loss, and take-profit.
"""

import logging
from dashboard.shared_db import DashboardDB

logger = logging.getLogger(__name__)


class OrderExecutor:
    def __init__(self, exchange, config):
        self.exchange = exchange
        self.config = config
        self.db = DashboardDB()

    def execute_trade(self, symbol: str, signal: str, amount: float, sl_price: float, tp_price: float):
        """Place a market order with stop-loss and take-profit."""
        try:
            side = 'buy' if signal == 'BUY' else 'sell'
            sl_side = 'sell' if side == 'buy' else 'buy'

            # Main market order with SL/TP attached (Preferred for Bybit)
            params = {}
            if sl_price > 0:
                params['stopLoss'] = str(sl_price)
            if tp_price > 0:
                params['takeProfit'] = str(tp_price)

            # Bybit specific
            category = 'linear' if self.config.MARKET_TYPE == 'linear' else 'spot'
            params['category'] = category
            
            # positionIdx 0 for one-way mode (futures)
            if category != 'spot':
                params['positionIdx'] = 0 

            logger.info(f"Placing {side.upper()} order | {symbol} | Amount: {amount} | SL: {sl_price} | TP: {tp_price} | Category: {category}")
            order = self.exchange.create_order(
                symbol=symbol,
                type='market',
                side=side,
                amount=amount,
                params=params
            )
            logger.info(f"✅ Order placed with SL/TP: {order['id']}")

            # Log to DB
            try:
                self.db.log_trade(symbol, side.upper(), order.get('price', current_price if 'current_price' in locals() else 0), amount)
            except Exception as e:
                logger.error(f"Failed to log trade to DB: {e}")

            return order

        except Exception as e:
            logger.error(f"Order execution error: {e}")
            return None

    def cancel_all_orders(self, symbol: str):
        """Cancel all open orders for a symbol."""
        try:
            self.exchange.cancel_all_orders(symbol)
            logger.info(f"All open orders cancelled for {symbol}")
        except Exception as e:
            logger.error(f"Error cancelling orders: {e}")
