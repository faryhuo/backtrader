import { useState, useEffect } from 'react';
import { Card, Button, InputNumber, Table, Spin, Alert, Tag, Select, DatePicker, Space, Empty, Progress } from 'antd';
import {
    PieChartOutlined,
    LineChartOutlined,
    ThunderboltOutlined,
    DeleteOutlined,
    InfoCircleOutlined,
    SettingOutlined,
    DownOutlined,
    RightOutlined
} from '@ant-design/icons';
import dayjs from 'dayjs';
import { api } from '../services/api';
import { useTranslation } from 'react-i18next';
import { useTickerWeights } from '../hooks/useTickerWeights';
import { useStrategyParams } from '../hooks/useStrategyParams';
import { useBacktest } from '../hooks/useBacktest';
import { getIndividualResultsColumns } from '../utils/tableColumns';
import './PortfolioBacktest.css';

function PortfolioBacktest() {
    const { t } = useTranslation();

    // Form state
    const [dateRange, setDateRange] = useState([dayjs('2022-01-01'), dayjs('2023-12-31')]);
    const [initialCash, setInitialCash] = useState(100000);
    const [commission, setCommission] = useState(0.0005);
    const [stake] = useState(100);
    const [strategies, setStrategies] = useState([]);
    const [selectedStrategy, setSelectedStrategy] = useState('');
    const [paramsExpanded, setParamsExpanded] = useState(true);

    // Use custom hooks
    const {
        tickers,
        weights,
        addTicker,
        removeTicker,
        updateTicker,
        updateWeight,
        normalizeWeights,
        equalWeights,
        totalWeight,
        isWeightValid,
        validTickers,
    } = useTickerWeights();

    const {
        strategyParams,
        paramOverrides,
        handleParamChange,
    } = useStrategyParams(selectedStrategy);

    const {
        result,
        loading,
        error,
        runPortfolioBacktest,
    } = useBacktest();

    // Load strategies on mount
    useEffect(() => {
        const loadStrategies = async () => {
            try {
                const names = await api.getStrategies();
                setStrategies(names);
                if (names.length > 0 && !selectedStrategy) {
                    setSelectedStrategy(names[0]);
                }
            } catch (err) {
                console.error('Failed to load strategies:', err);
            }
        };
        loadStrategies();
        // eslint-disable-next-line react-hooks/exhaustive-deps
    }, []);

    // Run portfolio backtest handler
    const handleRunBacktest = async () => {
        if (!dateRange || dateRange.length !== 2) {
            return;
        }

        await runPortfolioBacktest({
            tickers: validTickers,
            weights,
            startDate: dateRange[0].format('YYYY-MM-DD'),
            endDate: dateRange[1].format('YYYY-MM-DD'),
            initialCash,
            commission,
            stake,
            selectedStrategy,
            paramOverrides,
        }, t);
    };

    // Get individual results columns
    const individualResultsColumns = getIndividualResultsColumns({ t });

    return (
        <div className="portfolio-page">
            <PortfolioHeader t={t} />

            <Card className="portfolio-config-card" title={
                <span><LineChartOutlined /> {t('portfolio.configuration', 'Portfolio Configuration')}</span>
            }>
                <TickerWeightSection
                    t={t}
                    tickers={tickers}
                    weights={weights}
                    totalWeight={totalWeight}
                    isWeightValid={isWeightValid}
                    addTicker={addTicker}
                    removeTicker={removeTicker}
                    updateTicker={updateTicker}
                    updateWeight={updateWeight}
                    normalizeWeights={normalizeWeights}
                    equalWeights={equalWeights}
                />

                <ParametersSection
                    t={t}
                    dateRange={dateRange}
                    setDateRange={setDateRange}
                    strategies={strategies}
                    selectedStrategy={selectedStrategy}
                    setSelectedStrategy={setSelectedStrategy}
                    initialCash={initialCash}
                    setInitialCash={setInitialCash}
                    commission={commission}
                    setCommission={setCommission}
                />

                {strategyParams.length > 0 && (
                    <StrategyParamsSection
                        t={t}
                        strategyParams={strategyParams}
                        paramOverrides={paramOverrides}
                        handleParamChange={handleParamChange}
                        paramsExpanded={paramsExpanded}
                        setParamsExpanded={setParamsExpanded}
                    />
                )}

                <div className="run-button-container">
                    <Button
                        type="primary"
                        size="large"
                        icon={<ThunderboltOutlined />}
                        onClick={handleRunBacktest}
                        loading={loading}
                    >
                        {t('portfolio.run_backtest', 'Run Portfolio Backtest')}
                    </Button>
                </div>

                {error && <Alert type="error" message={error} showIcon style={{ marginTop: 16 }} />}
            </Card>

            {loading && (
                <Card className="portfolio-results-card">
                    <div className="loading-container">
                        <Spin size="large" />
                        <p>{t('portfolio.running', 'Running portfolio backtest...')}</p>
                    </div>
                </Card>
            )}

            {result && !loading && (
                <ResultsSection t={t} result={result} columns={individualResultsColumns} />
            )}

            {!result && !loading && (
                <Card className="empty-state-card">
                    <Empty
                        image={<PieChartOutlined style={{ fontSize: 64, color: '#666' }} />}
                        description={t('portfolio.empty_state', 'Configure your portfolio above and run a backtest to see results')}
                    />
                </Card>
            )}
        </div>
    );
}

// Header component
function PortfolioHeader({ t }) {
    return (
        <div className="portfolio-header">
            <h2><PieChartOutlined /> {t('portfolio.title', 'Portfolio Backtest')}</h2>
            <p>{t('portfolio.description', 'Run backtests on multiple assets with custom weight allocation')}</p>
        </div>
    );
}

// Ticker & Weight Section
function TickerWeightSection({
    t, tickers, weights, totalWeight, isWeightValid,
    addTicker, removeTicker, updateTicker, updateWeight, normalizeWeights, equalWeights
}) {
    return (
        <div className="ticker-weight-section">
            <div className="section-header">
                <h4>{t('portfolio.assets', 'Assets & Weights')}</h4>
                <Space>
                    <Button size="small" onClick={equalWeights}>
                        {t('portfolio.equal_weights', 'Equal Weights')}
                    </Button>
                    <Button size="small" onClick={normalizeWeights}>
                        {t('portfolio.normalize', 'Normalize')}
                    </Button>
                    <Button type="dashed" size="small" onClick={addTicker}>
                        + {t('portfolio.add_ticker', 'Add Ticker')}
                    </Button>
                </Space>
            </div>

            <div className="ticker-weight-grid">
                {tickers.map((ticker, index) => (
                    <div key={index} className="ticker-weight-row">
                        <Select
                            mode="tags"
                            className="ticker-input"
                            placeholder="AAPL"
                            value={ticker ? [ticker] : []}
                            onChange={(values) => updateTicker(index, values[values.length - 1] || '')}
                            tokenSeparators={[',']}
                            maxTagCount={1}
                            allowClear
                        />
                        <InputNumber
                            className="weight-input"
                            min={0}
                            max={1}
                            step={0.01}
                            value={weights[index]}
                            onChange={(v) => updateWeight(index, v)}
                            formatter={v => `${(v * 100).toFixed(0)}%`}
                            parser={v => parseFloat(v.replace('%', '')) / 100}
                        />
                        <Button
                            type="text"
                            danger
                            icon={<DeleteOutlined />}
                            onClick={() => removeTicker(index)}
                            disabled={tickers.length <= 1}
                        />
                    </div>
                ))}
            </div>

            <div className="weight-status">
                <Progress
                    percent={Math.min(totalWeight * 100, 100)}
                    status={isWeightValid ? 'success' : 'exception'}
                    format={() => `${(totalWeight * 100).toFixed(0)}%`}
                />
                {!isWeightValid && (
                    <span className="weight-warning">
                        {t('portfolio.weight_warning', 'Weights will be normalized to 100%')}
                    </span>
                )}
            </div>
        </div>
    );
}

// Parameters Section
function ParametersSection({
    t, dateRange, setDateRange, strategies, selectedStrategy, setSelectedStrategy,
    initialCash, setInitialCash, commission, setCommission
}) {
    return (
        <div className="params-section">
            <div className="param-group">
                <label>{t('portfolio.date_range', 'Date Range')}</label>
                <DatePicker.RangePicker
                    value={dateRange}
                    onChange={setDateRange}
                    format="YYYY-MM-DD"
                />
            </div>
            <div className="param-group">
                <label>{t('portfolio.strategy', 'Strategy')}</label>
                <Select
                    value={selectedStrategy}
                    onChange={setSelectedStrategy}
                    style={{ width: 200 }}
                    options={strategies.map(s => ({ value: s, label: s }))}
                />
            </div>
            <div className="param-group">
                <label>{t('portfolio.initial_cash', 'Initial Cash')}</label>
                <InputNumber
                    value={initialCash}
                    onChange={setInitialCash}
                    min={1000}
                    step={10000}
                    formatter={v => `$ ${v}`.replace(/\B(?=(\d{3})+(?!\d))/g, ',')}
                    parser={v => v.replace(/\$\s?|(,*)/g, '')}
                />
            </div>
            <div className="param-group">
                <label>{t('portfolio.commission', 'Commission')}</label>
                <InputNumber
                    value={commission}
                    onChange={setCommission}
                    min={0}
                    max={0.1}
                    step={0.0001}
                    formatter={v => `${(v * 100).toFixed(2)}%`}
                    parser={v => parseFloat(v.replace('%', '')) / 100}
                />
            </div>
        </div>
    );
}

// Strategy Parameters Section
function StrategyParamsSection({
    t, strategyParams, paramOverrides, handleParamChange, paramsExpanded, setParamsExpanded
}) {
    return (
        <div className="strategy-params-section">
            <div
                className="strategy-params-header"
                onClick={() => setParamsExpanded(!paramsExpanded)}
            >
                <span className="params-toggle-icon">
                    {paramsExpanded ? <DownOutlined /> : <RightOutlined />}
                </span>
                <SettingOutlined />
                <span>{t('portfolio.strategy_params', 'Strategy Parameters')}</span>
                <span className="params-count">({strategyParams.length})</span>
            </div>
            {paramsExpanded && (
                <div className="strategy-params-grid">
                    {strategyParams.map((param) => (
                        <div key={param.name} className="strategy-param-item">
                            <label htmlFor={`param-${param.name}`}>
                                {param.name}
                                <span className="param-type">({param.type})</span>
                            </label>
                            <InputNumber
                                id={`param-${param.name}`}
                                step={param.type === 'float' ? 0.01 : 1}
                                value={paramOverrides[param.name] ?? param.value}
                                onChange={(v) => handleParamChange(param.name, v, param.type)}
                                style={{ width: '100%' }}
                            />
                        </div>
                    ))}
                </div>
            )}
        </div>
    );
}

// Results Section
function ResultsSection({ t, result, columns }) {
    return (
        <div className="results-section">
            <PortfolioMetricsCard t={t} metrics={result.portfolio_metrics} />

            <Card className="individual-results-card" title={
                <span><LineChartOutlined /> {t('portfolio.individual_results', 'Individual Asset Results')}</span>
            }>
                <Table
                    dataSource={result.individual_results}
                    rowKey="ticker"
                    size="small"
                    pagination={false}
                    columns={columns}
                />
            </Card>

            {result.correlation && !result.correlation.error && (
                <CorrelationCard t={t} correlation={result.correlation} />
            )}

            {result.optimization && !result.optimization.error && (
                <OptimizationCard t={t} optimization={result.optimization} />
            )}

            {result.plot_url && (
                <Card className="chart-card" title={t('portfolio.chart', 'Portfolio Chart')}>
                    <img src={result.plot_url} alt={t('portfolio.chart_alt', 'Portfolio Chart')} className="portfolio-chart" />
                </Card>
            )}
        </div>
    );
}

// Portfolio Metrics Card
function PortfolioMetricsCard({ t, metrics }) {
    return (
        <Card className="portfolio-metrics-card" title={
            <span><PieChartOutlined /> {t('portfolio.portfolio_metrics', 'Portfolio Metrics')}</span>
        }>
            <div className="metrics-grid">
                <div className="metric-item">
                    <span className="metric-label">{t('portfolio.final_value', 'Final Value')}</span>
                    <span className="metric-value">${metrics?.final_value?.toLocaleString()}</span>
                </div>
                <div className="metric-item">
                    <span className="metric-label">{t('portfolio.total_return', 'Total Return')}</span>
                    <span className={`metric-value ${metrics?.total_return >= 0 ? 'positive' : 'negative'}`}>
                        {metrics?.total_return?.toFixed(2)}%
                    </span>
                </div>
                <div className="metric-item">
                    <span className="metric-label">{t('portfolio.sharpe', 'Weighted Sharpe')}</span>
                    <span className="metric-value">{metrics?.weighted_sharpe?.toFixed(4) || 'N/A'}</span>
                </div>
                <div className="metric-item">
                    <span className="metric-label">{t('portfolio.max_drawdown', 'Max Drawdown')}</span>
                    <span className="metric-value negative">{metrics?.max_drawdown?.toFixed(2)}%</span>
                </div>
            </div>
        </Card>
    );
}

// Correlation Card
function CorrelationCard({ t, correlation }) {
    return (
        <Card className="correlation-card" title={
            <span><InfoCircleOutlined /> {t('portfolio.correlation', 'Correlation Matrix')}</span>
        }>
            <div className="correlation-matrix">
                <table>
                    <thead>
                        <tr>
                            <th></th>
                            {correlation.tickers?.map(ticker => <th key={ticker}>{ticker}</th>)}
                        </tr>
                    </thead>
                    <tbody>
                        {correlation.matrix?.map((row, i) => (
                            <tr key={i}>
                                <th>{correlation.tickers?.[i]}</th>
                                {row.map((val, j) => (
                                    <td
                                        key={j}
                                        style={{
                                            backgroundColor: `rgba(${val > 0 ? '0,255,0' : '255,0,0'}, ${Math.abs(val) * 0.5})`,
                                        }}
                                    >
                                        {val.toFixed(2)}
                                    </td>
                                ))}
                            </tr>
                        ))}
                    </tbody>
                </table>
            </div>
        </Card>
    );
}

// Optimization Card
function OptimizationCard({ t, optimization }) {
    return (
        <Card className="optimization-card" title={
            <span><ThunderboltOutlined /> {t('portfolio.optimization', 'Optimization Suggestions')}</span>
        }>
            <div className="optimization-content">
                <p className="optimization-intro">
                    {t('portfolio.optimization_intro', 'Based on historical returns and covariance, here are the optimal weights for maximum Sharpe ratio:')}
                </p>
                <div className="optimal-weights">
                    {optimization.tickers?.map((ticker, i) => (
                        <div key={ticker} className="optimal-weight-item">
                            <Tag color="green">{ticker}</Tag>
                            <span>{((optimization.optimal_weights?.[i] || 0) * 100).toFixed(1)}%</span>
                        </div>
                    ))}
                </div>
                {optimization.expected_return && (
                    <div className="optimization-metrics">
                        <span>{t('portfolio.optimization_metrics.expected_return', 'Expected Return')}: {(optimization.expected_return * 100).toFixed(2)}%</span>
                        <span>{t('portfolio.optimization_metrics.expected_volatility', 'Expected Volatility')}: {(optimization.expected_volatility * 100).toFixed(2)}%</span>
                        <span>{t('portfolio.optimization_metrics.sharpe_ratio', 'Sharpe Ratio')}: {optimization.sharpe_ratio?.toFixed(4)}</span>
                    </div>
                )}
            </div>
        </Card>
    );
}

export default PortfolioBacktest;
