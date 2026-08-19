"""
tests/test_risk_tools.py
------------------------
Unit tests for risk tools and RiskService.
Mocks the underlying RiskManager and Exchange operations.
"""

import pytest
from unittest.mock import Mock, patch

import config
from app.services.risk_service import RiskService
from app.tools import risk_tools


@pytest.fixture
def mock_risk_manager():
    """Create a mock RiskManager."""
    manager = Mock()
    manager.get_balance.return_value = 10000.0
    manager.calculate_position_size.return_value = 0.5
    manager.calculate_sl_tp.return_value = (44000.0, 48000.0)
    manager.has_open_position.return_value = False
    return manager


class TestRiskService:
    """Tests for RiskService class."""

    @patch('app.services.risk_service.RiskManager')
    def test_get_portfolio_balance(self, mock_class, mock_risk_manager):
        """Test retrieving balance statistics."""
        mock_class.return_value = mock_risk_manager
        
        # In order to trigger __init__ where RiskManager is instantiated
        service = RiskService()
        result = service.get_portfolio_balance()

        assert "available_usdt" in result
        assert result["available_usdt"] == 10000.0
        assert result["max_risk_amount"] == 10000.0 * config.MAX_RISK_PER_TRADE
        assert result["max_trade_cap"] == 10000.0 * config.MAX_BALANCE_USAGE_PCT

    @patch('app.services.risk_service.RiskManager')
    def test_assess_trade_risk(self, mock_class, mock_risk_manager):
        """Test trade risk assessment calculation."""
        mock_class.return_value = mock_risk_manager
        
        service = RiskService()
        result = service.assess_trade_risk(
            symbol="BTC/USDT",
            current_price=45000.0,
            signal="BUY",
            atr=500.0
        )

        assert result["symbol"] == "BTC/USDT"
        assert result["position_size"] == 0.5
        assert result["total_cost_usdt"] == 0.5 * 45000.0
        assert result["stop_loss"] == 44000.0
        assert result["take_profit"] == 48000.0
        assert result["reward_risk_ratio"] > 0.0
        assert result["has_existing_position"] is False
        
        mock_risk_manager.calculate_position_size.assert_called_once_with("BTC/USDT", 45000.0)
        mock_risk_manager.calculate_sl_tp.assert_called_once_with("BUY", 45000.0, atr=500.0)


class TestRiskTools:
    """Tests for LangChain risk tools."""

    @patch('app.tools.risk_tools.get_risk_service')
    def test_perform_risk_analysis_tool(self, mock_get_service):
        """Test perform_risk_analysis tool output layout."""
        mock_service = Mock()
        mock_service.assess_trade_risk.return_value = {
            "symbol": "BTC/USDT",
            "signal": "BUY",
            "current_price": 45000.0,
            "position_size": 0.5,
            "total_cost_usdt": 22500.0,
            "stop_loss": 44000.0,
            "take_profit": 47000.0,
            "reward_risk_ratio": 2.0,
            "has_existing_position": False,
            "atr_used": True
        }
        mock_get_service.return_value = mock_service

        result = risk_tools.perform_risk_analysis.invoke({
            "symbol": "BTC/USDT",
            "current_price": 45000.0,
            "signal": "BUY",
            "atr": 500.0
        })

        assert "BTC/USDT" in result
        assert "Entry Price: $45,000.00" in result
        assert "Stop-Loss (SL): $44,000.00" in result
        assert "Take-Profit (TP): $47,000.00" in result
        assert "Reward-to-Risk Ratio: 2.00" in result

    @patch('app.tools.risk_tools.get_risk_service')
    def test_get_portfolio_balance_tool(self, mock_get_service):
        """Test get_portfolio_balance tool output layout."""
        mock_service = Mock()
        mock_service.get_portfolio_balance.return_value = {
            "available_usdt": 10000.0,
            "max_risk_amount": 200.0,
            "max_trade_cap": 1000.0
        }
        mock_get_service.return_value = mock_service

        result = risk_tools.get_portfolio_balance.invoke({})

        assert "Portfolio Balance Summary" in result
        assert "Available USDT: $10,000.00" in result
        assert "Max Loss limit" in result
        assert "Max capital commitment limit" in result


class TestRiskToolsIntegration:
    """Integration tests for tool schema and registry."""

    def test_tools_are_structured_tools(self):
        """Test that risk tools are StructuredTool instances."""
        from langchain_core.tools import StructuredTool
        
        assert isinstance(risk_tools.perform_risk_analysis, StructuredTool)
        assert isinstance(risk_tools.get_portfolio_balance, StructuredTool)

    def test_tools_registered_in_registry(self):
        """Test that risk tools are registered in central registry."""
        from app.tools import get_registry
        
        registry = get_registry()
        assert "perform_risk_analysis" in registry.get_names()
        assert "get_portfolio_balance" in registry.get_names()
