import { useState } from 'react';
import { Card, Button, Spin, Alert, Empty } from 'antd';
import {
    PieChartOutlined,
    LineChartOutlined,
    ThunderboltOutlined,
} from '@ant-design/icons';
import dayjs from 'dayjs';
import { useTranslation } from 'react-i18next';
import { useTickerWeights } from '../hooks/useTickerWeights';
import { useStrategyParams } from '../hooks/useStrategyParams';
import { useStrategies } from '../hooks/useStrategies';
import { useBacktest } from '../hooks/useBacktest';
import { usePersistedState } from '../hooks/usePersistedState';
import { getDefaults } from '../config/defaults';
import { getIndividualResultsColumns } from '../utils/tableColumns';
import {
    PortfolioHeader,
    TickerWeightSection,
    ParametersSection,
    StrategyParamsSection,
    PortfolioResultsSection,
} from '../components/PortfolioBacktest';
import './PortfolioBacktest.css';

/**
 * Portfolio Backtest Page - Container Component
 * 
 * This is the main container component that orchestrates data and state
 * for the portfolio backtest feature. All presentational logic is delegated
 * to child components imported from components/PortfolioBacktest/.
 */
function PortfolioBacktest() {
    const { t } = useTranslation();
    const defaults = getDefaults().backtest;

    // Form state - persisted in localStorage across page navigations
    const dayjsArraySerialize = (val) => JSON.stringify(val.map(d => d.format('YYYY-MM-DD')));
    const dayjsArrayDeserialize = (str) => JSON.parse(str).map(s => dayjs(s));
    const [dateRange, setDateRange] = usePersistedState(
        'portfolio.dateRange',
        [dayjs().subtract(3, 'month'), dayjs()],
        { serialize: dayjsArraySerialize, deserialize: dayjsArrayDeserialize }
    );
    const [initialCash, setInitialCash] = usePersistedState('portfolio.initialCash', defaults.initial_cash);
    const [commission, setCommission] = usePersistedState('portfolio.commission', defaults.commission);
    const [timeframe, setTimeframe] = usePersistedState('portfolio.timeframe', defaults.timeframe);

    const [savedStrategy, setSavedStrategy] = usePersistedState('portfolio.strategy', '');
    const {
        strategies,
        selectedStrategy,
        setSelectedStrategy: _setSelectedStrategy,
    } = useStrategies({ initialSelectedStrategy: savedStrategy });
    const setSelectedStrategy = (val) => {
        _setSelectedStrategy(val);
        setSavedStrategy(val);
    };
    const [paramsExpanded, setParamsExpanded] = useState(true);



    // Use custom hooks - tickers/weights persisted
    const [savedTickers, setSavedTickers] = usePersistedState('portfolio.tickers', ['AAPL', 'GOOGL']);
    const [savedWeights, setSavedWeights] = usePersistedState('portfolio.weights', [0.5, 0.5]);
    const {
        tickers,
        weights,
        addTicker: _addTicker,
        removeTicker: _removeTicker,
        updateTicker: _updateTicker,
        updateWeight: _updateWeight,
        normalizeWeights: _normalizeWeights,
        equalWeights: _equalWeights,
        totalWeight,
        isWeightValid,
        validTickers,
    } = useTickerWeights({ initialTickers: savedTickers, initialWeights: savedWeights });

    // Wrap mutations to persist to localStorage
    const syncTickersWeights = (newTickers, newWeights) => {
        if (newTickers !== undefined) setSavedTickers(newTickers);
        if (newWeights !== undefined) setSavedWeights(newWeights);
    };
    const addTicker = () => { _addTicker(); syncTickersWeights([...tickers, ''], [...weights, 0]); };
    const removeTicker = (i) => { _removeTicker(i); syncTickersWeights(tickers.filter((_, idx) => idx !== i), weights.filter((_, idx) => idx !== i)); };
    const updateTicker = (i, v) => { _updateTicker(i, v); const t = [...tickers]; t[i] = v.toUpperCase(); syncTickersWeights(t, undefined); };
    const updateWeight = (i, v) => { _updateWeight(i, v); const w = [...weights]; w[i] = v || 0; syncTickersWeights(undefined, w); };
    const normalizeWeights = () => { _normalizeWeights(); const total = weights.reduce((a, b) => a + b, 0); if (total > 0) syncTickersWeights(undefined, weights.map(w => Math.round((w / total) * 100) / 100)); };
    const equalWeights = () => { _equalWeights(); const eq = Math.round((1 / tickers.length) * 100) / 100; syncTickersWeights(undefined, tickers.map(() => eq)); };

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
            timeframe,
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
                    timeframe={timeframe}
                    setTimeframe={setTimeframe}
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
                <PortfolioResultsSection t={t} result={result} columns={individualResultsColumns} />
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

export default PortfolioBacktest;
