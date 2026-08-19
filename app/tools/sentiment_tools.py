"""
app/tools/sentiment_tools.py
-----------------------------
LangChain tools for sentiment analysis.
These tools allow the AI agent to run sentiment classification on crypto news.
"""

import logging
from langchain_core.tools import tool

from app.services.sentiment_service import SentimentService

logger = logging.getLogger(__name__)

# Module-level service instance
_sentiment_service = None


def get_sentiment_service() -> SentimentService:
    """Get or create SentimentService instance."""
    global _sentiment_service
    if _sentiment_service is None:
        _sentiment_service = SentimentService()
    return _sentiment_service


@tool
def analyze_news_sentiment(coin: str, headlines: str) -> str:
    """
    Analyze the sentiment of a list of news headlines for a specific coin.
    
    Args:
        coin: The cryptocurrency coin symbol (e.g., 'BTC', 'ETH', 'SOL')
        headlines: Semicolon-separated list of news headlines (e.g., 'BTC hits new ATH; regulator issues warning')
    
    Returns:
        Sentiment classification report string
    """
    try:
        if not headlines.strip():
            return f"Error: No headlines provided for {coin} sentiment analysis."
            
        headline_list = [h.strip() for h in headlines.split(';') if h.strip()]
        
        service = get_sentiment_service()
        result = service.analyze_headlines(coin, headline_list)
        
        emoji = "📈" if result["sentiment"] == "POSITIVE" else ("📉" if result["sentiment"] == "NEGATIVE" else "➡️")
        
        report = (
            f"=== Sentiment Analysis Report: {coin} ===\n"
            f"Overall Sentiment: {emoji} {result['sentiment']} (Confidence: {result['confidence']*100:.1f}%)\n"
            f"Reasoning: {result['reasoning']}\n"
            f"Sentiment Distribution:\n"
            f"  - Positive: {result['positive_score']*100:.1f}%\n"
            f"  - Neutral: {result['neutral_score']*100:.1f}%\n"
            f"  - Negative: {result['negative_score']*100:.1f}%"
        )
        
        return report
    except Exception as e:
        logger.error(f"Error in analyze_news_sentiment tool: {e}")
        return f"Error analyzing news sentiment: {str(e)}"


# Export tools for registration
SENTIMENT_TOOLS = [
    analyze_news_sentiment,
]
