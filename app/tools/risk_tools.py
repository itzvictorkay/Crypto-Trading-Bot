"""
app/tools/risk_tools.py
-----------------------
LangChain tools for trade risk analysis and portfolio tracking.
These tools allow the AI agent to compute position sizes and SL/TP levels dynamically.
"""

import logging
from typing import Optional
from langchain_core.tools import tool

from app.services.risk_service import RiskService

logger = logging.getLogger(__name__)

# Module-level service instance
_risk_service = None


def get_risk_service() -> RiskService:
    """Get or create RiskService instance."""
    global _risk_service
    if _risk_service is None:
        _risk_service = RiskService()
    return _risk_service


@tool
def perform_risk_analysis(
    symbol: str, 
    current_price: float, 
    signal: str, 
    atr: Optional[float] = None
) -> str:
    """
    Perform a complete risk analysis for a potential trade setup.
    Calculates safe position sizing, Stop-Loss (SL), and Take-Profit (TP) levels.
    
    Args:
        symbol: Trading pair (e.g., 'BTC/USDT')
        current_price: Current market entry price
        signal: Potential signal direction ('BUY' or 'SELL')
        atr: Optional Average True Range (ATR) to enable dynamic volatility-based stops
        
    Returns:
        Structured risk analysis report string
    """
    try:
        if signal.upper() not in ["BUY", "SELL"]:
            return "Error: signal direction must be either 'BUY' or 'SELL'."
            
        service = get_risk_service()
        report = service.assess_trade_risk(
            symbol=symbol,
            current_price=current_price,
            signal=signal.upper(),
            atr=atr
        )
        
        if "error" in report:
            return f"Error performing risk analysis: {report['error']}"
            
        pos_status = "⚠️ Open Position Detected" if report['has_existing_position'] else "No existing positions"
        stop_type = "ATR-based dynamic" if report['atr_used'] else "fixed percentage"
        
        result = (
            f"=== Risk Analysis Report: {symbol} [{signal.upper()}] ===\n"
            f"Entry Price: ${current_price:,.2f}\n"
            f"Sizing & Budget:\n"
            f"  - Recommended Sizing: {report['position_size']:.6f} units\n"
            f"  - Capital Committed: ${report['total_cost_usdt']:,.2f} USDT\n"
            f"Risk/Reward Targets ({stop_type} stops):\n"
            f"  - Stop-Loss (SL): ${report['stop_loss']:,.2f}\n"
            f"  - Take-Profit (TP): ${report['take_profit']:,.2f}\n"
            f"  - Reward-to-Risk Ratio: {report['reward_risk_ratio']:.2f} : 1\n"
            f"Portfolio Checks:\n"
            f"  - Status: {pos_status}"
        )
        
        return result
    except Exception as e:
        logger.error(f"Error in perform_risk_analysis tool: {e}")
        return f"Error executing risk calculation: {str(e)}"


@tool
def get_portfolio_balance() -> str:
    """
    Get current portfolio balance summary including total available capital and risk caps.
    
    Returns:
        Portfolio balance summary string
    """
    try:
        service = get_risk_service()
        data = service.get_portfolio_balance()
        
        if "error" in data:
            return f"Error retrieving portfolio balance: {data['error']}"
            
        result = (
            f"=== Portfolio Balance Summary ===\n"
            f"Available USDT: ${data['available_usdt']:,.2f}\n"
            f"Risk Metrics (per trade limits):\n"
            f"  - Max Loss limit (config risk%): ${data['max_risk_amount']:,.2f} USDT\n"
            f"  - Max capital commitment limit (config cap%): ${data['max_trade_cap']:,.2f} USDT"
        )
        return result
    except Exception as e:
        logger.error(f"Error in get_portfolio_balance tool: {e}")
        return f"Error retrieving balance details: {str(e)}"


# Export tools for registration
RISK_TOOLS = [
    perform_risk_analysis,
    get_portfolio_balance,
]
