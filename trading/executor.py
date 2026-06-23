"""
trading/executor.py
--------------------
Handles all order placement on Bybit via ccxt.
Supports market orders, stop-loss, and take-profit.
"""

import logging

logger = logging.getLogger(__name__)


class OrderExecutor:
    def __init__(self, exchange, config):
        self.exchange = exchange
        self.config = config

    def execute_trade(self, symbol: str, signal: str, amount: float, sl_price: float, tp_price: float):
        """Place a market order with stop-loss and take-profit."""
        try:
            side = 'buy' if signal == 'BUY' else 'sell'
            sl_side = 'sell' if side == 'buy' else 'buy'

            # Main market order
            logger.info(f"Placing {side.upper()} market order | {symbol} | Amount: {amount}")
            order = self.exchange.create_market_order(
                symbol=symbol,
                side=side,
                amount=amount
            )
            logger.info(f"✅ Main order placed: {order['id']}")

            # Stop-loss
            try:
                sl_order = self.exchange.create_order(
                    symbol=symbol,
                    type='stop_market',
                    side=sl_side,
                    amount=amount,
                    params={'stopPrice': sl_price, 'reduceOnly': True}
                )
                logger.info(f"🛡️ Stop-loss set at {sl_price} | ID: {sl_order['id']}")
            except Exception as e:
                logger.warning(f"SL order failed (may not be supported on spot): {e}")

            # Take-profit
            try:
                tp_order = self.exchange.create_order(
                    symbol=symbol,
                    type='take_profit_market',
                    side=sl_side,
                    amount=amount,
                    params={'stopPrice': tp_price, 'reduceOnly': True}
                )
                logger.info(f"🎯 Take-profit set at {tp_price} | ID: {tp_order['id']}")
            except Exception as e:
                logger.warning(f"TP order failed (may not be supported on spot): {e}")

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
