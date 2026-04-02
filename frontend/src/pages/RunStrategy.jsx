import dayjs from 'dayjs';
import '../components/RunStrategy/RunStrategy.css';
import { useSettingsContext } from '../contexts/SettingsContext';
import { useStrategyParams } from '../hooks/useStrategyParams';
import { useStrategies } from '../hooks/useStrategies';
import { useBacktest } from '../hooks/useBacktest';
import { useAIAnalysis } from '../hooks/useAIAnalysis';
import { usePersistedState } from '../hooks/usePersistedState';
import { buildTabItems } from '../utils/tabItemsBuilder.jsx';
import { getDefaults } from '../config/defaults';
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
    const { settings } = useSettingsContext();
    const defaults = getDefaults().backtest;

    // Form State - persisted in localStorage across page navigations
    const [ticker, setTicker] = usePersistedState('runStrategy.ticker', 'AAPL');
    const [startDate, setStartDate] = usePersistedState('runStrategy.startDate', dayjs().subtract(3, 'month').format('YYYY-MM-DD'));
    const [endDate, setEndDate] = usePersistedState('runStrategy.endDate', dayjs().format('YYYY-MM-DD'));
    const [initialCash, setInitialCash] = usePersistedState('runStrategy.initialCash', defaults.initial_cash);
    const [commission, setCommission] = usePersistedState('runStrategy.commission', defaults.commission);
    const [stake, setStake] = usePersistedState('runStrategy.stake', defaults.stake);
    // Sizer configuration
    const [sizerType, setSizerType] = usePersistedState('runStrategy.sizerType', defaults.sizer_type);
    const [sizerConfig, setSizerConfig] = usePersistedState('runStrategy.sizerConfig', { stake: defaults.stake, percents: defaults.sizer_percent, risk_percent: defaults.sizer_risk_percent });
    // Data timeframe
    const [timeframe, setTimeframe] = usePersistedState('runStrategy.timeframe', defaults.timeframe);

    const [savedStrategy, setSavedStrategy] = usePersistedState('runStrategy.strategy', '');
    const {
        strategies,
        selectedStrategy,
        setSelectedStrategy: _setSelectedStrategy,
        refresh: fetchStrategies,
    } = useStrategies({ initialSelectedStrategy: savedStrategy });

    const setSelectedStrategy = (val) => {
        _setSelectedStrategy(val);
        setSavedStrategy(val);
    };

    // Use custom hooks for complex state management
    const {
        strategyParams,
        paramOverrides,
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
        analyses,
        activeTab,
        setActiveTab,
        aiLoading,
        runAnalysis,
        clearAnalyses,
    } = useAIAnalysis({ settings });

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
        handleAIAnalysis,
        strategyCode,
        paramOverrides,
        ticker,
        startDate,
        endDate,
        initialCash,
        backtestId: result?.backtest_id,
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
