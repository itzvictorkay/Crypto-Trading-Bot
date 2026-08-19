"""
Phase 3 Market Tools Demo
Demonstrates market tools working with mocked data.
This shows how Claude will use these tools in Phase 9.
"""

from unittest.mock import Mock, patch
import pandas as pd
from app.tools.market_tools import (
    get_crypto_price,
    get_market_data,
    get_volume_stats,
    get_price_comparison,
    get_price_change,
    get_support_resistance,
)


def demo_market_tools():
    """Demonstrate all market tools with mocked data."""
    
    print("\n" + "="*70)
    print("PHASE 3: MARKET TOOLS DEMO")
    print("="*70 + "\n")
    
    # Create mock market data
    mock_ohlcv = pd.DataFrame({
        'open': [45000, 45100, 45200, 45150],
        'high': [45100, 45200, 45300, 45250],
        'low': [44900, 45000, 45100, 45050],
        'close': [45050, 45150, 45250, 45200],
        'volume': [1000000, 1100000, 950000, 1050000]
    }, index=pd.date_range(start='2024-01-01', periods=4, freq='1h'))
    
    mock_ticker = {
        'symbol': 'BTC/USDT',
        'last': 45200.50,
        'bid': 45200.00,
        'ask': 45201.00,
    }
    
    # Mock the market service
    with patch('app.tools.market_tools.get_market_service') as mock_svc_getter:
        mock_service = Mock()
        mock_service.get_current_price.return_value = 45200.50
        mock_service.get_market_data.return_value = mock_ohlcv
        mock_service.get_volume_stats.return_value = {
            'symbol': 'BTC/USDT',
            'timeframe': '1h',
            'average_volume': 1025000,
            'max_volume': 1100000,
            'min_volume': 950000,
            'current_volume': 1050000,
            'total_volume': 4100000,
            'timestamp': '2024-01-01T12:00:00'
        }
        mock_service.get_price_comparison.return_value = {
            'BTC/USDT': 45200.50,
            'ETH/USDT': 2465.25,
            'SOL/USDT': 185.75
        }
        mock_service.get_price_change.return_value = {
            'symbol': 'BTC/USDT',
            'period_hours': 24,
            'open_price': 44800,
            'close_price': 45200,
            'high_price': 45300,
            'low_price': 44700,
            'change': 400,
            'percent_change': 0.893,
            'timestamp': '2024-01-01T12:00:00'
        }
        mock_service.get_support_resistance.return_value = {
            'symbol': 'BTC/USDT',
            'timeframe': '1h',
            'support': 44950,
            'pivot': 45125,
            'resistance': 45300,
            'current_price': 45200,
            'timestamp': '2024-01-01T12:00:00'
        }
        
        mock_svc_getter.return_value = mock_service
        
        # 1. Get crypto price
        print("1️⃣  GET CRYPTO PRICE")
        print("-" * 70)
        result = get_crypto_price.invoke({'symbol': 'BTC/USDT'})
        print(result)
        
        # 2. Get market data
        print("\n2️⃣  GET MARKET DATA")
        print("-" * 70)
        result = get_market_data.invoke({'symbol': 'BTC/USDT', 'timeframe': '1h', 'limit': 4})
        print(result)
        
        # 3. Get volume stats
        print("\n3️⃣  GET VOLUME STATS")
        print("-" * 70)
        result = get_volume_stats.invoke({'symbol': 'BTC/USDT', 'timeframe': '1h'})
        print(result)
        
        # 4. Get price comparison
        print("\n4️⃣  GET PRICE COMPARISON")
        print("-" * 70)
        result = get_price_comparison.invoke({'symbols': 'BTC/USDT,ETH/USDT,SOL/USDT'})
        print(result)
        
        # 5. Get price change
        print("\n5️⃣  GET PRICE CHANGE")
        print("-" * 70)
        result = get_price_change.invoke({'symbol': 'BTC/USDT', 'period_hours': 24})
        print(result)
        
        # 6. Get support/resistance
        print("\n6️⃣  GET SUPPORT/RESISTANCE")
        print("-" * 70)
        result = get_support_resistance.invoke({'symbol': 'BTC/USDT', 'timeframe': '1h'})
        print(result)
    
    # Show tool registry
    print("\n" + "="*70)
    print("TOOL REGISTRY STATUS")
    print("="*70)
    
    from app.tools import get_registry
    registry = get_registry()
    
    print(f"\n✓ Total tools registered: {len(registry.get_names())}")
    print("\nRegistered tools:")
    for name in sorted(registry.get_names()):
        tool = registry.get(name)
        print(f"  • {name}")
        print(f"    └─ {tool.description.split(chr(10))[0]}")
    
    print("\n" + "="*70)
    print("✅ PHASE 3 COMPLETE")
    print("="*70)
    print("\nWhat's next:")
    print("  • Phase 4: Technical Tools (RSI, MACD, EMA, Bollinger Bands)")
    print("  • Phase 5: Sentiment Analysis Tools")
    print("  • Phase 6: News Retrieval Tools")
    print("  • Phase 9: Multi-Agent System with Market Agent")
    print()


if __name__ == '__main__':
    demo_market_tools()
