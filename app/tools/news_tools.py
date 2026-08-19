"""
app/tools/news_tools.py
-----------------------
LangChain tools for fetching cryptocurrency news.
These tools allow the AI agent to search and retrieve recent news headlines.
"""

import logging
from langchain_core.tools import tool

from app.services.news_service import NewsService

logger = logging.getLogger(__name__)

# Module-level service instance
_news_service = None


def get_news_service() -> NewsService:
    """Get or create NewsService instance."""
    global _news_service
    if _news_service is None:
        _news_service = NewsService()
    return _news_service


@tool
def search_crypto_news(symbol: str, limit: int = 10) -> str:
    """
    Search and retrieve recent news articles and headlines for a cryptocurrency.
    
    Args:
        symbol: Cryptocurrency symbol or coin name (e.g. 'BTC/USDT', 'BTC', 'ETH')
        limit: Number of news articles to fetch (max 20, default 10)
    
    Returns:
        A list of formatted headlines, sources, and publication dates
    """
    try:
        # Handle cases where user inputs a full trading pair like 'BTC/USDT'
        coin = symbol.split('/')[0].strip().upper()
        
        if limit > 20:
            limit = 20
        if limit < 1:
            return "Error: limit must be at least 1"
            
        service = get_news_service()
        articles = service.fetch_news(coin, limit=limit)
        
        if not articles:
            return f"No recent news found for {coin}. Please ensure your API keys (NewsAPI or CryptoPanic) are configured in .env."
            
        formatted_list = []
        for i, art in enumerate(articles, 1):
            published = art['published_at']
            # Format timestamp for better readability if possible
            try:
                dt = published.split('T')[0]
            except Exception:
                dt = published
                
            formatted_list.append(
                f"{i}. \"{art['title']}\"\n"
                f"   Source: {art['source']} | Date: {dt}\n"
                f"   URL: {art['url']}"
            )
            
        header = f"=== Recent News for {coin} ===\n"
        return header + "\n\n".join(formatted_list)
        
    except Exception as e:
        logger.error(f"Error in search_crypto_news tool: {e}")
        return f"Error retrieving news for {symbol}: {str(e)}"


# Export tools for registration
NEWS_TOOLS = [
    search_crypto_news,
]
