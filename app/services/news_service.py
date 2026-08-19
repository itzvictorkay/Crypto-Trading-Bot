"""
app/services/news_service.py
----------------------------
Service layer for fetching cryptocurrency news.
Supports retrieving articles/headlines from CryptoPanic API and NewsAPI.
Handles fallbacks and formats data cleanly for LangChain agents and sentiment analysis.
"""

import logging
from typing import List, Dict, Any, Optional
import requests
from datetime import datetime, timedelta
import config
from app.config_langchain import NEWS_API_KEY, CRYPTOPANIC_API_KEY, NEWS_API_ENABLED

logger = logging.getLogger(__name__)


class NewsService:
    """Service layer for fetching crypto news headlines and metadata."""

    def __init__(self):
        self.cryptopanic_key = CRYPTOPANIC_API_KEY or config.CRYPTOPANIC_KEY
        self.newsapi_key = NEWS_API_KEY
        self.enabled = NEWS_API_ENABLED
        logger.info("NewsService initialized")

    def fetch_news(self, coin: str, limit: int = 10) -> List[Dict[str, Any]]:
        """
        Fetch news articles for a coin, attempting CryptoPanic first, then falling back to NewsAPI.
        
        Args:
            coin: Coin identifier (e.g., 'BTC', 'ETH')
            limit: Maximum articles to return (default 10)
            
        Returns:
            List of dicts containing: title, source, url, published_at, summary
        """
        if not self.enabled:
            logger.info("News fetching is disabled in configuration.")
            return []

        articles = []
        
        # 1. Try CryptoPanic if key is available
        if self.cryptopanic_key:
            articles = self._fetch_from_cryptopanic(coin, limit)
            if articles:
                logger.info(f"Successfully fetched {len(articles)} articles from CryptoPanic for {coin}")
                return articles

        # 2. Try NewsAPI if no CryptoPanic articles or if key was missing
        if self.newsapi_key:
            articles = self._fetch_from_newsapi(coin, limit)
            if articles:
                logger.info(f"Successfully fetched {len(articles)} articles from NewsAPI for {coin}")
                return articles

        logger.warning(f"Could not fetch news for {coin} from any configured provider.")
        return []

    def _fetch_from_cryptopanic(self, coin: str, limit: int) -> List[Dict[str, Any]]:
        """Fetch headlines from CryptoPanic API."""
        try:
            url = f"https://cryptopanic.com/api/v1/posts/?auth_token={self.cryptopanic_key}&currencies={coin}&public=true"
            response = requests.get(url, timeout=10)
            
            if response.status_code != 200:
                logger.warning(f"CryptoPanic API returned status {response.status_code}")
                return []
                
            data = response.json()
            results = data.get('results', [])[:limit]
            
            articles = []
            for post in results:
                # Format to a standard structure
                articles.append({
                    "title": post.get("title", ""),
                    "source": post.get("source", {}).get("title", "CryptoPanic"),
                    "url": post.get("url", ""),
                    "published_at": post.get("published_at", ""),
                    "summary": post.get("title", "") # CryptoPanic primarily provides titles
                })
            return articles
        except Exception as e:
            logger.error(f"Error fetching from CryptoPanic: {e}")
            return []

    def _fetch_from_newsapi(self, coin: str, limit: int) -> List[Dict[str, Any]]:
        """Fetch news from NewsAPI (everything endpoint)."""
        try:
            # Query recent news (last 7 days)
            from_date = (datetime.now() - timedelta(days=7)).strftime('%Y-%m-%d')
            query = f"{coin} AND crypto"
            url = f"https://newsapi.org/v2/everything?q={query}&from={from_date}&sortBy=publishedAt&pageSize={limit}&apiKey={self.newsapi_key}"
            
            response = requests.get(url, timeout=10)
            
            if response.status_code != 200:
                logger.warning(f"NewsAPI returned status {response.status_code}")
                return []
                
            data = response.json()
            articles_raw = data.get('articles', [])[:limit]
            
            articles = []
            for art in articles_raw:
                articles.append({
                    "title": art.get("title", ""),
                    "source": art.get("source", {}).get("name", "NewsAPI"),
                    "url": art.get("url", ""),
                    "published_at": art.get("publishedAt", ""),
                    "summary": art.get("description", art.get("title", ""))
                })
            return articles
        except Exception as e:
            logger.error(f"Error fetching from NewsAPI: {e}")
            return []
