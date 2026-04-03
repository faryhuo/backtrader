import dayjs from 'dayjs';
import { useEffect } from 'react';
import { Modal } from 'antd';
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

const YAHOO_INTRADAY_LIMITS = {
    '1m': 7,
    '5m': 59,
    '15m': 59,
    '1h': 729,
};

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
    const [dataSource, setDataSource] = usePersistedState('runStrategy.dataSource', 'yahoo');
    const [instrumentType, setInstrumentType] = usePersistedState('runStrategy.instrumentType', 'stock');
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

    const getYahooAdjustedRange = () => {
        const limitDays = YAHOO_INTRADAY_LIMITS[timeframe];
        if (dataSource !== 'yahoo' || !limitDays) {
            return null;
        }

        const today = dayjs().format('YYYY-MM-DD');
        const latestAllowedStart = dayjs().subtract(limitDays, 'day').format('YYYY-MM-DD');

        const selectedStart = dayjs(startDate);
        const selectedEnd = dayjs(endDate);
        if (!selectedStart.isValid() || !selectedEnd.isValid()) {
            return null;
        }

        const minAllowed = dayjs(latestAllowedStart);
        const maxAllowed = dayjs(today);
        const withinWindow = !selectedStart.isBefore(minAllowed, 'day') && !selectedEnd.isAfter(maxAllowed, 'day') && !selectedEnd.isBefore(minAllowed, 'day');

        if (withinWindow) {
            return null;
        }

        return {
            startDate: latestAllowedStart,
            endDate: today,
            limitDays,
        };
    };

    const confirmRangeAdjustment = (confirmMessage) => new Promise((resolve) => {
        Modal.confirm({
            title: t('config_form.yahoo_intraday_title', 'Adjust backtest range'),
            content: confirmMessage,
            okText: t('common.confirm', 'Confirm'),
            cancelText: t('common.cancel', 'Cancel'),
            onOk: () => resolve(true),
            onCancel: () => resolve(false),
        });
    });

    const handleBacktest = async (e) => {
        e.preventDefault();
        clearAnalyses();

        let nextStartDate = startDate;
        let nextEndDate = endDate;

        const adjustedRange = getYahooAdjustedRange();
        if (adjustedRange) {
            const confirmMessage = t(
                'config_form.yahoo_intraday_confirm',
                {
                    timeframe,
                    limit_days: adjustedRange.limitDays,
                    start_date: adjustedRange.startDate,
                    end_date: adjustedRange.endDate,
                    defaultValue: `Yahoo Finance ${timeframe} data is only available for the most recent ${adjustedRange.limitDays} days. Update the backtest range to ${adjustedRange.startDate} - ${adjustedRange.endDate}?`,
                },
            );

            const confirmed = await confirmRangeAdjustment(confirmMessage);
            if (!confirmed) {
                return;
            }

            nextStartDate = adjustedRange.startDate;
            nextEndDate = adjustedRange.endDate;
            setStartDate(nextStartDate);
            setEndDate(nextEndDate);
        }

        await runBacktest({
            ticker,
            dataSource,
            instrumentType,
            startDate: nextStartDate,
            endDate: nextEndDate,
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

    useEffect(() => {
        if (dataSource === 'eodhd' && timeframe !== '1d') {
            setTimeframe('1d');
        }
    }, [dataSource, timeframe, setTimeframe]);

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
                dataSource={dataSource}
                setDataSource={setDataSource}
                instrumentType={instrumentType}
                setInstrumentType={setInstrumentType}
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
