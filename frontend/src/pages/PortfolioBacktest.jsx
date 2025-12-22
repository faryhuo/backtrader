import { useState, useEffect } from 'react'
import { Card, Button, InputNumber, Table, Spin, Alert, Tag, Select, DatePicker, Space, Empty, Progress } from 'antd'
import {
    PieChartOutlined,
    LineChartOutlined,
    ThunderboltOutlined,
    DeleteOutlined,
    InfoCircleOutlined,
    CheckCircleOutlined,
    CloseCircleOutlined,
    SettingOutlined,
    DownOutlined,
    RightOutlined
} from '@ant-design/icons'
import dayjs from 'dayjs'
import { api } from '../services/api'
import { useTranslation } from 'react-i18next'
import './PortfolioBacktest.css'

function PortfolioBacktest() {
    const { t } = useTranslation()

    // Form state
    const [tickers, setTickers] = useState(['AAPL', 'GOOGL'])
    const [weights, setWeights] = useState([0.5, 0.5])
    const [dateRange, setDateRange] = useState([dayjs('2022-01-01'), dayjs('2023-12-31')])
    const [initialCash, setInitialCash] = useState(100000)
    const [commission, setCommission] = useState(0.0005)
    const [stake] = useState(100)
    const [strategies, setStrategies] = useState([])
    const [selectedStrategy, setSelectedStrategy] = useState('')

    // Strategy params state
    const [strategyParams, setStrategyParams] = useState([])
    const [paramOverrides, setParamOverrides] = useState({})
    const [paramsExpanded, setParamsExpanded] = useState(true)

    // Result state
    const [result, setResult] = useState(null)
    const [loading, setLoading] = useState(false)
    const [error, setError] = useState(null)

    // Load strategies on mount
    useEffect(() => {
        const loadStrategies = async () => {
            try {
                const names = await api.getStrategies()
                setStrategies(names)
                if (names.length > 0 && !selectedStrategy) {
                    setSelectedStrategy(names[0])
                }
            } catch (err) {
                console.error('Failed to load strategies:', err)
            }
        }
        loadStrategies()
    }, [])

    // Fetch strategy params when strategy changes
    useEffect(() => {
        const fetchParams = async () => {
            if (!selectedStrategy) {
                setStrategyParams([])
                setParamOverrides({})
                return
            }
            try {
                const data = await api.getStrategyParams(selectedStrategy)
                setStrategyParams(data.params || [])
                // Initialize overrides with default values
                const defaults = {}
                    ; (data.params || []).forEach(p => {
                        defaults[p.name] = p.value
                    })
                setParamOverrides(defaults)
            } catch (err) {
                console.warn('Failed to fetch strategy params:', err)
                setStrategyParams([])
                setParamOverrides({})
            }
        }
        fetchParams()
    }, [selectedStrategy])

    // Handle param change
    const handleParamChange = (name, value, type) => {
        let parsedValue = value
        if (type === 'int') {
            parsedValue = parseInt(value, 10) || 0
        } else if (type === 'float') {
            parsedValue = parseFloat(value) || 0
        }
        setParamOverrides({ ...paramOverrides, [name]: parsedValue })
    }

    // Add a ticker
    const addTicker = () => {
        setTickers([...tickers, ''])
        setWeights([...weights, 0])
    }

    // Remove a ticker
    const removeTicker = (index) => {
        if (tickers.length <= 1) return
        setTickers(tickers.filter((_, i) => i !== index))
        setWeights(weights.filter((_, i) => i !== index))
    }

    // Update a ticker
    const updateTicker = (index, value) => {
        const newTickers = [...tickers]
        newTickers[index] = value.toUpperCase()
        setTickers(newTickers)
    }

    // Update a weight
    const updateWeight = (index, value) => {
        const newWeights = [...weights]
        newWeights[index] = value || 0
        setWeights(newWeights)
    }

    // Normalize weights to sum to 100
    const normalizeWeights = () => {
        const total = weights.reduce((a, b) => a + b, 0)
        if (total > 0) {
            setWeights(weights.map(w => Math.round((w / total) * 100) / 100))
        }
    }

    // Equal weights
    const equalWeights = () => {
        const equalWeight = Math.round((1 / tickers.length) * 100) / 100
        setWeights(tickers.map(() => equalWeight))
    }

    // Run portfolio backtest
    const runBacktest = async () => {
        // Validate
        const validTickers = tickers.filter(t => t.trim())
        if (validTickers.length === 0) {
            setError(t('portfolio.validation.no_ticker', 'Please enter at least one ticker'))
            return
        }
        if (!dateRange || dateRange.length !== 2) {
            setError(t('portfolio.validation.no_date_range', 'Please select a date range'))
            return
        }

        setLoading(true)
        setError(null)
        setResult(null)

        try {
            // Build params object only if there are overrides
            const paramsToSend = Object.keys(paramOverrides).length > 0 ? paramOverrides : null

            const data = await api.runPortfolioBacktest({
                tickers: validTickers,
                weights: weights.slice(0, validTickers.length),
                start_date: dateRange[0].format('YYYY-MM-DD'),
                end_date: dateRange[1].format('YYYY-MM-DD'),
                initial_cash: initialCash,
                commission: commission,
                stake: stake,
                strategy_name: selectedStrategy || null,
                params: paramsToSend
            })
            setResult(data)
        } catch (err) {
            setError(err?.message || t('portfolio.error.run_failed', 'Portfolio backtest failed'))
        } finally {
            setLoading(false)
        }
    }

    // Calculate total weight
    const totalWeight = weights.reduce((a, b) => a + b, 0)
    const isWeightValid = Math.abs(totalWeight - 1) < 0.01

    return (
        <div className="portfolio-page">
            <div className="portfolio-header">
                <h2><PieChartOutlined /> {t('portfolio.title', 'Portfolio Backtest')}</h2>
                <p>{t('portfolio.description', 'Run backtests on multiple assets with custom weight allocation')}</p>
            </div>

            {/* Configuration Card */}
            <Card className="portfolio-config-card" title={
                <span><LineChartOutlined /> {t('portfolio.configuration', 'Portfolio Configuration')}</span>
            }>
                {/* Ticker & Weight Table */}
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

                {/* Parameters Section */}
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

                {/* Strategy Parameters Section */}
                {strategyParams.length > 0 && (
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
                )}

                <div className="run-button-container">
                    <Button
                        type="primary"
                        size="large"
                        icon={<ThunderboltOutlined />}
                        onClick={runBacktest}
                        loading={loading}
                    >
                        {t('portfolio.run_backtest', 'Run Portfolio Backtest')}
                    </Button>
                </div>

                {error && <Alert type="error" message={error} showIcon style={{ marginTop: 16 }} />}
            </Card>

            {/* Results Section */}
            {loading && (
                <Card className="portfolio-results-card">
                    <div className="loading-container">
                        <Spin size="large" />
                        <p>{t('portfolio.running', 'Running portfolio backtest...')}</p>
                    </div>
                </Card>
            )}

            {result && !loading && (
                <div className="results-section">
                    {/* Portfolio Metrics Card */}
                    <Card className="portfolio-metrics-card" title={
                        <span><PieChartOutlined /> {t('portfolio.portfolio_metrics', 'Portfolio Metrics')}</span>
                    }>
                        <div className="metrics-grid">
                            <div className="metric-item">
                                <span className="metric-label">{t('portfolio.final_value', 'Final Value')}</span>
                                <span className="metric-value">${result.portfolio_metrics?.final_value?.toLocaleString()}</span>
                            </div>
                            <div className="metric-item">
                                <span className="metric-label">{t('portfolio.total_return', 'Total Return')}</span>
                                <span className={`metric-value ${result.portfolio_metrics?.total_return >= 0 ? 'positive' : 'negative'}`}>
                                    {result.portfolio_metrics?.total_return?.toFixed(2)}%
                                </span>
                            </div>
                            <div className="metric-item">
                                <span className="metric-label">{t('portfolio.sharpe', 'Weighted Sharpe')}</span>
                                <span className="metric-value">{result.portfolio_metrics?.weighted_sharpe?.toFixed(4) || 'N/A'}</span>
                            </div>
                            <div className="metric-item">
                                <span className="metric-label">{t('portfolio.max_drawdown', 'Max Drawdown')}</span>
                                <span className="metric-value negative">{result.portfolio_metrics?.max_drawdown?.toFixed(2)}%</span>
                            </div>
                        </div>
                    </Card>

                    {/* Individual Results Table */}
                    <Card className="individual-results-card" title={
                        <span><LineChartOutlined /> {t('portfolio.individual_results', 'Individual Asset Results')}</span>
                    }>
                        <Table
                            dataSource={result.individual_results}
                            rowKey="ticker"
                            size="small"
                            pagination={false}
                            columns={[
                                {
                                    title: t('portfolio.table.ticker', 'Ticker'),
                                    dataIndex: 'ticker',
                                    render: ticker => <Tag color="blue">{ticker}</Tag>
                                },
                                {
                                    title: t('portfolio.table.weight', 'Weight'),
                                    dataIndex: 'weight',
                                    render: w => `${(w * 100).toFixed(0)}%`
                                },
                                {
                                    title: t('portfolio.table.status', 'Status'),
                                    dataIndex: 'success',
                                    render: s => s
                                        ? <CheckCircleOutlined style={{ color: '#52c41a' }} />
                                        : <CloseCircleOutlined style={{ color: '#ff4d4f' }} />
                                },
                                {
                                    title: t('portfolio.table.initial', 'Initial'),
                                    dataIndex: 'initial_cash',
                                    render: v => v ? `$${v.toLocaleString()}` : '-'
                                },
                                {
                                    title: t('portfolio.table.final', 'Final'),
                                    dataIndex: 'final_value',
                                    render: v => v ? `$${v.toLocaleString()}` : '-'
                                },
                                {
                                    title: t('portfolio.table.return', 'Return'),
                                    dataIndex: 'return',
                                    render: r => r != null
                                        ? <span className={r >= 0 ? 'positive' : 'negative'}>{r.toFixed(2)}%</span>
                                        : '-'
                                },
                                {
                                    title: t('portfolio.table.sharpe', 'Sharpe'),
                                    dataIndex: 'sharpe',
                                    render: s => s?.toFixed(4) || '-'
                                },
                            ]}
                        />
                    </Card>

                    {/* Correlation Matrix */}
                    {result.correlation && !result.correlation.error && (
                        <Card className="correlation-card" title={
                            <span>
                                <InfoCircleOutlined /> {t('portfolio.correlation', 'Correlation Matrix')}
                            </span>
                        }>
                            <div className="correlation-matrix">
                                <table>
                                    <thead>
                                        <tr>
                                            <th></th>
                                            {result.correlation.tickers?.map(t => <th key={t}>{t}</th>)}
                                        </tr>
                                    </thead>
                                    <tbody>
                                        {result.correlation.matrix?.map((row, i) => (
                                            <tr key={i}>
                                                <th>{result.correlation.tickers?.[i]}</th>
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
                    )}

                    {/* Optimization Suggestions */}
                    {result.optimization && !result.optimization.error && (
                        <Card className="optimization-card" title={
                            <span>
                                <ThunderboltOutlined /> {t('portfolio.optimization', 'Optimization Suggestions')}
                            </span>
                        }>
                            <div className="optimization-content">
                                <p className="optimization-intro">
                                    {t('portfolio.optimization_intro', 'Based on historical returns and covariance, here are the optimal weights for maximum Sharpe ratio:')}
                                </p>
                                <div className="optimal-weights">
                                    {result.optimization.tickers?.map((ticker, i) => (
                                        <div key={ticker} className="optimal-weight-item">
                                            <Tag color="green">{ticker}</Tag>
                                            <span>{((result.optimization.optimal_weights?.[i] || 0) * 100).toFixed(1)}%</span>
                                        </div>
                                    ))}
                                </div>
                                {result.optimization.expected_return && (
                                    <div className="optimization-metrics">
                                        <span>{t('portfolio.optimization_metrics.expected_return', 'Expected Return')}: {(result.optimization.expected_return * 100).toFixed(2)}%</span>
                                        <span>{t('portfolio.optimization_metrics.expected_volatility', 'Expected Volatility')}: {(result.optimization.expected_volatility * 100).toFixed(2)}%</span>
                                        <span>{t('portfolio.optimization_metrics.sharpe_ratio', 'Sharpe Ratio')}: {result.optimization.sharpe_ratio?.toFixed(4)}</span>
                                    </div>
                                )}
                            </div>
                        </Card>
                    )}

                    {/* Portfolio Chart */}
                    {result.plot_url && (
                        <Card className="chart-card" title={t('portfolio.chart', 'Portfolio Chart')}>
                            <img src={result.plot_url} alt={t('portfolio.chart_alt', 'Portfolio Chart')} className="portfolio-chart" />
                        </Card>
                    )}
                </div>
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
    )
}

export default PortfolioBacktest
