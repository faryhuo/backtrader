# Multi-Asset Portfolio Backtest Implementation Roadmap

## Overview

This document tracks the implementation progress of the **Portfolio Enhancement** feature - a true multi-asset portfolio backtesting engine with rebalancing, optimization, and advanced analytics.

**Feature Reference**: [FEATURE-PLAN.md](./FEATURE-PLAN.md) - 组合回测增强（Portfolio Enhancement）

---

## ✅ Completed Phases (Phase 1 & 2)

### Phase 1: Basic Multi-Asset Engine ✅ COMPLETED

**Duration**: Completed on 2025-12-26

**Deliverables**:
1. ✅ **Multi-Asset Backtest Engine** ([multi_asset_backtest.py](../backend/src/service/multi_asset_backtest.py))
   - Single Backtrader Cerebro managing multiple data feeds
   - Data alignment logic handling different trading calendars
   - Main orchestration function `run_multi_asset_backtest()`
   - Comprehensive error handling and logging

2. ✅ **Strategy Wrapper** ([multi_asset_strategy_wrapper.py](../backend/src/service/multi_asset_strategy_wrapper.py))
   - `MultiAssetPortfolioStrategy` - Portfolio manager for N assets
   - `BuyAndHoldPortfolioStrategy` - Simple buy-and-hold implementation
   - Per-asset indicator creation with custom parameters
   - Rolling returns tracking (252-day lookback)
   - Initial position establishment logic

3. ✅ **Custom Analyzers** ([portfolio_analyzers.py](../backend/src/service/portfolio_analyzers.py))
   - `PortfolioValueAnalyzer` - Daily equity curve tracking
   - `RebalancingEventAnalyzer` - Rebalancing event logging
   - `AssetContributionAnalyzer` - Per-asset return contribution
   - `PortfolioMetricsAnalyzer` - Sharpe, Sortino, volatility

4. ✅ **Database Schema** ([backtest.py](../backend/src/db/models/backtest.py))
   - Extended `PortfolioResultModel` with 7 new columns:
     - `equity_curve` (JSON) - Time-series portfolio value
     - `rebalancing_events` (JSON) - Rebalancing history
     - `asset_contributions` (JSON) - Per-asset metrics
     - `optimization_history` (JSON) - Dynamic optimization tracking
     - `rebalance_frequency` (VARCHAR) - Schedule configuration
     - `optimization_method` (VARCHAR) - Algorithm used
     - `per_asset_params` (JSON) - Per-ticker parameters
   - Migration script: [add_multi_asset_columns.py](../backend/scripts/migrations/add_multi_asset_columns.py)

**Success Criteria Met**:
- ✅ Multiple tickers in single unified backtest
- ✅ Automatic data alignment across trading calendars
- ✅ Portfolio-level equity curve tracking
- ✅ Per-asset return contribution analysis
- ✅ Comprehensive portfolio metrics

---

### Phase 2: Rebalancing Logic ✅ COMPLETED

**Duration**: Completed on 2025-12-26

**Deliverables**:
1. ✅ **Rebalancing System** ([portfolio_rebalancer.py](../backend/src/service/portfolio_rebalancer.py))
   - `RebalanceScheduler` - Date generation (monthly/quarterly/annually)
     - Supports first/last day of period
     - Custom day-of-month scheduling
   - `PortfolioRebalancer` - Rebalancing calculator and executor
     - Current/target weight calculation
     - Trade calculation with minimum threshold (1% default)
     - Transaction cost estimation (0.1% default)
     - Rebalancing history tracking

2. ✅ **Strategy Integration**
   - Updated `MultiAssetPortfolioStrategy` with:
     - Rebalancer initialization
     - Rebalance date generation
     - `_should_rebalance()` - Date checking logic
     - `_execute_rebalance()` - Full rebalancing workflow
       - Position/price gathering
       - Target weight calculation
       - Buy/sell order execution
       - Event recording with transaction costs

3. ✅ **API Endpoint** ([portfolio_routes.py](../backend/src/routes/portfolio_routes.py))
   - New endpoint: `POST /api/portfolio/multi-asset/backtest`
   - Request model: `MultiAssetBacktestRequest`
     - Per-asset strategy parameters
     - Rebalance configuration (frequency, thresholds, costs)
     - Optimization method selection
   - Async executor: `_multi_asset_executor`
   - Database integration with all new fields

**Success Criteria Met**:
- ✅ Monthly/quarterly rebalancing support
- ✅ Rebalancing event tracking with full detail
- ✅ Equal weighting for rebalancing
- ✅ Configurable transaction costs and trade thresholds
- ✅ Complete rebalancing history in results

**Example API Call**:
```json
POST /api/portfolio/multi-asset/backtest
{
  "tickers": ["AAPL", "GOOGL", "MSFT"],
  "weights": [0.33, 0.33, 0.34],
  "start_date": "2023-01-01",
  "end_date": "2023-12-31",
  "initial_cash": 100000,
  "rebalance_config": {
    "frequency": "monthly",
    "min_trade_threshold": 0.01,
    "transaction_cost_pct": 0.001
  },
  "optimization_method": "equal_weight"
}
```

---

## 🚧 Remaining Phases (Phase 3-6)

### Phase 3: Optimization Methods 🔜 NEXT

**Estimated Duration**: 2 weeks

**Objectives**:
Implement multiple portfolio optimization algorithms to enable dynamic rebalancing with sophisticated allocation strategies.

**Tasks**:

#### 3.1: Portfolio Optimizer Base Class
**File**: `backend/src/service/portfolio_optimizer.py` (NEW)

**Implementation**:
```python
from abc import ABC, abstractmethod
import pandas as pd

class PortfolioOptimizer(ABC):
    """Base class for portfolio optimization algorithms."""

    @abstractmethod
    def optimize(self, returns: pd.DataFrame) -> dict:
        """
        Calculate optimal portfolio weights.

        Args:
            returns: Daily returns DataFrame (columns = tickers)

        Returns:
            {
                "weights": [0.3, 0.4, 0.3],
                "tickers": ["AAPL", "GOOGL", "MSFT"],
                "expected_return": 0.15,
                "expected_volatility": 0.12,
                "method": "risk_parity"
            }
        """
        pass
```

#### 3.2: Risk Parity Optimizer
**Algorithm**: Minimize difference between each asset's risk contribution and target (1/N)

**Key Concept**: Each asset should contribute equally to total portfolio risk.

**Implementation Approach**:
```python
class RiskParityOptimizer(PortfolioOptimizer):
    def optimize(self, returns):
        cov_matrix = returns.cov() * 252  # Annualized
        n_assets = len(returns.columns)

        def risk_contribution_objective(weights):
            """Each asset should contribute 1/N to total risk."""
            portfolio_var = weights.T @ cov_matrix @ weights
            marginal_contrib = cov_matrix @ weights
            risk_contrib = weights * marginal_contrib / np.sqrt(portfolio_var)
            target = np.ones(n_assets) / n_assets
            return np.sum((risk_contrib - target) ** 2)

        # Use scipy.optimize.minimize with SLSQP
        constraints = {'type': 'eq', 'fun': lambda w: np.sum(w) - 1}
        bounds = tuple((0, 1) for _ in range(n_assets))

        result = minimize(
            risk_contribution_objective,
            np.ones(n_assets)/n_assets,  # Initial guess
            method='SLSQP',
            bounds=bounds,
            constraints=constraints
        )

        return {
            "weights": result.x.tolist(),
            "method": "risk_parity",
            "success": result.success
        }
```

**When to Use**:
- True diversification (ignores expected returns)
- No return estimation needed (robust)
- Good for long-term strategic allocation

**Trade-offs**:
- May over-allocate to low-volatility assets
- Ignores return expectations

#### 3.3: Minimum Variance Optimizer
**Algorithm**: Minimize portfolio variance (volatility)

**Key Concept**: Find the portfolio with lowest possible risk.

**Implementation Approach**:
```python
class MinimumVarianceOptimizer(PortfolioOptimizer):
    def optimize(self, returns):
        cov_matrix = returns.cov() * 252
        n_assets = len(returns.columns)

        def portfolio_variance(weights):
            return weights.T @ cov_matrix @ weights

        constraints = {'type': 'eq', 'fun': lambda w: np.sum(w) - 1}
        bounds = tuple((0, 1) for _ in range(n_assets))

        result = minimize(
            portfolio_variance,
            np.ones(n_assets)/n_assets,
            method='SLSQP',
            bounds=bounds,
            constraints=constraints
        )

        expected_vol = np.sqrt(result.fun)

        return {
            "weights": result.x.tolist(),
            "expected_volatility": expected_vol,
            "method": "min_variance",
            "success": result.success
        }
```

**When to Use**:
- Conservative portfolios
- Low-risk tolerance
- Stable covariance structure

**Trade-offs**:
- Ignores expected returns completely
- May concentrate in few low-volatility assets

#### 3.4: Markowitz Optimizer (Maximum Sharpe Ratio)
**Algorithm**: Maximize Sharpe ratio (return per unit risk)

**Key Concept**: Optimal risk-adjusted returns.

**Migration Source**: Existing implementation in `portfolio_backtest.py` lines 102-204

**Implementation Approach**:
```python
class MarkowitzOptimizer(PortfolioOptimizer):
    def __init__(self, risk_free_rate=0.02):
        self.risk_free_rate = risk_free_rate

    def optimize(self, returns):
        mean_returns = returns.mean() * 252  # Annualized
        cov_matrix = returns.cov() * 252
        n_assets = len(returns.columns)

        def negative_sharpe(weights):
            """Minimize negative Sharpe = maximize Sharpe."""
            portfolio_return = np.dot(weights, mean_returns)
            portfolio_vol = np.sqrt(weights.T @ cov_matrix @ weights)
            sharpe = (portfolio_return - self.risk_free_rate) / portfolio_vol
            return -sharpe  # Minimize negative

        constraints = {'type': 'eq', 'fun': lambda w: np.sum(w) - 1}
        bounds = tuple((0, 1) for _ in range(n_assets))

        result = minimize(
            negative_sharpe,
            np.ones(n_assets)/n_assets,
            method='SLSQP',
            bounds=bounds,
            constraints=constraints
        )

        weights = result.x
        portfolio_return = np.dot(weights, mean_returns)
        portfolio_vol = np.sqrt(weights.T @ cov_matrix @ weights)
        sharpe = (portfolio_return - self.risk_free_rate) / portfolio_vol

        return {
            "weights": weights.tolist(),
            "expected_return": portfolio_return,
            "expected_volatility": portfolio_vol,
            "sharpe_ratio": sharpe,
            "method": "markowitz",
            "success": result.success
        }
```

**When to Use**:
- Balanced risk-return objectives
- Sufficient historical data
- Mean-variance assumptions hold

**Trade-offs**:
- Sensitive to input estimates (garbage in, garbage out)
- Requires return estimation (can be noisy)

#### 3.5: Equal Weight Optimizer
**Algorithm**: Simple 1/N allocation

**Implementation Approach**:
```python
class EqualWeightOptimizer(PortfolioOptimizer):
    def optimize(self, returns):
        n_assets = len(returns.columns)
        weight = 1.0 / n_assets

        mean_returns = returns.mean() * 252
        cov_matrix = returns.cov() * 252
        weights = np.ones(n_assets) * weight

        portfolio_return = np.dot(weights, mean_returns)
        portfolio_vol = np.sqrt(weights.T @ cov_matrix @ weights)

        return {
            "weights": weights.tolist(),
            "expected_return": portfolio_return,
            "expected_volatility": portfolio_vol,
            "method": "equal_weight",
            "success": True
        }
```

**When to Use**:
- Benchmark comparison
- No strong views on assets
- Simplicity preferred

**Benefits**:
- No optimization errors
- 1/N diversification
- Surprisingly effective in practice

#### 3.6: Optimizer Factory
**File**: `backend/src/service/portfolio_optimizer.py` (same file)

**Implementation**:
```python
def get_optimizer(method: str, **kwargs) -> PortfolioOptimizer:
    """
    Factory function to create optimizer instances.

    Args:
        method: Optimization method name
        **kwargs: Optional parameters for optimizer

    Returns:
        PortfolioOptimizer instance

    Raises:
        ValueError: If method is not supported
    """
    optimizers = {
        "equal_weight": EqualWeightOptimizer,
        "risk_parity": RiskParityOptimizer,
        "min_variance": MinimumVarianceOptimizer,
        "markowitz": MarkowitzOptimizer,
    }

    if method not in optimizers:
        raise ValueError(
            f"Unsupported optimization method: {method}. "
            f"Supported: {', '.join(optimizers.keys())}"
        )

    return optimizers[method](**kwargs)
```

#### 3.7: Integration with Rebalancer
**File**: `backend/src/service/multi_asset_strategy_wrapper.py` (UPDATE)

**Changes Needed**:
```python
# In __init__ method, update rebalancer creation:
from src.service.portfolio_optimizer import get_optimizer

if frequency:
    # Create optimizer if specified
    optimizer = None
    if self.p.optimization_method != "equal_weight":
        try:
            optimizer = get_optimizer(self.p.optimization_method)
            logger.info(f"Using optimizer: {self.p.optimization_method}")
        except Exception as e:
            logger.warning(f"Failed to create optimizer: {e}. Using equal weights.")

    self.rebalancer = PortfolioRebalancer(
        scheduler=scheduler,
        optimizer=optimizer,  # Now uses actual optimizer
        min_trade_threshold=...,
        transaction_cost_pct=...,
    )
```

#### 3.8: Unit Tests
**File**: `backend/tests/service/test_portfolio_optimizer.py` (NEW)

**Test Coverage**:
```python
class TestPortfolioOptimizers:
    def test_risk_parity_weights_sum_to_one(self):
        """Risk parity weights should sum to 1.0"""

    def test_risk_parity_equal_risk_contribution(self):
        """Each asset should contribute ~equally to risk"""

    def test_min_variance_lowest_volatility(self):
        """Min variance should have lower vol than equal weight"""

    def test_markowitz_highest_sharpe(self):
        """Markowitz should have highest Sharpe ratio"""

    def test_optimizer_convergence(self):
        """All optimizers should converge successfully"""

    def test_optimizer_factory(self):
        """Factory should create correct optimizer instances"""

    def test_invalid_optimizer_raises_error(self):
        """Invalid method should raise ValueError"""
```

**Deliverables Checklist**:
- [ ] Create `portfolio_optimizer.py` with base class
- [ ] Implement Risk Parity optimizer
- [ ] Implement Minimum Variance optimizer
- [ ] Migrate Markowitz optimizer from existing code
- [ ] Implement Equal Weight optimizer
- [ ] Add optimizer factory function
- [ ] Integrate optimizers with rebalancer
- [ ] Write comprehensive unit tests
- [ ] Update API documentation

**Success Criteria**:
- [ ] All optimizers converge in < 5 seconds
- [ ] Risk parity achieves ~equal risk contribution
- [ ] Min variance minimizes portfolio volatility
- [ ] Markowitz maximizes Sharpe ratio
- [ ] 100% test coverage for optimizers
- [ ] Optimizer fallback to equal weights on failure

---

### Phase 4: Per-Asset Parameters 🔜 FUTURE

**Estimated Duration**: 1 week

**Objectives**:
Enable different strategy parameters for each ticker while using the same strategy logic.

**Current Status**: Partially implemented
- ✅ `per_asset_params` parameter in API
- ✅ Basic infrastructure in strategy wrapper
- ❌ Full indicator creation per asset
- ❌ Frontend UI for configuration

**Tasks**:

#### 4.1: Extend Strategy Wrapper
**File**: `backend/src/service/multi_asset_strategy_wrapper.py` (UPDATE)

**Enhancement Needed**:
Currently `_create_indicators()` creates SMA and RSI with custom periods. Need to:
1. Support arbitrary indicators based on user strategy
2. Load actual user strategy code (not just hardcoded SMA/RSI)
3. Create indicators with per-asset parameters

**Example**:
```python
# Frontend sends:
per_asset_params = {
    "AAPL": {"sma_period": 10, "rsi_period": 14},
    "GOOGL": {"sma_period": 20, "rsi_period": 21},
    "MSFT": {"sma_period": 15, "rsi_period": 14}
}

# Strategy creates different indicators per asset
# AAPL gets SMA(10) + RSI(14)
# GOOGL gets SMA(20) + RSI(21)
# MSFT gets SMA(15) + RSI(14)
```

#### 4.2: Update API Request Model
**File**: `backend/src/routes/portfolio_routes.py` (UPDATE)

**Current**: `per_asset_params: dict[str, dict] | None`

**Enhancement**: Add validation and examples in documentation

#### 4.3: Frontend Per-Asset Parameter Editor
**File**: `frontend/src/components/PortfolioBacktest/PerAssetParamsEditor.jsx` (NEW)

**UI Design**:
```jsx
<PerAssetParamsEditor>
  {/* For each ticker, show expandable section */}
  <Collapse>
    <Panel header="AAPL" key="AAPL">
      <Form.Item label="SMA Period">
        <InputNumber value={10} />
      </Form.Item>
      <Form.Item label="RSI Period">
        <InputNumber value={14} />
      </Form.Item>
    </Panel>
    <Panel header="GOOGL" key="GOOGL">
      {/* Same structure */}
    </Panel>
  </Collapse>

  {/* Bulk actions */}
  <Button onClick={applyToAll}>Apply to All</Button>
  <Button onClick={reset}>Reset to Defaults</Button>
</PerAssetParamsEditor>
```

**Deliverables Checklist**:
- [ ] Full indicator creation with per-asset params
- [ ] Strategy code loading and execution
- [ ] Parameter validation in API
- [ ] Frontend parameter editor component
- [ ] Bulk edit actions (apply to all, reset)
- [ ] Integration tests

**Success Criteria**:
- [ ] Different params applied correctly per asset
- [ ] UI allows easy configuration
- [ ] Parameter validation prevents errors
- [ ] Backward compatible with existing strategies

---

### Phase 5: Worker Integration 🔜 FUTURE

**Estimated Duration**: 1 week

**Objectives**:
Integrate multi-asset backtests with the worker pool system for isolation and resource management.

**Current Status**:
- ✅ Multi-asset backtest runs synchronously in executor
- ❌ No worker pool integration
- ❌ No memory monitoring

**Tasks**:

#### 5.1: Multi-Asset Worker
**File**: `backend/src/service/worker/multi_asset_worker.py` (NEW)

**Implementation Pattern** (similar to `backtest_worker.py`):
```python
def execute_multi_asset_task(task: "MultiAssetBacktestTask") -> "MultiAssetBacktestResult":
    """
    Execute multi-asset backtest in isolated worker process.

    This runs in a separate process from the main API,
    providing isolation and resource limits.
    """
    from src.service.multi_asset_backtest import run_multi_asset_backtest

    # Set resource limits
    resource.setrlimit(resource.RLIMIT_AS, (2 * 1024**3, 2 * 1024**3))  # 2GB memory limit

    result = run_multi_asset_backtest(
        tickers=task.tickers,
        weights=task.weights,
        start_date=task.start_date,
        end_date=task.end_date,
        initial_cash=task.initial_cash,
        commission=task.commission,
        per_asset_params=task.per_asset_params,
        rebalance_config=task.rebalance_config,
        optimization_method=task.optimization_method,
        timeframe=task.timeframe,
        save_path=task.chart_save_path,
    )

    return MultiAssetBacktestResult(
        task_id=task.task_id,
        status=TaskStatus.COMPLETED,
        metrics=result
    )
```

#### 5.2: Task Models
**File**: `backend/src/service/worker/task_models.py` (UPDATE)

**Add**:
```python
@dataclass
class MultiAssetBacktestTask:
    task_id: str
    tickers: list[str]
    weights: list[float]
    start_date: str
    end_date: str
    initial_cash: float
    commission: float
    per_asset_params: Optional[dict]
    rebalance_config: Optional[dict]
    optimization_method: str
    timeframe: str
    chart_save_path: Optional[Path]

@dataclass
class MultiAssetBacktestResult:
    task_id: str
    status: TaskStatus
    metrics: dict
    error: Optional[str] = None
```

#### 5.3: Memory Monitoring
**Enhancement**: Add memory usage tracking

```python
import psutil

def monitor_memory_usage():
    """Track memory usage during multi-asset backtest."""
    process = psutil.Process()
    mem_info = process.memory_info()
    logger.info(f"Memory usage: {mem_info.rss / 1024**2:.1f} MB")

    if mem_info.rss > 1.8 * 1024**3:  # 1.8GB warning threshold
        logger.warning("High memory usage detected!")
```

#### 5.4: Integration with Existing Worker Pool
**File**: `backend/src/service/backtest_engine.py` (UPDATE)

**Pattern**: Follow existing `run_backtest_worker()` implementation

**Deliverables Checklist**:
- [ ] Create `multi_asset_worker.py`
- [ ] Add task models
- [ ] Integrate with worker pool
- [ ] Add memory monitoring
- [ ] Set resource limits (2GB memory)
- [ ] Add timeout handling
- [ ] Error recovery and reporting

**Success Criteria**:
- [ ] Multi-asset backtests run in isolated workers
- [ ] Memory usage < 2GB per worker
- [ ] Timeout after 10 minutes
- [ ] Graceful error handling
- [ ] API process remains responsive

---

### Phase 6: Frontend Visualization 🔜 FUTURE

**Estimated Duration**: 1 week

**Objectives**:
Create rich visualizations for multi-asset backtest results.

**Tasks**:

#### 6.1: Equity Curve Chart
**File**: `frontend/src/components/PortfolioBacktest/EquityCurveChart.jsx` (NEW)

**Features**:
- Time-series line chart of portfolio value
- Compare with benchmark (optional)
- Mark rebalancing events on chart
- Zoom/pan controls
- Export to CSV

**Library**: Recharts or ECharts

**Example**:
```jsx
<LineChart data={equityCurveData}>
  <XAxis dataKey="date" />
  <YAxis />
  <Line dataKey="value" stroke="#8884d8" />
  <ReferenceLine x={rebalanceDate} stroke="red" label="Rebalance" />
  <Tooltip />
  <Legend />
</LineChart>
```

#### 6.2: Rebalancing Timeline
**File**: `frontend/src/components/PortfolioBacktest/RebalancingTimeline.jsx` (NEW)

**Features**:
- Vertical timeline showing all rebalancing events
- Each event shows: date, new weights, transaction cost
- Expandable detail view
- Color coding by cost

**Example**:
```jsx
<Timeline mode="left">
  {rebalancingEvents.map(event => (
    <Timeline.Item label={event.date} color={getCostColor(event.cost)}>
      <Card size="small">
        <p>Transaction Cost: ${event.cost}</p>
        <WeightChanges
          from={event.pre_weights}
          to={event.target_weights}
        />
      </Card>
    </Timeline.Item>
  ))}
</Timeline>
```

#### 6.3: Asset Contribution Pie Chart
**File**: `frontend/src/components/PortfolioBacktest/AssetContributionChart.jsx` (NEW)

**Features**:
- Pie chart showing each asset's contribution to total return
- Hover to see details (return %, weight, contribution)
- Toggle between contribution types (return, risk, etc.)

**Example**:
```jsx
<PieChart>
  <Pie
    data={assetContributions}
    dataKey="contribution_pct"
    nameKey="ticker"
    label={renderCustomLabel}
  />
  <Tooltip />
  <Legend />
</PieChart>
```

#### 6.4: Enhanced Results Page
**File**: `frontend/src/pages/PortfolioBacktest.jsx` (UPDATE)

**Add Tab**:
```jsx
<Tabs>
  <TabPane tab="Overview" key="overview">
    <PerformanceOverview />
  </TabPane>
  <TabPane tab="Equity Curve" key="equity">
    <EquityCurveChart data={result.equity_curve} />
  </TabPane>
  <TabPane tab="Rebalancing" key="rebalancing">
    <RebalancingTimeline events={result.rebalancing_events} />
  </TabPane>
  <TabPane tab="Asset Contributions" key="contributions">
    <AssetContributionChart data={result.asset_contributions} />
  </TabPane>
  <TabPane tab="Correlation Matrix" key="correlation">
    <CorrelationHeatmap />
  </TabPane>
</Tabs>
```

#### 6.5: Error Handling
**Enhancement**: Improve error messages for multi-asset specific errors

**Examples**:
- "Data alignment failed: AAPL and GOOGL have only 45% overlap"
- "Optimization failed: Covariance matrix is singular"
- "Rebalancing skipped: Insufficient data for optimization (need 252 days)"

**Deliverables Checklist**:
- [ ] Equity curve chart component
- [ ] Rebalancing timeline component
- [ ] Asset contribution pie chart
- [ ] Correlation matrix heatmap
- [ ] Enhanced results layout
- [ ] Error message improvements
- [ ] Loading states
- [ ] Responsive design

**Success Criteria**:
- [ ] All charts render correctly
- [ ] Interactive features work
- [ ] Mobile responsive
- [ ] Clear error messages
- [ ] Fast rendering (< 1s)

---

## Architecture Reference

### Key Files Created

**Backend Core**:
1. `backend/src/service/multi_asset_backtest.py` - Main engine ✅
2. `backend/src/service/multi_asset_strategy_wrapper.py` - Strategy wrapper ✅
3. `backend/src/service/portfolio_analyzers.py` - Custom analyzers ✅
4. `backend/src/service/portfolio_rebalancer.py` - Rebalancing system ✅
5. `backend/src/service/portfolio_optimizer.py` - Optimization algorithms 🔜

**Backend Infrastructure**:
6. `backend/src/db/models/backtest.py` - Database models (extended) ✅
7. `backend/src/routes/portfolio_routes.py` - API endpoints (extended) ✅
8. `backend/scripts/migrations/add_multi_asset_columns.py` - Migration ✅
9. `backend/src/service/worker/multi_asset_worker.py` - Worker integration 🔜

**Frontend**:
10. `frontend/src/components/PortfolioBacktest/EquityCurveChart.jsx` 🔜
11. `frontend/src/components/PortfolioBacktest/RebalancingTimeline.jsx` 🔜
12. `frontend/src/components/PortfolioBacktest/AssetContributionChart.jsx` 🔜
13. `frontend/src/components/PortfolioBacktest/PerAssetParamsEditor.jsx` 🔜

### API Endpoints

**New**:
- `POST /api/portfolio/multi-asset/backtest` - Run multi-asset backtest ✅

**Existing** (unchanged):
- `POST /api/portfolio/backtest` - Run parallel portfolio backtest
- `GET /api/portfolio/history` - List portfolio history
- `GET /api/portfolio/{id}` - Get portfolio details

---

## Testing Strategy

### Unit Tests
- Portfolio optimizers (Phase 3)
- Rebalancing logic (Phase 2) ✅
- Data alignment (Phase 1) ✅

### Integration Tests
- End-to-end multi-asset backtest
- API endpoint validation
- Database storage

### Performance Tests
- 5-asset backtest < 30 seconds
- 20-asset backtest < 2 minutes
- Memory usage < 2GB

---

## Success Criteria Summary

### Overall Goals
- [ ] 5-asset backtest completes in < 30 seconds
- [ ] Equity curve matches manual calculation (±0.01%)
- [ ] Rebalancing executes on correct dates (100% accuracy)
- [ ] All optimizers converge in < 5 seconds
- [ ] Memory usage < 2GB per worker
- [ ] Zero regression in existing tests
- [ ] Frontend configuration takes < 2 minutes

### Phase-Specific Criteria

**Phase 1 & 2**: ✅ All criteria met

**Phase 3**:
- [ ] All 4 optimizers implemented and tested
- [ ] Convergence success rate > 95%
- [ ] Performance within limits

**Phase 4**:
- [ ] Per-asset parameters work correctly
- [ ] UI is intuitive and fast

**Phase 5**:
- [ ] Worker isolation prevents API blocking
- [ ] Resource limits enforced

**Phase 6**:
- [ ] All visualizations render correctly
- [ ] User experience is smooth

---

## Dependencies

### Python Packages (Already Installed)
- scipy >= 1.16.3 (for optimization)
- numpy (for matrix operations)
- pandas (for data handling)
- backtrader (for backtesting)

### Frontend Packages (May Need)
- recharts or echarts (for charts)
- antd (already installed)

---

## Migration Path

### For Existing Users
1. Existing `/api/portfolio/backtest` continues to work (backward compatible)
2. New `/api/portfolio/multi-asset/backtest` is opt-in
3. Database schema extended (existing data unaffected)
4. Frontend can support both old and new modes

### Deployment Steps
1. Run database migration: `python -m scripts.migrations.add_multi_asset_columns`
2. Deploy backend code
3. Deploy frontend code
4. Test with sample backtests

---

## Future Enhancements (Phase 7+)

### Advanced Features (Not in Current Scope)
- **Ledoit-Wolf Covariance Estimation** - More robust with limited data
- **EWMA Covariance** - Exponentially weighted moving average
- **Black-Litterman Model** - Incorporate views
- **Maximum Diversification** - Maximize diversification ratio
- **Risk Budgeting** - Allocate risk budget across assets
- **Monte Carlo Simulation** - Stress testing
- **Efficient Frontier Visualization** - Risk/return trade-off chart
- **Multi-Period Optimization** - Dynamic programming approach
- **Transaction Cost Optimization** - Minimize turnover

### Performance Optimizations
- Caching of covariance matrices
- Parallel optimization for multiple methods
- Incremental rebalancing (only when necessary)

---

## Contact & Support

For questions or issues with this implementation:
1. See main documentation: [CLAUDE.md](../CLAUDE.md)
2. Check feature plan: [FEATURE-PLAN.md](./FEATURE-PLAN.md)
3. Review implementation plan: [C:\Users\FaryHuo\.claude\plans\flickering-splashing-thimble.md](C:\Users\FaryHuo\.claude\plans\flickering-splashing-thimble.md)

---

**Last Updated**: 2025-12-26
**Status**: Phase 1 & 2 Complete, Phase 3-6 Pending
**Next Action**: Implement Phase 3 (Optimization Methods)
