import { useState, useEffect } from 'react';
import { Select, Button, Space, Tabs, Progress, Card } from 'antd';
import '../components/RunStrategy/RunStrategy.css';
import { api } from '../services/api';
import { useSettingsContext } from '../contexts/SettingsContext';
import { useStrategyParams } from '../hooks/useStrategyParams';
import { useBacktest } from '../hooks/useBacktest';
import { useAIAnalysis } from '../hooks/useAIAnalysis';
import StrategyConfigForm from '../components/RunStrategy/StrategyConfigForm';
import PerformanceOverview from '../components/RunStrategy/PerformanceOverview';
import TradeLog from '../components/RunStrategy/TradeLog';
import StrategyPlot from '../components/RunStrategy/StrategyPlot';
import DeepAnalysis from '../components/DeepAnalysis';
import AIInsight from '../components/RunStrategy/AIInsight';
import CodeViewer from '../components/RunStrategy/CodeViewer';

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
    DollarOutlined,
    LoadingOutlined,
    CheckCircleOutlined
} from '@ant-design/icons';
import { useTranslation } from 'react-i18next';

function RunStrategy() {
    const { t } = useTranslation();
    const { settings, getAvailableModels } = useSettingsContext();

    // Form State
    const [ticker, setTicker] = useState('AAPL');
    const [startDate, setStartDate] = useState('2022-01-01');
    const [endDate, setEndDate] = useState('2023-12-31');
    const [initialCash, setInitialCash] = useState(100000.0);
    const [commission, setCommission] = useState(0.0005);
    const [stake, setStake] = useState(100);
    const [strategies, setStrategies] = useState([]);
    const [selectedStrategy, setSelectedStrategy] = useState('');

    // Use custom hooks for complex state management
    const {
        strategyParams,
        paramOverrides,
        setParamOverrides,
        strategyCode,
    } = useStrategyParams(selectedStrategy);

    const {
        result,
        loading,
        error,
        taskProgress,
        runBacktest,
    } = useBacktest();

    const {
        selectedModel,
        setSelectedModel,
        analyses,
        activeTab,
        setActiveTab,
        aiLoading,
        runAnalysis,
        clearAnalyses,
        availableModels,
    } = useAIAnalysis({ getAvailableModels, settings });

    // Load strategies on mount
    useEffect(() => {
        const init = async () => {
            const names = await fetchStrategies();
            if (names && names.length > 0) {
                if (!names.includes(selectedStrategy)) {
                    setSelectedStrategy(names[0]);
                }
            }
        };
        init();
        // eslint-disable-next-line react-hooks/exhaustive-deps
    }, []);

    const fetchStrategies = async () => {
        try {
            const names = await api.getStrategies();
            setStrategies(names);
            return names;
        } catch (err) {
            console.error('Failed to fetch strategies', err);
            return [];
        }
    };

    const handleBacktest = async (e) => {
        e.preventDefault();
        clearAnalyses();

        await runBacktest({
            ticker,
            startDate,
            endDate,
            initialCash,
            commission,
            stake,
            selectedStrategy,
            paramOverrides,
        }, t);
    };

    const handleAIAnalysis = async () => {
        if (!result) return;

        await runAnalysis({
            result,
            strategyName: selectedStrategy,
            ticker,
            startDate,
            endDate,
            strategyCode,
            t,
        });
    };

    // Derived values
    const tradeList = result?.metrics?.trade_details?.trades || result?.trade_details?.trades || [];
    const metrics = result?.metrics || result || {};
    const plotUrl = result?.plot_url || metrics.plot_url;

    // Build tab items
    const tabItems = buildTabItems({
        t,
        result,
        tradeList,
        plotUrl,
        analyses,
        activeTab,
        setActiveTab,
        aiLoading,
        selectedModel,
        setSelectedModel,
        availableModels,
        handleAIAnalysis,
        strategyCode,
        paramOverrides,
        ticker,
        startDate,
        endDate,
        initialCash,
    });

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
                <ResultsSection
                    t={t}
                    ticker={ticker}
                    selectedStrategy={selectedStrategy}
                    startDate={startDate}
                    endDate={endDate}
                    initialCash={initialCash}
                    paramOverrides={paramOverrides}
                    tabItems={tabItems}
                />
            ) : loading && taskProgress ? (
                <TaskProgressCard taskProgress={taskProgress} />
            ) : (
                <EmptyState t={t} />
            )}
        </div>
    );
}

// Results section with header card and tabs
function ResultsSection({ t, ticker, selectedStrategy, startDate, endDate, initialCash, paramOverrides, tabItems }) {
    return (
        <div className="results-animate-in">
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
    );
}

// Task progress card during backtest execution
function TaskProgressCard({ taskProgress }) {
    return (
        <Card className="task-progress-card" style={{
            background: 'linear-gradient(135deg, rgba(34, 211, 238, 0.1) 0%, rgba(8, 145, 178, 0.1) 100%)',
            border: '1px solid rgba(34, 211, 238, 0.3)',
            borderRadius: '12px',
            marginTop: '24px'
        }}>
            <div style={{ display: 'flex', alignItems: 'center', gap: '16px', marginBottom: '16px' }}>
                {taskProgress.status === 'completed' ? (
                    <CheckCircleOutlined style={{ fontSize: '24px', color: '#52c41a' }} />
                ) : (
                    <LoadingOutlined style={{ fontSize: '24px', color: '#22d3ee' }} spin />
                )}
                <div>
                    <h3 style={{ margin: 0, color: '#e2e8f0', fontSize: '16px' }}>{taskProgress.name}</h3>
                    <span style={{ color: '#94a3b8', fontSize: '14px' }}>{taskProgress.message}</span>
                </div>
            </div>
            <Progress
                percent={taskProgress.progress}
                status={taskProgress.status === 'running' ? 'active' : 'normal'}
                strokeColor={{ '0%': '#22d3ee', '100%': '#0891b2' }}
                trailColor="rgba(255,255,255,0.1)"
            />
        </Card>
    );
}

// Empty state when no backtest has been run
function EmptyState({ t }) {
    return (
        <div className="empty-state-container">
            <div className="empty-state-icon">
                <RobotOutlined />
            </div>
            <h3>{t('config_form.ready_to_run', 'Ready to Backtest')}</h3>
            <p>{t('config_form.select_strategy_hint', 'Configure your parameters above and hit "Run Backtest" to see AI-powered analysis.')}</p>
        </div>
    );
}

// Build tab items configuration
function buildTabItems({
    t, result, tradeList, plotUrl, analyses, activeTab, setActiveTab,
    aiLoading, selectedModel, setSelectedModel, availableModels, handleAIAnalysis,
    strategyCode, paramOverrides, ticker, startDate, endDate, initialCash
}) {
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
                <AIInsightTab
                    t={t}
                    analyses={analyses}
                    activeTab={activeTab}
                    setActiveTab={setActiveTab}
                    aiLoading={aiLoading}
                    selectedModel={selectedModel}
                    setSelectedModel={setSelectedModel}
                    availableModels={availableModels}
                    handleAIAnalysis={handleAIAnalysis}
                    plotUrl={plotUrl}
                    result={result}
                />
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

    if (strategyCode) {
        tabItems.push({
            key: 'strategy_code',
            label: <span><CodeOutlined className="tab-icon" /> {t('history.tab_strategy_code', 'Strategy Code')}</span>,
            children: (
                <div style={{ padding: '20px' }}>
                    <CodeViewer
                        code={strategyCode}
                        language="python"
                        params={paramOverrides}
                        maxHeight={500}
                    />
                </div>
            )
        });
    }

    return tabItems;
}

// AI Insight tab content
function AIInsightTab({
    t, analyses, activeTab, setActiveTab, aiLoading, selectedModel, setSelectedModel,
    availableModels, handleAIAnalysis, plotUrl, result
}) {
    return (
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
                        onChange={setSelectedModel}
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
                <div style={{ textAlign: 'center', padding: '2rem', color: '#888' }}>
                    {t('history.no_ai_analysis', 'No AI analysis available. Click the button above to generate one.')}
                </div>
            )}
        </div>
    );
}

export default RunStrategy;
