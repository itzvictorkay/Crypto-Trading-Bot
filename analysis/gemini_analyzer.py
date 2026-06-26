import logging
import json
import os
from google import genai
from google.genai import types

logger = logging.getLogger(__name__)

class GeminiAnalyzer:
    def __init__(self, api_key: str):
        self.client = genai.Client(api_key=api_key)
        self.model_id = "gemini-2.0-flash"

    def analyze_trade(self, symbol: str, timeframe: str, df_last_5: str, indicators: dict) -> dict:
        """
        Send technical data to Gemini for analysis.
        Returns a dict with 'signal', 'confidence', and 'reasoning'.
        """
        try:
            prompt = f"""
You are a Senior Crypto Quantitative Trader. Analyze the following data for {symbol} on the {timeframe} timeframe and decide if we should enter a trade.

LAST 5 CANDLES (OHLCV):
{df_last_5}

TECHNICAL INDICATORS:
{json.dumps(indicators, indent=2)}

TASK:
1. Identify the current market structure (support/resistance, trend).
2. Evaluate the confluence of indicators.
3. Provide a trade recommendation: BUY, SELL, or HOLD.
4. Assign a confidence score from 0 to 100.
5. Provide a short reasoning.

RESPONSE FORMAT (JSON ONLY):
{{
  "signal": "BUY" | "SELL" | "HOLD",
  "confidence": 85,
  "reasoning": "Explain why...",
  "target_price": 12345.67
}}
"""
            response = self.client.models.generate_content(
                model=self.model_id,
                contents=prompt,
                config=types.GenerateContentConfig(
                    response_mime_type="application/json",
                ),
            )
            
            result = json.loads(response.text)
            logger.info(f"Gemini Analysis for {symbol}: {result.get('signal')} (Conf: {result.get('confidence')}%)")
            return result
        except Exception as e:
            logger.error(f"Gemini Analysis Error: {e}")
            return {"signal": "HOLD", "confidence": 0, "reasoning": str(e)}
