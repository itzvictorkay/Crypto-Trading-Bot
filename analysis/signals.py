"""
analysis/signals.py
--------------------
Technical analysis engine with:
- RSI, EMA crossover, MACD, Bollinger Bands
- 200 EMA trend filter
- Volume confirmation
- Claude AI sentiment analysis
"""

import pandas as pd
import pandas_ta as ta
import logging
import requests
import anthropic
import os

logger = logging.getLogger(__name__)


def get_claude_sentiment(coin: str = "BTC", cryptopanic_key: str = "") -> str:
    try:
        headlines = []
        if cryptopanic_key:
            url = f"https://cryptopanic.com/api/v1/posts/?auth_token={cryptopanic_key}&currencies={coin}&public=true"
            response = requests.get(url, timeout=10)
            if response.status_code == 200:
                data = response.json()
                headlines = [p['title'] for p in data.get('results', [])[:10]]
        if not headlines:
            return "NEUTRAL"
        news_text = "\n".join(headlines)
        client = anthropic.Anthropic(api_key=os.getenv("ANTHROPIC_API_KEY", ""))
        message = client.messages.create(
            model="claude-sonnet-4-20250514",
            max_tokens=50,
            messages=[{"role": "user", "content": f"You are a crypto analyst. Read these {coin} headlines and reply with ONE word only: POSITIVE, NEGATIVE, or NEUTRAL.\n\n{news_text}"}]
        )
        sentiment = message.content[0].text.strip().upper()
        return sentiment if sentiment in ["POSITIVE", "NEGATIVE", "NEUTRAL"] else "NEUTRAL"
    except Exception as e:
        logger.error(f"Sentiment error: {e}")
        return "NEUTRAL"


class SignalEngine:
    def __init__(self, config):
        self.config = config

    def calculate_indicators(self, df: pd.DataFrame) -> pd.DataFrame:
        """Calculate all technical indicators with robust column name handling."""
        try:
            # RSI
            df['rsi'] = ta.rsi(df['close'], length=self.config.RSI_PERIOD)

            # EMAs
            df['ema_fast'] = ta.ema(df['close'], length=self.config.EMA_FAST)
            df['ema_slow'] = ta.ema(df['close'], length=self.config.EMA_SLOW)
            df['ema_200']  = ta.ema(df['close'], length=200)

            # MACD
            macd = ta.macd(
                df['close'],
                fast=self.config.MACD_FAST,
                slow=self.config.MACD_SLOW,
                signal=self.config.MACD_SIGNAL
            )
            df['macd']        = macd[f'MACD_{self.config.MACD_FAST}_{self.config.MACD_SLOW}_{self.config.MACD_SIGNAL}']
            df['macd_signal'] = macd[f'MACDs_{self.config.MACD_FAST}_{self.config.MACD_SLOW}_{self.config.MACD_SIGNAL}']

            # Bollinger Bands — handle both int and float std column names
            bb_std = self.config.BB_STD
            bb = ta.bbands(df['close'], length=self.config.BB_PERIOD, std=bb_std)

            # Try different column name formats pandas_ta might use
            std_str_options = [
                str(bb_std),                          # "2.0"
                str(int(bb_std)) if bb_std == int(bb_std) else str(bb_std),  # "2"
            ]
            bb_upper_col = None
            bb_lower_col = None
            for std_str in std_str_options:
                upper_key = f'BBU_{self.config.BB_PERIOD}_{std_str}'
                lower_key = f'BBL_{self.config.BB_PERIOD}_{std_str}'
                if upper_key in bb.columns:
                    bb_upper_col = upper_key
                    bb_lower_col = lower_key
                    break

            if bb_upper_col:
                df['bb_upper'] = bb[bb_upper_col]
                df['bb_lower'] = bb[bb_lower_col]
            else:
                # fallback: just grab first BBU and BBL columns
                bbu_cols = [c for c in bb.columns if c.startswith('BBU_')]
                bbl_cols = [c for c in bb.columns if c.startswith('BBL_')]
                if bbu_cols and bbl_cols:
                    df['bb_upper'] = bb[bbu_cols[0]]
                    df['bb_lower'] = bb[bbl_cols[0]]
                else:
                    # last resort: calculate manually
                    rolling_mean = df['close'].rolling(self.config.BB_PERIOD).mean()
                    rolling_std  = df['close'].rolling(self.config.BB_PERIOD).std()
                    df['bb_upper'] = rolling_mean + (rolling_std * bb_std)
                    df['bb_lower'] = rolling_mean - (rolling_std * bb_std)

            # Volume average
            df['avg_volume'] = df['volume'].rolling(20).mean()

            logger.info("All indicators calculated successfully.")
        except Exception as e:
            logger.error(f"Error calculating indicators: {e}")
        return df

    def generate_signal(self, df: pd.DataFrame):
        """Generate BUY, SELL, or HOLD signal."""
        last = df.iloc[-1]
        buy_signals  = 0
        sell_signals = 0
        indicators   = {}

        try:
            # ── Volume Confirmation ──────────────────────────────
            avg_vol = last.get('avg_volume', None)
            if self.config.DISABLE_VOLUME_FILTER:
                logger.info("Volume filter is disabled.")
            elif avg_vol is None or pd.isna(avg_vol):
                logger.warning("avg_volume not available yet - skipping volume check")
            elif last['volume'] < avg_vol * self.config.VOLUME_THRESHOLD_PCT:
                logger.warning(f"Volume too low ({last['volume']} < {avg_vol * self.config.VOLUME_THRESHOLD_PCT}) - skipping signal.")
                return 'HOLD', {'reason': 'low_volume'}

            # ── 200 EMA Trend Filter ─────────────────────────────
            ema_200 = last.get('ema_200', None)
            above_200 = (last['close'] > ema_200) if (ema_200 and not pd.isna(ema_200)) else True
            indicators['trend'] = 'UP' if above_200 else 'DOWN'
            if ema_200 and not pd.isna(ema_200):
                indicators['ema_200'] = round(ema_200, 4)

            # ── RSI ───────────────────────────────────────────────
            rsi = last.get('rsi', None)
            if rsi and not pd.isna(rsi):
                indicators['rsi'] = round(rsi, 2)
                if rsi < self.config.RSI_OVERSOLD:
                    buy_signals += 1
                elif rsi > self.config.RSI_OVERBOUGHT:
                    sell_signals += 1

            # ── EMA Crossover ─────────────────────────────────────
            ema_fast = last.get('ema_fast', None)
            ema_slow = last.get('ema_slow', None)
            if ema_fast and ema_slow and not pd.isna(ema_fast) and not pd.isna(ema_slow):
                indicators['ema_fast'] = round(ema_fast, 4)
                indicators['ema_slow'] = round(ema_slow, 4)
                if ema_fast > ema_slow:
                    buy_signals += 1
                else:
                    sell_signals += 1

            # ── MACD ──────────────────────────────────────────────
            macd       = last.get('macd', None)
            macd_sig   = last.get('macd_signal', None)
            if macd and macd_sig and not pd.isna(macd) and not pd.isna(macd_sig):
                indicators['macd']        = round(macd, 4)
                indicators['macd_signal'] = round(macd_sig, 4)
                if macd > macd_sig:
                    buy_signals += 1
                else:
                    sell_signals += 1

            # ── Bollinger Bands ───────────────────────────────────
            bb_upper = last.get('bb_upper', None)
            bb_lower = last.get('bb_lower', None)
            if bb_upper and bb_lower and not pd.isna(bb_upper) and not pd.isna(bb_lower):
                indicators['bb_upper'] = round(bb_upper, 4)
                indicators['bb_lower'] = round(bb_lower, 4)
                if last['close'] < bb_lower:
                    buy_signals += 1
                elif last['close'] > bb_upper:
                    sell_signals += 1

            logger.info(f"Buy: {buy_signals} | Sell: {sell_signals} | Trend: {indicators.get('trend')}")

            # ── Confluence Check ──────────────────────────────────
            raw_signal = 'HOLD'
            trend_allows_buy = above_200 or not self.config.USE_TREND_FILTER
            trend_allows_sell = not above_200 or not self.config.USE_TREND_FILTER

            if buy_signals >= self.config.MIN_SIGNAL_CONFLUENCE and trend_allows_buy:
                raw_signal = 'BUY'
            elif sell_signals >= self.config.MIN_SIGNAL_CONFLUENCE and trend_allows_sell:
                raw_signal = 'SELL'

            if raw_signal == 'HOLD':
                return 'HOLD', indicators

            # ── Sentiment Filter ──────────────────────────────────
            if os.getenv("ANTHROPIC_API_KEY") and os.getenv("CRYPTOPANIC_KEY"):
                coin = self.config.SYMBOL.split('/')[0]
                sentiment = get_claude_sentiment(coin, os.getenv("CRYPTOPANIC_KEY", ""))
                indicators['sentiment'] = sentiment
                if raw_signal == 'BUY' and sentiment == 'NEGATIVE':
                    return 'HOLD', indicators
                if raw_signal == 'SELL' and sentiment == 'POSITIVE':
                    return 'HOLD', indicators

            return raw_signal, indicators

        except Exception as e:
            logger.error(f"Signal generation error: {e}")
            return 'HOLD', indicators
