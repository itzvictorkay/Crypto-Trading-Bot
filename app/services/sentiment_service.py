"""
app/services/sentiment_service.py
---------------------------------
Service layer for news sentiment analysis.
Uses the configured LangChain LLM provider (Claude 3.5 Sonnet) to analyze
crypto news headlines and return structured sentiment classifications.
"""

import logging
from typing import Dict, Any, List, Optional
from langchain_core.prompts import ChatPromptTemplate
from langchain_core.output_parsers import JsonOutputParser
from pydantic import BaseModel, Field

from app.llm_provider import get_llm

logger = logging.getLogger(__name__)


class SentimentAnalysisResult(BaseModel):
    sentiment: str = Field(description="The overall sentiment: POSITIVE, NEGATIVE, or NEUTRAL")
    confidence: float = Field(description="Confidence score from 0.0 to 1.0")
    reasoning: str = Field(description="Brief explanation of the sentiment assessment")
    positive_score: float = Field(description="Score for positive sentiment (0.0 to 1.0)")
    negative_score: float = Field(description="Score for negative sentiment (0.0 to 1.0)")
    neutral_score: float = Field(description="Score for neutral sentiment (0.0 to 1.0)")


class SentimentService:
    """Service layer for analyzing cryptocurrency market sentiment."""

    def __init__(self, llm=None):
        """
        Initialize SentimentService.
        
        Args:
            llm: Optional LangChain LLM instance. If None, uses default provider.
        """
        try:
            self.llm = llm or get_llm()
        except Exception as e:
            logger.warning(f"Could not load default LLM for SentimentService: {e}. Falling back to lazy-loading.")
            self.llm = None
            
        self.parser = JsonOutputParser(pydantic_object=SentimentAnalysisResult)
        
        self.prompt_template = ChatPromptTemplate.from_messages([
            ("system", 
             "You are an expert Cryptocurrency Analyst and Sentiment Specialist. "
             "Analyze the news headlines or articles provided for the given coin and classify the market sentiment.\n"
             "You must return your output strictly in JSON format matching the schema instructions:\n{format_instructions}"),
            ("user", 
             "Coin: {coin}\n\n"
             "News Headlines/Content:\n{news_text}\n\n"
             "Analyze the sentiment for {coin} based only on the headlines provided.")
        ])
        
        logger.info("SentimentService initialized")

    def _get_llm(self):
        """Lazy-load LLM if not initialized in __init__."""
        if self.llm is None:
            self.llm = get_llm()
        return self.llm

    def analyze_headlines(self, coin: str, headlines: List[str]) -> Dict[str, Any]:
        """
        Analyze sentiment of a list of news headlines.
        
        Args:
            coin: Cryptocurrency token name (e.g. 'BTC', 'ETH')
            headlines: List of headline strings
            
        Returns:
            Dict matching the SentimentAnalysisResult schema
        """
        if not headlines:
            logger.info(f"No headlines provided for {coin} sentiment analysis. Returning NEUTRAL.")
            return {
                "sentiment": "NEUTRAL",
                "confidence": 1.0,
                "reasoning": "No headlines provided.",
                "positive_score": 0.0,
                "negative_score": 0.0,
                "neutral_score": 1.0
            }
            
        try:
            llm = self._get_llm()
            news_text = "\n".join([f"- {h}" for h in headlines])
            
            chain = self.prompt_template | llm | self.parser
            
            logger.info(f"Running sentiment analysis for {coin} over {len(headlines)} headlines")
            result = chain.invoke({
                "coin": coin,
                "news_text": news_text,
                "format_instructions": self.parser.get_format_instructions()
            })
            
            # Format validation
            sentiment = str(result.get("sentiment", "NEUTRAL")).upper().strip()
            if sentiment not in ["POSITIVE", "NEGATIVE", "NEUTRAL"]:
                result["sentiment"] = "NEUTRAL"
            else:
                result["sentiment"] = sentiment
                
            logger.info(f"Sentiment for {coin}: {result['sentiment']} (Conf: {result['confidence']:.2f})")
            return result
            
        except Exception as e:
            logger.error(f"Error in SentimentService.analyze_headlines: {e}", exc_info=True)
            return {
                "sentiment": "NEUTRAL",
                "confidence": 0.0,
                "reasoning": f"Sentiment analysis failed: {str(e)}",
                "positive_score": 0.0,
                "negative_score": 0.0,
                "neutral_score": 1.0
            }
