"""
tests/test_technical_tools.py
-----------------------------
Unit tests for technical tools and TechnicalService.
Uses mocked candle data to avoid live API calls.
"""

import pytest
import pandas as pd
import numpy as np
from unittest.mock import Mock, MagicMock, patch

from app.services.technical_service import TechnicalService
from app.tools import technical_tools


@pytest.fixture
def mock_large_ohlcv_data():
    """Create a mock OHLCV dataset of 250 rows for full indicator coverage (e.g. EMA 200)."""
    np.random.seed(42)
    rows = 250
    # Simulate a steady price trend with small fluctuations
    base_price = 45000.0
    price_changes = np.random.normal(loc=1.0, scale=50.0, size=rows)
    closes = base_price + np.cumsum(price_changes)
    opens = closes - np.random.normal(loc=0.0, scale=25.0, size=rows)
    highs = np.maximum(opens, closes) + np.random.exponential(scale=15.0, size=rows)
    lows = np.minimum(opens, closes) - np.random.exponential(scale=15.0, size=rows)
    volumes = np.random.exponential(scale=1000000.0, size=rows) + 500000.0

    return pd.DataFrame({
        'open': opens,
        'high': highs,
        'low': lows,
        'close': closes,
        'volume': volumes
    }, index=pd.date_range(start='2024-01-01', periods=rows, freq='1h'))


@pytest.fixture
def mock_market_service():
    """Create a mocked MarketService."""
    return Mock()


@pytest.fixture
def technical_service_with_mock(mock_market_service):
    """Create TechnicalService with mocked market service."""
    return TechnicalService(market_service=mock_market_service)


class TestTechnicalService:
    """Tests for TechnicalService class."""
    
    def test_analyze_indicators_success(self, technical_service_with_mock, mock_market_service, mock_large_ohlcv_data):
        """Test successful indicator analysis."""
        mock_market_service.get_market_data.return_value = mock_large_ohlcv_data
        
        result = technical_service_with_mock.analyze_indicators('BTC/USDT', timeframe='1h')
        
        assert result is not None
        assert result['symbol'] == 'BTC/USDT'
        assert result['timeframe'] == '1h'
        assert result['rsi'] is not None
        assert result['ema_fast'] is not None
        assert result['ema_slow'] is not None
        assert result['ema_200'] is not None
        assert result['macd'] is not None
        assert result['bb_upper'] is not None
        assert result['bb_lower'] is not None
        assert result['atr'] is not None
        assert result['trend'] in ['bullish', 'bearish']
        assert result['recommended_signal'] in ['BUY', 'SELL', 'HOLD']
        assert result['volume_trend'] in ['high', 'low', 'normal']
        
        mock_market_service.get_market_data.assert_called_once_with(
            'BTC/USDT', timeframe='1h', limit=250
        )
        
    def test_analyze_indicators_empty_data(self, technical_service_with_mock, mock_market_service):
        """Test indicator analysis when market data is empty."""
        mock_market_service.get_market_data.return_value = pd.DataFrame()
        
        result = technical_service_with_mock.analyze_indicators('BTC/USDT')
        
        assert result is None


class TestTechnicalTools:
    """Tests for LangChain technical tools."""
    
    @patch('app.tools.technical_tools.get_technical_service')
    def test_calculate_rsi_tool(self, mock_get_service):
        """Test calculate_rsi tool."""
        mock_service = Mock()
        mock_service.analyze_indicators.return_value = {
            'rsi': 65.5,
            'close_price': 45200.50
        }
        mock_get_service.return_value = mock_service
        
        result = technical_tools.calculate_rsi.invoke({
            'symbol': 'BTC/USDT',
            'timeframe': '1h'
        })
        
        assert 'BTC/USDT' in result
        assert '65.50' in result
        assert 'Neutral' in result
        mock_service.analyze_indicators.assert_called_once_with('BTC/USDT', timeframe='1h')

    @patch('app.tools.technical_tools.get_technical_service')
    def test_calculate_rsi_tool_oversold(self, mock_get_service):
        """Test calculate_rsi tool when oversold."""
        mock_service = Mock()
        mock_service.analyze_indicators.return_value = {
            'rsi': 25.0,
            'close_price': 45200.50
        }
        mock_get_service.return_value = mock_service
        
        result = technical_tools.calculate_rsi.invoke({'symbol': 'BTC/USDT'})
        
        assert 'Oversold' in result

    @patch('app.tools.technical_tools.get_technical_service')
    def test_calculate_rsi_tool_overbought(self, mock_get_service):
        """Test calculate_rsi tool when overbought."""
        mock_service = Mock()
        mock_service.analyze_indicators.return_value = {
            'rsi': 75.0,
            'close_price': 45200.50
        }
        mock_get_service.return_value = mock_service
        
        result = technical_tools.calculate_rsi.invoke({'symbol': 'BTC/USDT'})
        
        assert 'Overbought' in result
        
    @patch('app.tools.technical_tools.get_technical_service')
    def test_calculate_macd_tool(self, mock_get_service):
        """Test calculate_macd tool."""
        mock_service = Mock()
        mock_service.analyze_indicators.return_value = {
            'macd': 15.2,
            'macd_signal': 10.1,
            'close_price': 45200.50
        }
        mock_get_service.return_value = mock_service
        
        result = technical_tools.calculate_macd.invoke({'symbol': 'BTC/USDT'})
        
        assert 'MACD' in result
        assert '15.2000' in result
        assert '10.1000' in result
        assert 'Bullish' in result

    @patch('app.tools.technical_tools.get_technical_service')
    def test_calculate_moving_averages_tool(self, mock_get_service):
        """Test calculate_moving_averages tool."""
        mock_service = Mock()
        mock_service.analyze_indicators.return_value = {
            'close_price': 45200.50,
            'ema_fast': 45100.0,
            'ema_slow': 45000.0,
            'ema_200': 44500.0
        }
        mock_get_service.return_value = mock_service
        
        result = technical_tools.calculate_moving_averages.invoke({'symbol': 'BTC/USDT'})
        
        assert '45,200.50' in result
        assert 'Fast' in result
        assert 'Slow' in result
        assert 'Bullish Crossover' in result
        assert 'Above 200 EMA' in result

    @patch('app.tools.technical_tools.get_technical_service')
    def test_calculate_bollinger_bands_tool(self, mock_get_service):
        """Test calculate_bollinger_bands tool."""
        mock_service = Mock()
        mock_service.analyze_indicators.return_value = {
            'close_price': 45200.50,
            'bb_upper': 45500.0,
            'bb_lower': 45000.0
        }
        mock_get_service.return_value = mock_service
        
        result = technical_tools.calculate_bollinger_bands.invoke({'symbol': 'BTC/USDT'})
        
        assert '45,200.50' in result
        assert 'Upper Band: $45,500.00' in result
        assert 'Lower Band: $45,000.00' in result
        assert 'Between bands' in result

    @patch('app.tools.technical_tools.get_technical_service')
    def test_calculate_market_indicators_tool(self, mock_get_service):
        """Test calculate_market_indicators tool."""
        mock_service = Mock()
        mock_service.analyze_indicators.return_value = {
            'close_price': 45200.50,
            'trend': 'bullish',
            'recommended_signal': 'BUY',
            'rsi': 55.0,
            'macd': 12.0,
            'macd_signal': 10.0,
            'ema_fast': 45100.0,
            'ema_slow': 45050.0,
            'ema_200': 44000.0,
            'bb_upper': 45600.0,
            'bb_lower': 44900.0,
            'atr': 250.0,
            'volume_trend': 'normal'
        }
        mock_get_service.return_value = mock_service
        
        result = technical_tools.calculate_market_indicators.invoke({'symbol': 'BTC/USDT'})
        
        assert 'Technical Analysis Report' in result
        assert 'RSI: 55.00' in result
        assert 'BUY' in result
        assert 'ATR' in result


class TestTechnicalToolsIntegration:
    """Integration tests for tool schema and registration."""
    
    def test_all_tools_are_structured_tools(self):
        """Test that all technical tools are StructuredTool instances."""
        from langchain_core.tools import StructuredTool
        
        for tool_func in technical_tools.TECHNICAL_TOOLS:
            assert isinstance(tool_func, StructuredTool)
            
    def test_tools_registered_in_registry(self):
        """Test that technical tools are successfully registered in the central registry."""
        from app.tools import get_registry
        
        registry = get_registry()
        names = registry.get_names()
        
        assert "calculate_rsi" in names
        assert "calculate_macd" in names
        assert "calculate_moving_averages" in names
        assert "calculate_bollinger_bands" in names
        assert "calculate_market_indicators" in names
