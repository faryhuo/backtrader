import { useState } from 'react';
import '../components/RunStrategy/RunStrategy.css';
import { useSettingsContext } from '../contexts/SettingsContext';
import { useStrategyParams } from '../hooks/useStrategyParams';
import { useStrategies } from '../hooks/useStrategies';
import { useBacktest } from '../hooks/useBacktest';
import { useAIAnalysis } from '../hooks/useAIAnalysis';
import { buildTabItems } from '../utils/tabItemsBuilder.jsx';
import StrategyConfigForm from '../components/RunStrategy/StrategyConfigForm';
import ResultsHeader from '../components/RunStrategy/ResultsHeader';
import TaskProgressCard from '../components/RunStrategy/TaskProgressCard';
import EmptyState from '../components/RunStrategy/EmptyState';
import { useTranslation } from 'react-i18next';

/**
 * RunStrategy Page - Container Component
 * 
 * Orchestrates the strategy backtest workflow including configuration,
 * execution, and result display. Delegates UI rendering to child components.
 */
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
    // Sizer configuration
    const [sizerType, setSizerType] = useState('fixed_size');
    const [sizerConfig, setSizerConfig] = useState({ stake: 100, percents: 10, risk_percent: 2 });
    // Data timeframe
    const [timeframe, setTimeframe] = useState('1d');

    const {
        strategies,
        selectedStrategy,
        setSelectedStrategy,
        refresh: fetchStrategies,
    } = useStrategies();

    // Use custom hooks for complex state management
    const {
        strategyParams,
        paramOverrides,
        setParamOverrides,
        handleParamChange,
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
            sizerType,
            sizerConfig,
            timeframe,
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
                sizerType={sizerType}
                setSizerType={setSizerType}
                sizerConfig={sizerConfig}
                setSizerConfig={setSizerConfig}
                timeframe={timeframe}
                setTimeframe={setTimeframe}
                loading={loading}
                onSubmit={handleBacktest}
                error={error}
                strategyParams={strategyParams}
                paramOverrides={paramOverrides}
                onParamChange={handleParamChange}
            />

            {result ? (
                <ResultsHeader
                    t={t}
                    ticker={ticker}
                    selectedStrategy={selectedStrategy}
                    startDate={startDate}
                    endDate={endDate}
                    initialCash={initialCash}
                    paramOverrides={paramOverrides}
                    tabItems={tabItems}
                    backtestId={result?.backtest_id}
                    analyses={analyses}
                />
            ) : loading && taskProgress ? (
                <TaskProgressCard taskProgress={taskProgress} />
            ) : (
                <EmptyState t={t} />
            )}
        </div>
    );
}

export default RunStrategy;
