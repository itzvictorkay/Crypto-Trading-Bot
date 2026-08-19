"""
tests/test_market_tools.py
--------------------------
Unit tests for market tools and MarketService.
Uses mocked CCXT data to avoid live API calls.
"""

import pytest
import pandas as pd
from unittest.mock import Mock, MagicMock, patch
from datetime import datetime

from app.services.market_service import MarketService
from app.tools import market_tools


# Mock data fixtures
@pytest.fixture
def mock_ohlcv_data():
    """Create mock OHLCV data."""
    return pd.DataFrame({
        'open': [45000, 45100, 45200, 45150],
        'high': [45100, 45200, 45300, 45250],
        'low': [44900, 45000, 45100, 45050],
        'close': [45050, 45150, 45250, 45200],
        'volume': [1000000, 1100000, 950000, 1050000]
    }, index=pd.date_range(start='2024-01-01', periods=4, freq='1h'))


@pytest.fixture
def mock_ticker_data():
    """Create mock ticker data."""
    return {
        'symbol': 'BTC/USDT',
        'last': 45200.50,
        'bid': 45200.00,
        'ask': 45201.00,
        'high': 45300,
        'low': 44900,
        'volume': 10000000
    }


@pytest.fixture
def mock_fetcher():
    """Create a mocked DataFetcher."""
    fetcher = Mock()
    return fetcher


@pytest.fixture
def market_service_with_mock(mock_fetcher):
    """Create MarketService with mocked fetcher."""
    return MarketService(fetcher=mock_fetcher)


class TestMarketService:
    """Tests for MarketService class."""
    
    def test_get_current_price_success(self, market_service_with_mock, mock_fetcher, mock_ticker_data):
        """Test successful price fetch."""
        mock_fetcher.fetch_ticker.return_value = mock_ticker_data
        
        price = market_service_with_mock.get_current_price('BTC/USDT')
        
        assert price == 45200.50
        mock_fetcher.fetch_ticker.assert_called_once_with('BTC/USDT')
    
    def test_get_current_price_no_data(self, market_service_with_mock, mock_fetcher):
        """Test price fetch with missing data."""
        mock_fetcher.fetch_ticker.return_value = {}
        
        price = market_service_with_mock.get_current_price('BTC/USDT')
        
        assert price is None
    
    def test_get_current_price_exception(self, market_service_with_mock, mock_fetcher):
        """Test price fetch with exception."""
        mock_fetcher.fetch_ticker.side_effect = Exception("Network error")
        
        price = market_service_with_mock.get_current_price('BTC/USDT')
        
        assert price is None
    
    def test_get_market_data_success(self, market_service_with_mock, mock_fetcher, mock_ohlcv_data):
        """Test successful market data fetch."""
        mock_fetcher.fetch_ohlcv.return_value = mock_ohlcv_data
        
        df = market_service_with_mock.get_market_data('BTC/USDT', timeframe='1h', limit=100)
        
        assert isinstance(df, pd.DataFrame)
        assert len(df) == 4
        assert 'close' in df.columns
        mock_fetcher.fetch_ohlcv.assert_called_once_with('BTC/USDT', timeframe='1h', limit=100)
    
    def test_get_market_data_exceeds_limit(self, market_service_with_mock, mock_fetcher, mock_ohlcv_data):
        """Test market data fetch with limit exceeded."""
        mock_fetcher.fetch_ohlcv.return_value = mock_ohlcv_data
        
        df = market_service_with_mock.get_market_data('BTC/USDT', limit=2000)
        
        # Should cap at 1000
        mock_fetcher.fetch_ohlcv.assert_called_once()
        args = mock_fetcher.fetch_ohlcv.call_args
        assert args[1]['limit'] == 1000
    
    def test_get_market_data_empty(self, market_service_with_mock, mock_fetcher):
        """Test market data fetch with empty result."""
        mock_fetcher.fetch_ohlcv.return_value = pd.DataFrame()
        
        df = market_service_with_mock.get_market_data('INVALID/USDT')
        
        assert df is None
    
    def test_get_volume_stats(self, market_service_with_mock, mock_fetcher, mock_ohlcv_data):
        """Test volume statistics calculation."""
        mock_fetcher.fetch_ohlcv.return_value = mock_ohlcv_data
        
        stats = market_service_with_mock.get_volume_stats('BTC/USDT')
        
        assert stats is not None
        assert stats['symbol'] == 'BTC/USDT'
        assert stats['average_volume'] == pytest.approx(1025000, rel=0.01)
        assert stats['max_volume'] == 1100000
        assert stats['min_volume'] == 950000
        assert stats['current_volume'] == 1050000
    
    def test_get_price_comparison(self, market_service_with_mock, mock_fetcher, mock_ticker_data):
        """Test price comparison for multiple symbols."""
        mock_fetcher.fetch_ticker.return_value = mock_ticker_data
        
        prices = market_service_with_mock.get_price_comparison(['BTC/USDT', 'ETH/USDT'])
        
        assert prices is not None
        assert 'BTC/USDT' in prices
        assert 'ETH/USDT' in prices
        assert prices['BTC/USDT'] == 45200.50
    
    def test_get_price_comparison_no_data(self, market_service_with_mock, mock_fetcher):
        """Test price comparison with no data."""
        mock_fetcher.fetch_ticker.return_value = {}
        
        prices = market_service_with_mock.get_price_comparison(['INVALID/USDT'])
        
        assert prices is None
    
    def test_get_price_change(self, market_service_with_mock, mock_fetcher, mock_ohlcv_data):
        """Test price change calculation."""
        mock_fetcher.fetch_ohlcv.return_value = mock_ohlcv_data
        
        change = market_service_with_mock.get_price_change('BTC/USDT', period_hours=4)
        
        assert change is not None
        assert change['symbol'] == 'BTC/USDT'
        assert change['open_price'] == 45000
        assert change['close_price'] == 45200
        assert change['percent_change'] > 0
    
    def test_get_support_resistance(self, market_service_with_mock, mock_fetcher, mock_ohlcv_data):
        """Test support/resistance calculation."""
        mock_fetcher.fetch_ohlcv.return_value = mock_ohlcv_data
        
        sr = market_service_with_mock.get_support_resistance('BTC/USDT')
        
        assert sr is not None
        assert sr['symbol'] == 'BTC/USDT'
        assert 'support' in sr
        assert 'pivot' in sr
        assert 'resistance' in sr
        assert sr['support'] < sr['pivot'] < sr['resistance']


class TestMarketTools:
    """Tests for LangChain market tools."""
    
    @patch('app.tools.market_tools.get_market_service')
    def test_get_crypto_price_tool(self, mock_get_service, mock_fetcher, mock_ticker_data):
        """Test get_crypto_price tool."""
        mock_service = Mock()
        mock_service.get_current_price.return_value = 45200.50
        mock_get_service.return_value = mock_service
        
        result = market_tools.get_crypto_price.invoke({'symbol': 'BTC/USDT'})
        
        assert 'BTC/USDT' in result
        assert '$45,200.50' in result
        mock_service.get_current_price.assert_called_once_with('BTC/USDT')
    
    @patch('app.tools.market_tools.get_market_service')
    def test_get_crypto_price_tool_error(self, mock_get_service):
        """Test get_crypto_price tool with error."""
        mock_service = Mock()
        mock_service.get_current_price.return_value = None
        mock_get_service.return_value = mock_service
        
        result = market_tools.get_crypto_price.invoke({'symbol': 'INVALID/USDT'})
        
        assert 'Error' in result
    
    @patch('app.tools.market_tools.get_market_service')
    def test_get_market_data_tool(self, mock_get_service, mock_ohlcv_data):
        """Test get_market_data tool."""
        mock_service = Mock()
        mock_service.get_market_data.return_value = mock_ohlcv_data
        mock_get_service.return_value = mock_service
        
        result = market_tools.get_market_data.invoke({
            'symbol': 'BTC/USDT',
            'timeframe': '1h',
            'limit': 50
        })
        
        assert 'BTC/USDT' in result
        assert '[1h]' in result
        assert '4 candles' in result
    
    @patch('app.tools.market_tools.get_market_service')
    def test_get_market_data_tool_limit_capped(self, mock_get_service, mock_ohlcv_data):
        """Test get_market_data tool caps limit at 200."""
        mock_service = Mock()
        mock_service.get_market_data.return_value = mock_ohlcv_data
        mock_get_service.return_value = mock_service
        
        result = market_tools.get_market_data.invoke({
            'symbol': 'BTC/USDT',
            'limit': 500
        })
        
        # Verify limit was capped to 200
        call_args = mock_service.get_market_data.call_args
        assert call_args[1]['limit'] == 200
    
    @patch('app.tools.market_tools.get_market_service')
    def test_get_volume_stats_tool(self, mock_get_service):
        """Test get_volume_stats tool."""
        mock_service = Mock()
        mock_service.get_volume_stats.return_value = {
            'symbol': 'BTC/USDT',
            'timeframe': '1h',
            'average_volume': 1025000,
            'max_volume': 1100000,
            'min_volume': 950000,
            'current_volume': 1050000,
            'total_volume': 4100000,
            'timestamp': datetime.now().isoformat()
        }
        mock_get_service.return_value = mock_service
        
        result = market_tools.get_volume_stats.invoke({'symbol': 'BTC/USDT'})
        
        assert 'BTC/USDT' in result
        assert 'Current' in result
        assert 'Average' in result
    
    @patch('app.tools.market_tools.get_market_service')
    def test_get_price_comparison_tool(self, mock_get_service):
        """Test get_price_comparison tool."""
        mock_service = Mock()
        mock_service.get_price_comparison.return_value = {
            'BTC/USDT': 45200.50,
            'ETH/USDT': 2465.25
        }
        mock_get_service.return_value = mock_service
        
        result = market_tools.get_price_comparison.invoke({
            'symbols': 'BTC/USDT,ETH/USDT'
        })
        
        assert 'Price Comparison' in result
        assert 'BTC/USDT' in result
        assert 'ETH/USDT' in result
    
    @patch('app.tools.market_tools.get_market_service')
    def test_get_price_comparison_tool_too_many_symbols(self, mock_get_service):
        """Test get_price_comparison tool with too many symbols."""
        result = market_tools.get_price_comparison.invoke({
            'symbols': 'A,B,C,D,E,F,G,H,I,J,K'
        })
        
        assert 'Error' in result
        assert 'Maximum 10' in result
    
    @patch('app.tools.market_tools.get_market_service')
    def test_get_price_change_tool(self, mock_get_service):
        """Test get_price_change tool."""
        mock_service = Mock()
        mock_service.get_price_change.return_value = {
            'symbol': 'BTC/USDT',
            'period_hours': 24,
            'open_price': 45000,
            'close_price': 45200,
            'high_price': 45300,
            'low_price': 44900,
            'change': 200,
            'percent_change': 0.444,
            'timestamp': datetime.now().isoformat()
        }
        mock_get_service.return_value = mock_service
        
        result = market_tools.get_price_change.invoke({
            'symbol': 'BTC/USDT',
            'period_hours': 24
        })
        
        assert 'BTC/USDT' in result
        assert '24h' in result
        assert '+0.44%' in result
    
    @patch('app.tools.market_tools.get_market_service')
    def test_get_support_resistance_tool(self, mock_get_service):
        """Test get_support_resistance tool."""
        mock_service = Mock()
        mock_service.get_support_resistance.return_value = {
            'symbol': 'BTC/USDT',
            'timeframe': '1h',
            'support': 45000,
            'pivot': 45150,
            'resistance': 45300,
            'current_price': 45200,
            'timestamp': datetime.now().isoformat()
        }
        mock_get_service.return_value = mock_service
        
        result = market_tools.get_support_resistance.invoke({
            'symbol': 'BTC/USDT'
        })
        
        assert 'BTC/USDT' in result
        assert 'Support' in result
        assert 'Resistance' in result


class TestMarketToolsIntegration:
    """Integration tests for tool schema and registration."""
    
    def test_all_tools_are_structured_tools(self):
        """Test that all market tools are LangChain StructuredTool objects."""
        from langchain_core.tools import StructuredTool
        
        for tool_func in market_tools.MARKET_TOOLS:
            assert isinstance(tool_func, StructuredTool)
    
    def test_tools_have_descriptions(self):
        """Test that all tools have descriptions."""
        for tool_func in market_tools.MARKET_TOOLS:
            assert tool_func.description is not None
            assert len(tool_func.description.strip()) > 0
    
    def test_tool_names_are_unique(self):
        """Test that all tool names are unique."""
        names = [tool_func.name for tool_func in market_tools.MARKET_TOOLS]
        assert len(names) == len(set(names))


if __name__ == '__main__':
    pytest.main([__file__, '-v'])
