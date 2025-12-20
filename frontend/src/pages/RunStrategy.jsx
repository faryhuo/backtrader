
import { useState, useEffect } from 'react'
import { Table, Input, Select, DatePicker, Button, Space, Tag, message, Tabs, Descriptions } from 'antd'
import '../components/RunStrategy/RunStrategy.css'
import { api } from '../services/api'
import { performFullStrategyAnalysis, getAvailableModels } from '../services/aiAnalysis'
import StrategyConfigForm from '../components/RunStrategy/StrategyConfigForm'
import PerformanceOverview from '../components/RunStrategy/PerformanceOverview'
import TradeLog from '../components/RunStrategy/TradeLog'
import StrategyPlot from '../components/RunStrategy/StrategyPlot'
import DeepAnalysis from '../components/DeepAnalysis'
import AIInsight from '../components/RunStrategy/AIInsight'

import { RobotOutlined } from '@ant-design/icons'
import { useTranslation } from 'react-i18next'
import dayjs from 'dayjs'

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
    const [strategyParams, setStrategyParams] = useState([])  // Strategy-specific params
    const [paramOverrides, setParamOverrides] = useState({})  // User overrides for params
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

    // Fetch strategy params and code when strategy changes
    useEffect(() => {
        const fetchStrategyDetails = async () => {
            if (!selectedStrategy) {
                setStrategyParams([]);
                setParamOverrides({});
                setStrategyCode('');
                return;
            }
            try {
                // Fetch params
                const data = await api.getStrategyParams(selectedStrategy);
                setStrategyParams(data.params || []);
                const defaults = {};
                (data.params || []).forEach(p => {
                    defaults[p.name] = p.value;
                });
                setParamOverrides(defaults);

                // Fetch code
                const strategyData = await api.getStrategy(selectedStrategy);
                if (strategyData && strategyData.code) {
                    setStrategyCode(strategyData.code);
                }

            } catch (err) {
                console.warn('Failed to fetch strategy details:', err);
                // Don't clear everything on error to prevent UI flicker if transient
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
        // Reset analysis when running new backtest
        setAnalyses({})
        setActiveTab(null)

        try {
            // Build params object only if there are overrides
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
            // Need a plot URL for strict analysis (though some models might work without it)
            // But let's follow the standard pattern
            if (!result) return;
        }
        setAiLoading(true)

        try {
            const data = await performFullStrategyAnalysis({
                result: {
                    metrics: result.metrics || result, // Handle inconsistent structure if any
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

            // We don't save to history here automatically as this is a "Run" session,
            // but the user can see the result immediately.

        } catch (err) {
            console.error(err)
            message.error("Failed to perform AI analysis: " + err.message)
        } finally {
            setAiLoading(false)
        }
    }

    const tradeList = result?.metrics?.trade_details?.trades || result?.trade_details?.trades || []

    // Normalize metrics access
    const metrics = result?.metrics || result || {}
    const plotUrl = result?.plot_url || metrics.plot_url

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
                    <Tabs defaultActiveKey="overview" className="strategy-results-tabs">
                        <Tabs.TabPane tab={t('history.tab_overview', 'Overview')} key="overview">
                            <Descriptions bordered column={2} size="small" style={{ marginBottom: 20 }}>
                                <Descriptions.Item label={t('config_form.ticker')}>
                                    <Tag color="blue">{ticker}</Tag>
                                </Descriptions.Item>
                                <Descriptions.Item label={t('config_form.strategy')}>
                                    {selectedStrategy}
                                </Descriptions.Item>
                                <Descriptions.Item label={t('history.test_period')}>
                                    {startDate} ~ {endDate}
                                </Descriptions.Item>
                                <Descriptions.Item label={t('config_form.initial_cash')}>
                                    ${parseFloat(initialCash).toLocaleString()}
                                </Descriptions.Item>
                                <Descriptions.Item label={t('config_form.commission')}>
                                    {commission}
                                </Descriptions.Item>
                                <Descriptions.Item label={t('config_form.stake')}>
                                    {stake}
                                </Descriptions.Item>
                                {paramOverrides && Object.keys(paramOverrides).length > 0 && (
                                    <Descriptions.Item label={t('history.strategy_params', 'Strategy Params')} span={2}>
                                        <div style={{ display: 'flex', flexWrap: 'wrap', gap: '8px' }}>
                                            {Object.entries(paramOverrides).map(([key, value]) => (
                                                <Tag key={key} color="purple">
                                                    {key}: {typeof value === 'number' ? value.toLocaleString() : String(value)}
                                                </Tag>
                                            ))}
                                        </div>
                                    </Descriptions.Item>
                                )}
                            </Descriptions>

                            <PerformanceOverview result={result} />
                        </Tabs.TabPane>

                        <Tabs.TabPane tab={t('history.tab_chart', 'Chart')} key="chart">
                            <div style={{ padding: '20px 0' }}>
                                <StrategyPlot
                                    result={result}
                                    ticker={ticker}
                                    startDate={startDate}
                                    endDate={endDate}
                                    strategyName={selectedStrategy}
                                />
                            </div>
                        </Tabs.TabPane>

                        <Tabs.TabPane tab={t('history.tab_trades', 'Trades')} key="trades">
                            <TradeLog trades={tradeList} />
                        </Tabs.TabPane>

                        <Tabs.TabPane tab={t('history.tab_ai_insight', 'AI Insight')} key="ai_insight">
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
                                        <RobotOutlined style={{ fontSize: '1.5rem', color: '#3b82f6' }} />
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
                                            dropdownStyle={{ background: '#1f2937', border: '1px solid #374151' }}
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
                                                background: 'linear-gradient(135deg, #3b82f6 0%, #2563eb 100%)',
                                                border: 'none',
                                                boxShadow: '0 4px 6px -1px rgba(37, 99, 235, 0.2)'
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
                        </Tabs.TabPane>

                        <Tabs.TabPane tab={t('history.tab_deep_analysis', 'Deep Analysis')} key="deep_analysis">
                            {result.backtest_id ? (
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
                            )}
                        </Tabs.TabPane>

                        {strategyCode && (
                            <Tabs.TabPane tab={t('history.tab_strategy_code', 'Strategy Code')} key="strategy_code">
                                <div style={{ padding: '20px' }}>
                                    {paramOverrides && Object.keys(paramOverrides).length > 0 && (
                                        <div style={{
                                            background: 'rgba(128, 90, 213, 0.15)',
                                            border: '1px solid rgba(128, 90, 213, 0.3)',
                                            borderRadius: '8px',
                                            padding: '12px 16px',
                                            marginBottom: '16px'
                                        }}>
                                            <div style={{
                                                fontSize: '13px',
                                                color: '#a78bfa',
                                                marginBottom: '8px',
                                                fontWeight: 500
                                            }}>
                                                {t('history.params_override', 'Parameter Overrides')}
                                            </div>
                                            <div style={{ display: 'flex', flexWrap: 'wrap', gap: '8px' }}>
                                                {Object.entries(paramOverrides).map(([key, value]) => (
                                                    <Tag key={key} color="purple">
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
                            </Tabs.TabPane>
                        )}
                    </Tabs>
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
