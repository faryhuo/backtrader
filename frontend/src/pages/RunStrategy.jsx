
import { useState, useEffect } from 'react'
import { Select, Button, Space, message, Tabs, Tag } from 'antd'
import '../components/RunStrategy/RunStrategy.css'
import { api } from '../services/api'
import { performFullStrategyAnalysis, getAvailableModels } from '../services/aiAnalysis'
import StrategyConfigForm from '../components/RunStrategy/StrategyConfigForm'
import PerformanceOverview from '../components/RunStrategy/PerformanceOverview'
import TradeLog from '../components/RunStrategy/TradeLog'
import StrategyPlot from '../components/RunStrategy/StrategyPlot'
import DeepAnalysis from '../components/DeepAnalysis'
import AIInsight from '../components/RunStrategy/AIInsight'

import {
    RobotOutlined,
    LineChartOutlined,
    SwapOutlined,
    BarChartOutlined,
    BulbOutlined,
    ExperimentOutlined,
    CodeOutlined,
    StockOutlined,
    CalendarOutlined,
    DollarOutlined
} from '@ant-design/icons'
import { useTranslation } from 'react-i18next'

function RunStrategy() {
    const { t } = useTranslation();
    // Backtest State
    const [ticker, setTicker] = useState('AAPL')
    const [startDate, setStartDate] = useState('2022-01-01')
    const [endDate, setEndDate] = useState('2023-12-31')
    const [initialCash, setInitialCash] = useState(100000.0)
    const [commission, setCommission] = useState(0.0005)
    const [stake, setStake] = useState(100)
    const [strategies, setStrategies] = useState([])
    const [selectedStrategy, setSelectedStrategy] = useState('')
    const [strategyParams, setStrategyParams] = useState([])
    const [paramOverrides, setParamOverrides] = useState({})
    const [result, setResult] = useState(null)
    const [loading, setLoading] = useState(false)
    const [error, setError] = useState(null)

    // AI Analysis State
    const [aiLoading, setAiLoading] = useState(false)
    const [analyses, setAnalyses] = useState({})
    const [activeTab, setActiveTab] = useState(null)
    const availableModels = getAvailableModels()
    const [selectedModel, setSelectedModel] = useState(availableModels[0] || 'gpt-4o')

    // Strategy Code State
    const [strategyCode, setStrategyCode] = useState('')

    useEffect(() => {
        const init = async () => {
            const names = await fetchStrategies();
            if (names && names.length > 0) {
                if (!names.includes(selectedStrategy)) {
                    setSelectedStrategy(names[0]);
                }
            }
        }
        init();
        // eslint-disable-next-line react-hooks/exhaustive-deps
    }, [])

    useEffect(() => {
        const fetchStrategyDetails = async () => {
            if (!selectedStrategy) {
                setStrategyParams([]);
                setParamOverrides({});
                setStrategyCode('');
                return;
            }
            try {
                const data = await api.getStrategyParams(selectedStrategy);
                setStrategyParams(data.params || []);
                const defaults = {};
                (data.params || []).forEach(p => {
                    defaults[p.name] = p.value;
                });
                setParamOverrides(defaults);

                const strategyData = await api.getStrategy(selectedStrategy);
                if (strategyData && strategyData.code) {
                    setStrategyCode(strategyData.code);
                }
            } catch (err) {
                console.warn('Failed to fetch strategy details:', err);
            }
        };
        fetchStrategyDetails();
    }, [selectedStrategy])

    const fetchStrategies = async () => {
        try {
            const names = await api.getStrategies()
            setStrategies(names)
            return names
        } catch (err) {
            console.error("Failed to fetch strategies", err)
            return []
        }
    }

    const handleBacktest = async (e) => {
        e.preventDefault()
        if (!selectedStrategy) {
            setError('Please select or create a strategy first.')
            return
        }
        setLoading(true)
        setError(null)
        setResult(null)
        setAnalyses({})
        setActiveTab(null)

        try {
            const paramsToSend = Object.keys(paramOverrides).length > 0 ? paramOverrides : null;

            const data = await api.runBacktest({
                ticker,
                start_date: startDate,
                end_date: endDate,
                initial_cash: parseFloat(initialCash),
                commission: parseFloat(commission),
                stake: parseInt(stake, 10),
                strategy_name: selectedStrategy,
                params: paramsToSend
            })
            setResult(data)
        } catch (err) {
            console.error(err)
            setError(err.message || 'An error occurred')
        } finally {
            setLoading(false)
        }
    }

    const handleAIAnalysis = async () => {
        if (!result || !result.plot_url) {
            if (!result) return;
        }
        setAiLoading(true)

        try {
            const data = await performFullStrategyAnalysis({
                result: {
                    metrics: result.metrics || result,
                    plot_url: result.plot_url,
                },
                strategyName: selectedStrategy,
                ticker: ticker,
                startDate: startDate,
                endDate: endDate,
                model: selectedModel,
                initialStrategyCode: strategyCode
            })

            setAnalyses(prev => {
                const newState = { ...prev, [selectedModel]: data.analysis }
                return newState
            })
            setActiveTab(selectedModel)
        } catch (err) {
            console.error(err)
            message.error("Failed to perform AI analysis: " + err.message)
        } finally {
            setAiLoading(false)
        }
    }

    const tradeList = result?.metrics?.trade_details?.trades || result?.trade_details?.trades || []
    const metrics = result?.metrics || result || {}
    const plotUrl = result?.plot_url || metrics.plot_url

    // Build tab items for Ant Design Tabs
    const tabItems = [
        {
            key: 'overview',
            label: <span><LineChartOutlined className="tab-icon" /> {t('history.tab_overview', 'Overview')}</span>,
            children: <PerformanceOverview result={result} />
        },
        {
            key: 'chart',
            label: <span><BarChartOutlined className="tab-icon" /> {t('history.tab_chart', 'Chart')}</span>,
            children: (
                <div style={{ padding: '20px 0' }}>
                    <StrategyPlot result={result} />
                </div>
            )
        },
        {
            key: 'trades',
            label: <span><SwapOutlined className="tab-icon" /> {t('history.tab_trades', 'Trades')}</span>,
            children: <TradeLog trades={tradeList} />
        },
        {
            key: 'ai_insight',
            label: <span><BulbOutlined className="tab-icon" /> {t('history.tab_ai_insight', 'AI Insight')}</span>,
            children: (
                <div style={{ padding: '20px' }}>
                    <div style={{
                        display: 'flex',
                        justifyContent: 'space-between',
                        alignItems: 'center',
                        padding: '1.25rem 2rem',
                        background: 'rgba(255, 255, 255, 0.03)',
                        borderRadius: '12px',
                        marginBottom: '1.5rem',
                        border: '1px solid rgba(255, 255, 255, 0.05)'
                    }}>
                        <div style={{ display: 'flex', alignItems: 'center', gap: '1rem' }}>
                            <RobotOutlined style={{ fontSize: '1.5rem', color: '#22d3ee' }} />
                            <span style={{ fontSize: '1.1rem', fontWeight: 600, color: '#e2e8f0' }}>
                                {t('strategy_plot.ai_interpretation', 'AI Analysis')}
                            </span>
                        </div>
                        <div style={{ display: 'flex', gap: '1rem', alignItems: 'center' }}>
                            <Select
                                value={selectedModel}
                                onChange={(value) => setSelectedModel(value)}
                                style={{ width: 180 }}
                                className="custom-select"
                                bordered={false}
                                dropdownStyle={{ background: '#1a1b23', border: '1px solid #374151' }}
                            >
                                {availableModels.map(m => (
                                    <Select.Option key={m} value={m}>
                                        <Space>
                                            <RobotOutlined />
                                            {m}
                                        </Space>
                                    </Select.Option>
                                ))}
                            </Select>
                            <Button
                                type="primary"
                                icon={<RobotOutlined />}
                                onClick={handleAIAnalysis}
                                loading={aiLoading}
                                disabled={!plotUrl && !result}
                                style={{
                                    height: '40px',
                                    padding: '0 24px',
                                    borderRadius: '8px',
                                    background: 'linear-gradient(135deg, #22d3ee 0%, #0891b2 100%)',
                                    border: 'none',
                                    boxShadow: '0 4px 6px -1px rgba(34, 211, 238, 0.2)'
                                }}
                            >
                                {aiLoading ? t('strategy_plot.interpreting', 'Analysing...') : t('strategy_plot.ai_interpretation', 'Start Analysis')}
                            </Button>
                        </div>
                    </div>

                    {Object.keys(analyses).length > 0 ? (
                        <AIInsight
                            analyses={analyses}
                            activeTab={activeTab || Object.keys(analyses)[0]}
                            onTabChange={setActiveTab}
                        />
                    ) : (
                        <div style={{
                            textAlign: 'center',
                            padding: '2rem',
                            color: '#888'
                        }}>
                            {t('history.no_ai_analysis', 'No AI analysis available. Click the button above to generate one.')}
                        </div>
                    )}
                </div>
            )
        },
        {
            key: 'deep_analysis',
            label: <span><ExperimentOutlined className="tab-icon" /> {t('history.tab_deep_analysis', 'Deep Analysis')}</span>,
            children: result?.backtest_id ? (
                <DeepAnalysis backtest={{
                    backtest_id: result.backtest_id,
                    ticker,
                    start_date: startDate,
                    end_date: endDate,
                    initial_cash: initialCash
                }} />
            ) : (
                <div style={{ padding: '2rem', textAlign: 'center', color: '#888' }}>
                    {t('history.save_first_hint', 'Please run backtest again to generate Deep Analysis.')}
                </div>
            )
        }
    ];

    // Add strategy code tab if code exists
    if (strategyCode) {
        tabItems.push({
            key: 'strategy_code',
            label: <span><CodeOutlined className="tab-icon" /> {t('history.tab_strategy_code', 'Strategy Code')}</span>,
            children: (
                <div style={{ padding: '20px' }}>
                    {paramOverrides && Object.keys(paramOverrides).length > 0 && (
                        <div style={{
                            background: 'rgba(34, 211, 238, 0.1)',
                            border: '1px solid rgba(34, 211, 238, 0.3)',
                            borderRadius: '8px',
                            padding: '12px 16px',
                            marginBottom: '16px'
                        }}>
                            <div style={{
                                fontSize: '13px',
                                color: '#22d3ee',
                                marginBottom: '8px',
                                fontWeight: 500
                            }}>
                                {t('history.params_override', 'Parameter Overrides')}
                            </div>
                            <div style={{ display: 'flex', flexWrap: 'wrap', gap: '8px' }}>
                                {Object.entries(paramOverrides).map(([key, value]) => (
                                    <Tag key={key} color="cyan">
                                        {key}: {typeof value === 'number' ? value.toLocaleString() : String(value)}
                                    </Tag>
                                ))}
                            </div>
                        </div>
                    )}
                    <pre style={{
                        background: 'rgba(22, 27, 34, 0.6)',
                        padding: '16px',
                        borderRadius: '8px',
                        overflow: 'auto',
                        maxHeight: '600px',
                        whiteSpace: 'pre',
                        fontFamily: 'Monaco, Consolas, "Courier New", monospace',
                        fontSize: '13px',
                        lineHeight: '1.5'
                    }}>
                        {strategyCode}
                    </pre>
                </div>
            )
        });
    }

    return (
        <div className="page-container">
            <div className="page-header" style={{ display: 'none' }}>
                <h1>{t('config_form.title', 'Run Strategy')}</h1>
            </div>

            <StrategyConfigForm
                strategies={strategies}
                selectedStrategy={selectedStrategy}
                setSelectedStrategy={setSelectedStrategy}
                fetchStrategies={fetchStrategies}
                ticker={ticker}
                setTicker={setTicker}
                startDate={startDate}
                setStartDate={setStartDate}
                endDate={endDate}
                setEndDate={setEndDate}
                initialCash={initialCash}
                setInitialCash={setInitialCash}
                commission={commission}
                setCommission={setCommission}
                stake={stake}
                setStake={setStake}
                loading={loading}
                onSubmit={handleBacktest}
                error={error}
                strategyParams={strategyParams}
                paramOverrides={paramOverrides}
                setParamOverrides={setParamOverrides}
            />

            {result ? (
                <div className="results-animate-in">
                    {/* Backtest Header Card */}
                    <div className="backtest-header-card">
                        <div className="backtest-header-icon">
                            <BarChartOutlined />
                        </div>
                        <div className="backtest-header-content">
                            <h2 className="backtest-header-title">{t('history.backtest_results', 'Backtest Results')}</h2>
                            <div className="backtest-header-meta">
                                <div className="backtest-meta-item">
                                    <StockOutlined />
                                    <span className="backtest-meta-value">{ticker}</span>
                                </div>
                                <div className="backtest-meta-item">
                                    <CodeOutlined />
                                    <span className="backtest-meta-value">{selectedStrategy}</span>
                                </div>
                                <div className="backtest-meta-item">
                                    <CalendarOutlined />
                                    <span className="backtest-meta-value">{startDate} ~ {endDate}</span>
                                </div>
                                <div className="backtest-meta-item">
                                    <DollarOutlined />
                                    <span className="backtest-meta-value">${parseFloat(initialCash).toLocaleString()}</span>
                                </div>
                            </div>
                            {paramOverrides && Object.keys(paramOverrides).length > 0 && (
                                <div className="param-pills">
                                    {Object.entries(paramOverrides).map(([key, value]) => (
                                        <span key={key} className="param-pill">
                                            <span className="param-pill-key">{key}:</span>
                                            {typeof value === 'number' ? value.toLocaleString() : String(value)}
                                        </span>
                                    ))}
                                </div>
                            )}
                        </div>
                    </div>

                    <Tabs
                        defaultActiveKey="overview"
                        className="strategy-results-tabs"
                        items={tabItems}
                    />
                </div>
            ) : (
                <div className="empty-state-container">
                    <div className="empty-state-icon">
                        <RobotOutlined />
                    </div>
                    <h3>{t('config_form.ready_to_run', 'Ready to Backtest')}</h3>
                    <p>{t('config_form.select_strategy_hint', 'Configure your parameters above and hit "Run Backtest" to see AI-powered analysis.')}</p>
                </div>
            )}
        </div>
    )
}

export default RunStrategy
