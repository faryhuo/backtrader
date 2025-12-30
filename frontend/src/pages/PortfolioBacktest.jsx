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

    // Form state
    const [dateRange, setDateRange] = useState([dayjs('2022-01-01'), dayjs('2023-12-31')]);
    const [initialCash, setInitialCash] = useState(defaults.initial_cash);
    const [commission, setCommission] = useState(defaults.commission);
    const [timeframe, setTimeframe] = useState(defaults.timeframe);

    const {
        strategies,
        selectedStrategy,
        setSelectedStrategy,
    } = useStrategies();
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
