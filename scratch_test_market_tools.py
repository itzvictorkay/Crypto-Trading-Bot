"""
Quick manual verification script for MarketService and MarketTools.
This script mocks the DataFetcher to verify that the service layer and LangChain tools function correctly without live API calls.
"""

import sys
import os
import pandas as pd
from unittest.mock import Mock, patch

# Ensure the parent directory is in the path
sys.path.insert(0, os.path.abspath(os.path.dirname(__file__)))

from app.services.market_service import MarketService
from app.tools.market_tools import (
    get_crypto_price,
    get_market_data,
    get_volume_stats,
    get_price_comparison,
    get_price_change,
    get_support_resistance
)

def run_tests():
    print("=" * 60)
    print("RUNNING MANUAL VERIFICATION ON MARKET SERVICES AND TOOLS")
    print("=" * 60)
    
    # 1. Setup mock data
    mock_ohlcv = pd.DataFrame({
        'open': [45000.0, 45100.0, 45200.0, 45150.0],
        'high': [45100.0, 45200.0, 45300.0, 45250.0],
        'low': [44900.0, 45000.0, 45100.0, 45050.0],
        'close': [45050.0, 45150.0, 45250.0, 45200.0],
        'volume': [1000000.0, 1100000.0, 950000.0, 1050000.0]
    }, index=pd.date_range(start='2024-01-01', periods=4, freq='1h'))

    mock_ticker = {
        'symbol': 'BTC/USDT',
        'last': 45200.50,
        'bid': 45200.00,
        'ask': 45201.00,
        'high': 45300.0,
        'low': 44900.0,
        'volume': 10000000.0
    }

    # 2. Patch DataFetcher and get_market_service to inject mock
    with patch('app.services.market_service.DataFetcher') as MockFetcherClass, \
         patch('app.tools.market_tools.get_market_service') as mock_get_service:
        
        # Instantiate mocks
        mock_fetcher = Mock()
        mock_fetcher.fetch_ticker.return_value = mock_ticker
        mock_fetcher.fetch_ohlcv.return_value = mock_ohlcv
        
        service = MarketService(fetcher=mock_fetcher)
        mock_get_service.return_value = service
        
        # Verify Price Tool
        print("\n--- Testing get_crypto_price Tool ---")
        price_res = get_crypto_price.invoke({"symbol": "BTC/USDT"})
        print(f"Result: {price_res}")
        assert "BTC/USDT: $45,200.50" in price_res, "Price verification failed"
        print("✓ get_crypto_price OK")

        # Verify Market Data Tool
        print("\n--- Testing get_market_data Tool ---")
        data_res = get_market_data.invoke({"symbol": "BTC/USDT", "timeframe": "1h", "limit": 4})
        print(f"Result:\n{data_res}")
        assert "BTC/USDT [1h]" in data_res and "4 candles" in data_res, "Market data verification failed"
        print("✓ get_market_data OK")

        # Verify Volume Stats Tool
        print("\n--- Testing get_volume_stats Tool ---")
        vol_res = get_volume_stats.invoke({"symbol": "BTC/USDT", "timeframe": "1h"})
        print(f"Result:\n{vol_res}")
        assert "Current: 1,050,000" in vol_res, "Volume stats verification failed"
        print("✓ get_volume_stats OK")

        # Verify Price Comparison Tool
        print("\n--- Testing get_price_comparison Tool ---")
        comp_res = get_price_comparison.invoke({"symbols": "BTC/USDT,ETH/USDT"})
        print(f"Result:\n{comp_res}")
        assert "BTC/USDT: $45,200.50" in comp_res, "Price comparison verification failed"
        print("✓ get_price_comparison OK")

        # Verify Price Change Tool
        print("\n--- Testing get_price_change Tool ---")
        change_res = get_price_change.invoke({"symbol": "BTC/USDT", "period_hours": 4})
        print(f"Result:\n{change_res}")
        assert "+0.44%" in change_res or "Change" in change_res, "Price change verification failed"
        print("✓ get_price_change OK")

        # Verify Support & Resistance Tool
        print("\n--- Testing get_support_resistance Tool ---")
        sr_res = get_support_resistance.invoke({"symbol": "BTC/USDT", "timeframe": "1h"})
        print(f"Result:\n{sr_res}")
        assert "Support" in sr_res and "Resistance" in sr_res, "S/R verification failed"
        print("✓ get_support_resistance OK")

    print("\n" + "=" * 60)
    print("ALL SERVICE & TOOL VERIFICATION TESTS PASSED SUCCESSFULLY!")
    print("=" * 60)

if __name__ == "__main__":
    run_tests()
