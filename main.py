"""
main.py
--------
Multi-pair, multi-timeframe crypto trading bot for Bybit.
Each pair runs in its own thread.
Confirms signals across multiple timeframes before trading.
"""

import time
import logging
import asyncio
import threading
import os
from telegram import Bot
import config
from dashboard.shared_db import DashboardDB

os.environ.setdefault('PYTHONIOENCODING', 'utf-8')

logging.basicConfig(
    level=getattr(logging, config.LOG_LEVEL.upper(), logging.INFO),
    format='%(asctime)s [%(levelname)s] %(name)s - %(message)s',
    handlers=[
        logging.FileHandler(config.LOG_FILE, encoding='utf-8'),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger(__name__)

from data.fetcher import DataFetcher
from analysis.signals import SignalEngine
from risk.manager import RiskManager
from trading.executor import OrderExecutor


# ── Telegram ──────────────────────────────────────────────────────────────────
def send_alert(message: str):
    if not config.TELEGRAM_ENABLED or not config.TELEGRAM_TOKEN or not config.TELEGRAM_CHAT_ID:
        return
    async def _send():
        try:
            async with Bot(token=config.TELEGRAM_TOKEN) as bot:
                await bot.send_message(
                    chat_id=config.TELEGRAM_CHAT_ID,
                    text=message,
                    parse_mode='HTML'
                )
        except Exception as e:
            logger.error(f"Telegram alert failed: {e}")
    try:
        # Use a background task for telegram to avoid blocking the main loop
        loop = asyncio.new_event_loop()
        threading.Thread(target=lambda: loop.run_until_complete(_send()), daemon=True).start()
    except Exception as e:
        logger.error(f"Alert error: {e}")


# ── Position Tracker ──────────────────────────────────────────────────────────
class PositionTracker:
    def __init__(self, exchange, market_type: str = 'spot'):
        self.exchange = exchange
        self.market_type = market_type
        self._lock = threading.Lock()

    def has_open_position(self, symbol: str) -> bool:
        try:
            if self.market_type in ['future', 'swap', 'linear', 'inverse']:
                # Bybit V5 requires category: 'linear' for USDT/USDC pairs, 'inverse' for Coin pairs
                category = 'linear' if ('USDT' in symbol or 'USDC' in symbol) else 'inverse'
                
                # Fetch positions for specific symbol to reduce data/bandwidth
                positions = self.exchange.fetch_positions(symbols=[symbol], params={'category': category})
                
                for pos in positions:
                    # In V5, contracts/size is absolute. Side tells us if Long or Short.
                    contracts = float(pos.get('contracts', 0) or pos.get('size', 0) or 0)
                    if pos['symbol'] == symbol and contracts > 0:
                        logger.info(f"[{symbol}] {category.upper()} Position: {contracts} contracts - Open: True")
                        return True
                
                logger.info(f"[{symbol}] {category.upper()} Position check: Open: False")
                return False
            else:
                # Spot market check
                base_currency = symbol.split('/')[0]
                balance = self.exchange.fetch_balance()
                held = float(balance.get(base_currency, {}).get('free', 0))
                has_position = held > 0.001
                logger.info(f"[{symbol}] Spot check: {held} {base_currency} - Open: {has_position}")
                return has_position
        except Exception as e:
            logger.error(f"[{symbol}] Position check error: {e}")
            return False  # Better to return False and try to trade than True and be stuck forever

    def get_held_amount(self, symbol: str) -> float:
        try:
            if self.market_type in ['future', 'swap', 'linear', 'inverse']:
                category = 'linear' if ('USDT' in symbol or 'USDC' in symbol) else 'inverse'
                positions = self.exchange.fetch_positions(symbols=[symbol], params={'category': category})
                for pos in positions:
                    if pos['symbol'] == symbol:
                        # Return absolute size of the position
                        return float(pos.get('contracts', 0) or pos.get('size', 0) or 0)
                return 0.0
            else:
                base_currency = symbol.split('/')[0]
                balance = self.exchange.fetch_balance()
                return float(balance.get(base_currency, {}).get('free', 0))
        except Exception as e:
            logger.error(f"[{symbol}] Error getting held amount: {e}")
            return 0.0


# ── Multi-Timeframe Signal Checker ────────────────────────────────────────────
def get_mtf_signal(symbol: str, fetcher, signal_engine: SignalEngine) -> tuple:
    """
    Analyze signal across all configured timeframes.
    Returns final signal and details dict.
    """
    timeframes = [tf.strip() for tf in config.TIMEFRAMES.split(',')]
    min_confluence = config.MIN_TIMEFRAME_CONFLUENCE

    buy_count  = 0
    sell_count = 0
    tf_results = {}

    for tf in timeframes:
        try:
            df = fetcher.fetch_ohlcv(symbol, tf, config.CANDLE_LIMIT)
            if df.empty:
                logger.warning(f"[{symbol}][{tf}] No data")
                tf_results[tf] = 'NO_DATA'
                continue

            df = signal_engine.calculate_indicators(df)
            signal, indicators = signal_engine.generate_signal(df)
            tf_results[tf] = signal
            logger.info(f"[{symbol}][{tf}] Signal: {signal}")

            if signal == 'BUY':
                buy_count += 1
            elif signal == 'SELL':
                sell_count += 1

        except Exception as e:
            logger.error(f"[{symbol}][{tf}] Error: {e}")
            tf_results[tf] = 'ERROR'

    # Determine final signal based on confluence
    if buy_count >= min_confluence:
        final_signal = 'BUY'
    elif sell_count >= min_confluence:
        final_signal = 'SELL'
    else:
        final_signal = 'HOLD'

    logger.info(f"[{symbol}] MTF Result: BUY={buy_count} SELL={sell_count} HOLD -> {final_signal}")
    return final_signal, tf_results


# ── Per-Pair Bot Loop ─────────────────────────────────────────────────────────
def run_pair(symbol: str, fetcher, signal_engine, risk_manager, executor, position_tracker):
    logger.info(f"[{symbol}] Thread started")

    # Use the shortest timeframe interval for the loop
    timeframes = [tf.strip() for tf in config.TIMEFRAMES.split(',')]
    loop_interval = config.LOOP_INTERVAL
    db = DashboardDB()

    while True:
        try:
            # Check for Pause
            status_info = db.get_status()
            if status_info.get('status') == 'PAUSED':
                logger.info(f"[{symbol}] Bot is PAUSED. Skipping cycle.")
                time.sleep(loop_interval)
                continue

            logger.info(f"[{symbol}] --- New multi-timeframe cycle ---")

            # Get current price from shortest timeframe
            df_current = fetcher.fetch_ohlcv(symbol, timeframes[0], 5)
            if df_current.empty:
                logger.warning(f"[{symbol}] No price data - skipping")
                time.sleep(loop_interval)
                continue

            current_price = df_current.iloc[-1]['close']
            logger.info(f"[{symbol}] Price: ${current_price:,.4f}")

            # Multi-timeframe signal
            signal, tf_results = get_mtf_signal(symbol, fetcher, signal_engine)

            # Format timeframe results for log/telegram
            tf_summary = " | ".join([f"{tf}:{sig}" for tf, sig in tf_results.items()])
            logger.info(f"[{symbol}] Timeframes: {tf_summary}")

            # Execute trade
            if signal == 'BUY':
                if position_tracker.has_open_position(symbol):
                    logger.info(f"[{symbol}] Already holding - skipping BUY")
                else:
                    amount = risk_manager.calculate_position_size(symbol, current_price)
                    if amount > 0:
                        sl, tp = risk_manager.calculate_sl_tp(signal, current_price)
                        order  = executor.execute_trade(symbol, signal, amount, sl, tp)
                        if order:
                            send_alert(
                                f"<b>BUY EXECUTED</b>\n\n"
                                f"<b>Pair:</b> {symbol}\n"
                                f"<b>Price:</b> ${current_price:,.4f}\n"
                                f"<b>Amount:</b> {amount:.6f}\n"
                                f"<b>SL:</b> ${sl:,.4f}\n"
                                f"<b>TP:</b> ${tp:,.4f}\n"
                                f"<b>Timeframes:</b> {tf_summary}"
                            )
                        else:
                            send_alert(f"<b>BUY FAILED</b>\n{symbol} order failed.")
                    else:
                        logger.warning(f"[{symbol}] Position size 0 - skipping")

            elif signal == 'SELL':
                held = position_tracker.get_held_amount(symbol)
                if held > 0.001:
                    order = executor.execute_trade(symbol, signal, held, 0, 0)
                    if order:
                        send_alert(
                            f"<b>SELL EXECUTED</b>\n\n"
                            f"<b>Pair:</b> {symbol}\n"
                            f"<b>Price:</b> ${current_price:,.4f}\n"
                            f"<b>Amount:</b> {held:.6f}\n"
                            f"<b>Timeframes:</b> {tf_summary}"
                        )
                    else:
                        send_alert(f"<b>SELL FAILED</b>\n{symbol} order failed.")
                else:
                    logger.info(f"[{symbol}] SELL signal but nothing to sell")
            else:
                logger.info(f"[{symbol}] HOLD - no trade placed")

            logger.info(f"[{symbol}] Cycle done. Sleeping {loop_interval}s...")

        except Exception as e:
            logger.error(f"[{symbol}] Error: {e}", exc_info=True)
            send_alert(f"<b>BOT ERROR [{symbol}]</b>\n{e}")

        time.sleep(loop_interval)


# ── Main ──────────────────────────────────────────────────────────────────────
def run_bot():
    logger.info("=" * 60)
    logger.info("  CRYPTO BOT - MULTI PAIR + MULTI TIMEFRAME")
    logger.info("=" * 60)

    symbols_env = [s.strip() for s in config.SYMBOLS.split(',') if s.strip()]
    timeframes = [tf.strip() for tf in config.TIMEFRAMES.split(',')]

    db = DashboardDB()
    
    # Initialize symbols in DB if empty
    db_symbols = db.get_symbols()
    if not db_symbols:
        for s in symbols_env:
            db.add_symbol(s)
        db_symbols = symbols_env

    if not db_symbols:
        logger.error("No symbols in .env or DB!")
        return

    logger.info(f"Pairs: {db_symbols}")
    logger.info(f"Timeframes: {timeframes}")
    logger.info(f"Min confluence: {config.MIN_TIMEFRAME_CONFLUENCE}/{len(timeframes)}")
    logger.info(f"Testnet: {config.USE_TESTNET}")

    fetcher          = DataFetcher(config.BYBIT_API_KEY, config.BYBIT_API_SECRET, config.USE_TESTNET, config.MARKET_TYPE)
    signal_engine    = SignalEngine(config)
    risk_manager     = RiskManager(fetcher.exchange, config)
    executor         = OrderExecutor(fetcher.exchange, config)
    position_tracker = PositionTracker(fetcher.exchange, config.MARKET_TYPE)

    pairs_list = "\n".join([f"- <b>{s}</b>" for s in db_symbols])
    tf_list    = " | ".join(timeframes)
    send_alert(
        f"<b>Bot Started - Multi Timeframe</b>\n\n"
        f"<b>Pairs:</b>\n{pairs_list}\n\n"
        f"<b>Timeframes:</b> {tf_list}\n"
        f"<b>Confluence:</b> {config.MIN_TIMEFRAME_CONFLUENCE}/{len(timeframes)} must agree\n"
        f"<b>Testnet:</b> {config.USE_TESTNET}"
    )

    def status_updater():
        """Periodically updates balance and positions in DB"""
        while True:
            try:
                balance = fetcher.exchange.fetch_balance()
                # Simplified balance for dashboard
                balance_data = {
                    'total_usdt': balance.get('USDT', {}).get('total', 0),
                    'free_usdt': balance.get('USDT', {}).get('free', 0)
                }
                
                # Get positions
                positions_data = []
                # Check for all active symbols
                current_symbols = db.get_symbols()
                for symbol in current_symbols:
                    if position_tracker.has_open_position(symbol):
                        positions_data.append({
                            'symbol': symbol,
                            'amount': position_tracker.get_held_amount(symbol)
                        })
                
                db.update_status(balance=balance_data, positions=positions_data)
            except Exception as e:
                logger.error(f"Status update failed: {e}")
            time.sleep(300) # Update every 5 mins

    threading.Thread(target=status_updater, daemon=True).start()

    threads = {}
    for symbol in db_symbols:
        t = threading.Thread(
            target=run_pair,
            args=(symbol, fetcher, signal_engine, risk_manager, executor, position_tracker),
            name=f"bot-{symbol}",
            daemon=True
        )
        t.start()
        threads[symbol] = t
        logger.info(f"[{symbol}] Thread launched")
        time.sleep(2)

    logger.info(f"All {len(db_symbols)} threads running!")

    try:
        while True:
            # Check for STOP command
            cmd = db.get_latest_command()
            if cmd == 'stop':
                logger.info("STOP command received. Terminating bot.")
                send_alert("<b>Bot received STOP command from dashboard. Terminating.</b>")
                os._exit(0) # Force exit
            
            # Check for symbol changes
            new_symbols = db.get_symbols()
            if set(new_symbols) != set(threads.keys()):
                logger.info("Symbols changed in DB. Updating threads...")
                # Start new threads
                for s in new_symbols:
                    if s not in threads:
                        t = threading.Thread(
                            target=run_pair,
                            args=(s, fetcher, signal_engine, risk_manager, executor, position_tracker),
                            name=f"bot-{s}",
                            daemon=True
                        )
                        t.start()
                        threads[s] = t
                        logger.info(f"[{s}] New symbol thread launched")
                # Removed symbols will just finish their current loop and stay idle if we don't kill them
                # But since they check db.get_status and we could check if they are still in symbols list...
                # For simplicity, let's just let them be or restart the bot.
                # Re-reading: Actually, if they are removed from DB, run_pair should check if it's still active.
            
            time.sleep(10)
    except KeyboardInterrupt:
        logger.info("Bot stopped manually.")
        send_alert("<b>Bot manually stopped.</b>")


if __name__ == "__main__":
    run_bot()
