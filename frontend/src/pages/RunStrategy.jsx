import { useState, useEffect } from 'react'
import '../index.css'
import '../components/RunStrategy/RunStrategy.css'
import { api } from '../services/api'
import StrategyConfigForm from '../components/RunStrategy/StrategyConfigForm'
import PerformanceOverview from '../components/RunStrategy/PerformanceOverview'
import TradeLog from '../components/RunStrategy/TradeLog'
import StrategyPlot from '../components/RunStrategy/StrategyPlot'

import { RobotOutlined } from '@ant-design/icons'
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
    const [strategyParams, setStrategyParams] = useState([])  // Strategy-specific params
    const [paramOverrides, setParamOverrides] = useState({})  // User overrides for params
    const [result, setResult] = useState(null)
    const [loading, setLoading] = useState(false)
    const [error, setError] = useState(null)



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

    // Fetch strategy params when strategy changes
    useEffect(() => {
        const fetchParams = async () => {
            if (!selectedStrategy) {
                setStrategyParams([]);
                setParamOverrides({});
                return;
            }
            try {
                const data = await api.getStrategyParams(selectedStrategy);
                setStrategyParams(data.params || []);
                // Initialize overrides with default values
                const defaults = {};
                (data.params || []).forEach(p => {
                    defaults[p.name] = p.value;
                });
                setParamOverrides(defaults);
            } catch (err) {
                console.warn('Failed to fetch strategy params:', err);
                setStrategyParams([]);
                setParamOverrides({});
            }
        };
        fetchParams();
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



    const tradeList = result?.metrics?.trade_details?.trades || []

    return (
        <div className="page-container">
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
                    <PerformanceOverview result={result} />


                    <TradeLog trades={tradeList} />

                    <StrategyPlot
                        result={result}
                        ticker={ticker}
                        startDate={startDate}
                        endDate={endDate}
                        strategyName={selectedStrategy}
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
