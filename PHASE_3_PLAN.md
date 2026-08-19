## PHASE 3: MARKET TOOLS (Coming Next)

### Objective
Wrap existing market data functionality into reusable LangChain tools, enabling the AI agent to intelligently request and analyze market data.

### Current State
- ✅ Existing `data/fetcher.py` has working CCXT integration
- ✅ Multi-pair, multi-timeframe support
- ✅ OHLCV and ticker data retrieval
- ✅ Error handling and logging
- 🔄 Need to: Wrap into service layer + tools

---

## Phase 3 Implementation Plan

### Task 1: Create Market Service

**File**: `app/services/market_service.py`

**Purpose**: Abstract the CCXT exchange layer, provide clean service interface

**Implementation**:
```python
from data.fetcher import DataFetcher
import logging

class MarketService:
    """Service for market data operations."""
    
    def __init__(self, api_key: str, api_secret: str, use_testnet: bool = True):
        """Initialize with existing DataFetcher."""
        self.fetcher = DataFetcher(api_key, api_secret, use_testnet)
    
    def get_current_price(self, symbol: str) -> dict:
        """Get current price for a symbol."""
        ticker = self.fetcher.fetch_ticker(symbol)
        return {
            "symbol": symbol,
            "price": float(ticker.get('last', 0)),
            "bid": float(ticker.get('bid', 0)),
            "ask": float(ticker.get('ask', 0)),
            "volume_24h": float(ticker.get('quoteVolume', 0)),
            "change_24h_percent": float(ticker.get('percentage', 0))
        }
    
    def get_ohlcv_data(self, symbol: str, timeframe: str, limit: int) -> dict:
        """Get OHLCV candle data."""
        df = self.fetcher.fetch_ohlcv(symbol, timeframe, limit)
        return {
            "symbol": symbol,
            "timeframe": timeframe,
            "candles": len(df),
            "current_price": float(df['close'].iloc[-1]),
            "high_24h": float(df['high'].max()),
            "low_24h": float(df['low'].min()),
            "volume_avg": float(df['volume'].mean()),
            "data": df.to_dict(orient='records')
        }
    
    def get_market_volume(self, symbol: str, timeframe: str) -> dict:
        """Analyze volume trends."""
        df = self.fetcher.fetch_ohlcv(symbol, timeframe, limit=20)
        avg_volume = float(df['volume'].mean())
        current_volume = float(df['volume'].iloc[-1])
        return {
            "symbol": symbol,
            "current_volume": current_volume,
            "average_volume": avg_volume,
            "volume_ratio": current_volume / avg_volume if avg_volume > 0 else 0,
            "trend": "above_average" if current_volume > avg_volume else "below_average"
        }
```

**Key Methods**:
- `get_current_price(symbol)` → Returns structured price data
- `get_ohlcv_data(symbol, timeframe, limit)` → Returns candle data
- `get_market_volume(symbol, timeframe)` → Returns volume analysis
- `get_market_trend(symbol, timeframe)` → Returns trend direction (to add)
- `get_price_change(symbol, periods)` → Returns price change % (to add)

**Testing**:
- Unit tests with mocked CCXT responses
- No live API calls required
- Verify returned data structure
- Error handling tests

---

### Task 2: Create Market Tools

**File**: `app/tools/market_tools.py`

**Purpose**: LangChain tools that agents can call

**Implementation**:
```python
from langchain_core.tools import tool
from app.services.market_service import MarketService
import config
import logging

logger = logging.getLogger(__name__)
market_service = MarketService(config.BYBIT_API_KEY, config.BYBIT_API_SECRET, config.USE_TESTNET)

@tool
def get_crypto_price(symbol: str) -> dict:
    """
    Get the current price of a cryptocurrency.
    
    Args:
        symbol: Trading pair (e.g., 'BTC/USDT', 'ETH/USDT')
    
    Returns:
        Dictionary with current price and 24h change
    """
    try:
        return market_service.get_current_price(symbol)
    except Exception as e:
        logger.error(f"Error getting price for {symbol}: {e}")
        return {"error": str(e), "symbol": symbol}

@tool
def get_market_data(symbol: str, timeframe: str = "1h", limit: int = 100) -> dict:
    """
    Get OHLCV market data for analysis.
    
    Args:
        symbol: Trading pair (e.g., 'BTC/USDT')
        timeframe: Candle timeframe (e.g., '15m', '1h', '4h', '1d')
        limit: Number of candles to fetch (default 100)
    
    Returns:
        Dictionary with OHLCV data and summary statistics
    """
    try:
        return market_service.get_ohlcv_data(symbol, timeframe, limit)
    except Exception as e:
        logger.error(f"Error getting market data for {symbol}: {e}")
        return {"error": str(e), "symbol": symbol}

@tool
def get_market_volume(symbol: str, timeframe: str = "1h") -> dict:
    """
    Analyze trading volume for a symbol.
    
    Args:
        symbol: Trading pair (e.g., 'BTC/USDT')
        timeframe: Timeframe for analysis (default 1h)
    
    Returns:
        Dictionary with volume metrics and trend
    """
    try:
        return market_service.get_market_volume(symbol, timeframe)
    except Exception as e:
        logger.error(f"Error getting volume for {symbol}: {e}")
        return {"error": str(e), "symbol": symbol}

@tool
def get_price_comparison(symbols: list) -> dict:
    """
    Compare prices across multiple cryptocurrencies.
    
    Args:
        symbols: List of trading pairs to compare
    
    Returns:
        Dictionary with price comparison data
    """
    try:
        prices = {}
        for symbol in symbols:
            prices[symbol] = market_service.get_current_price(symbol)
        return prices
    except Exception as e:
        logger.error(f"Error comparing prices: {e}")
        return {"error": str(e)}
```

**Tool Registration**:
```python
# At the end of market_tools.py
from app.tools import register_tool

register_tool("get_crypto_price", get_crypto_price, "Get current price of a crypto")
register_tool("get_market_data", get_market_data, "Get OHLCV candle data")
register_tool("get_market_volume", get_market_volume, "Analyze trading volume")
register_tool("get_price_comparison", get_price_comparison, "Compare prices of multiple cryptos")
```

**Tools to Create**:
1. ✅ `get_crypto_price(symbol)` - Current price
2. ✅ `get_market_data(symbol, timeframe, limit)` - OHLCV
3. ✅ `get_market_volume(symbol, timeframe)` - Volume analysis
4. ✅ `get_price_comparison(symbols)` - Multi-crypto comparison
5. 🔄 `get_market_trend(symbol, timeframe)` - Trend direction
6. 🔄 `get_support_resistance(symbol, timeframe)` - Price levels

---

### Task 3: Testing

**File**: `tests/test_market_tools.py`

**Test Strategy**:
```python
import pytest
from unittest.mock import Mock, patch
import pandas as pd
from app.services.market_service import MarketService
from app.tools.market_tools import (
    get_crypto_price,
    get_market_data,
    get_market_volume
)

@pytest.fixture
def mock_data_fetcher():
    """Mock the DataFetcher to avoid live API calls."""
    with patch('app.services.market_service.DataFetcher') as mock:
        yield mock

@pytest.fixture
def market_service(mock_data_fetcher):
    """Create a MarketService with mocked fetcher."""
    service = MarketService("test_key", "test_secret", use_testnet=True)
    # Setup mock responses
    service.fetcher.fetch_ticker = Mock(return_value={
        'symbol': 'BTC/USDT',
        'last': 45000.0,
        'bid': 44999.0,
        'ask': 45001.0,
        'quoteVolume': 1000.0,
        'percentage': 2.5
    })
    return service

def test_get_current_price(market_service):
    """Test getting current price."""
    result = get_crypto_price("BTC/USDT")
    assert result['symbol'] == "BTC/USDT"
    assert result['price'] == 45000.0
    assert 'change_24h_percent' in result

def test_get_market_data(market_service):
    """Test getting OHLCV data."""
    result = get_market_data("BTC/USDT", "1h", 100)
    assert result['symbol'] == "BTC/USDT"
    assert result['timeframe'] == "1h"
    assert 'candles' in result
    assert 'current_price' in result

def test_tool_handles_errors():
    """Test tools handle errors gracefully."""
    result = get_crypto_price("INVALID/PAIR")
    # Should return error dict, not raise exception
    assert isinstance(result, dict)
```

**Coverage Goals**:
- Unit tests for MarketService methods
- Tool tests with mocked CCXT responses
- Error handling tests
- Edge case tests (empty data, network errors, etc.)

---

### Task 4: Integration & Verification

**Checklist**:
- [ ] `app/services/market_service.py` created
- [ ] `app/tools/market_tools.py` created  
- [ ] Tools registered in registry
- [ ] `tests/test_market_tools.py` created
- [ ] All tests passing
- [ ] Existing bot still works (main.py runs)
- [ ] No breaking changes to existing code

---

### Reusing Existing Code

**What we're leveraging**:
- ✅ `data/fetcher.py` - No changes, just wrapped
- ✅ `config.py` - Existing BYBIT credentials
- ✅ CCXT integration - Already proven working
- ✅ Error handling patterns - Borrowed from existing code

**Benefits**:
- Zero changes to existing bot
- Proven market data retrieval
- Familiar configuration system
- All existing tests continue to pass

---

### Phase 3 Timeline

| Task | Estimated Time |
|------|-----------------|
| Create MarketService | 30 min |
| Create market_tools.py | 30 min |
| Write tests | 45 min |
| Integration & verification | 30 min |
| **Total** | **~2 hours** |

---

### Success Criteria

✅ **Phase 3 is complete when**:
1. `MarketService` wraps `DataFetcher` with clean interface
2. All market tools are decorated with `@tool` and registered
3. Tests provide 80%+ coverage of market tools
4. Integration test confirms tools work with agent
5. Existing bot continues to work unchanged
6. All tests passing

---

### Next Phase: Phase 4 - Technical Tools

Once Phase 3 is complete, we'll wrap technical indicators (RSI, MACD, Bollinger Bands, etc.) from `analysis/signals.py` into technical tools.

Tools will include:
- `calculate_rsi(symbol, timeframe, period)`
- `calculate_macd(symbol, timeframe)`
- `calculate_moving_average(symbol, timeframe, ma_type, period)`
- `calculate_bollinger_bands(symbol, timeframe)`
- `analyze_technical_indicators(symbol, timeframe)` - Returns all indicators

Same pattern: Service layer → Tool wrappers → Tests → Integration

---

## Architecture Visualization (After Phase 3)

```
LangChain Agent
      |
      v
Market Tools (market_tools.py)
      |
      +--- get_crypto_price()
      +--- get_market_data()
      +--- get_market_volume()
      +--- get_price_comparison()
      |
      v
Market Service (market_service.py)
      |
      v
DataFetcher (data/fetcher.py) [EXISTING]
      |
      v
CCXT Exchange
```

Clean separation of concerns:
- **CCXT** = Raw exchange data
- **DataFetcher** = Data retrieval layer
- **MarketService** = Business logic layer
- **Market Tools** = LangChain interface

Each layer is independent and testable!
