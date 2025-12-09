import { useState, useEffect } from 'react'
import '../index.css'
import { api } from '../services/api'
import StrategyConfigForm from '../components/RunStrategy/StrategyConfigForm'
import PerformanceOverview from '../components/RunStrategy/PerformanceOverview'
import TradeLog from '../components/RunStrategy/TradeLog'
import StrategyPlot from '../components/RunStrategy/StrategyPlot'

function RunStrategy() {
    // Backtest State
    const [ticker, setTicker] = useState('AAPL')
    const [startDate, setStartDate] = useState('2022-01-01')
    const [endDate, setEndDate] = useState('2023-12-31')
    const [initialCash, setInitialCash] = useState(100000.0)
    const [commission, setCommission] = useState(0.0005)
    const [stake, setStake] = useState(100)
    const [strategies, setStrategies] = useState([])
    const [selectedStrategy, setSelectedStrategy] = useState('')
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
            const data = await api.runBacktest({
                ticker,
                start_date: startDate,
                end_date: endDate,
                initial_cash: parseFloat(initialCash),
                commission: parseFloat(commission),
                stake: parseInt(stake, 10),
                strategy_name: selectedStrategy
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
            />

            {result && (
                <>
                    <PerformanceOverview result={result} />

                    <TradeLog trades={tradeList} />

                    <StrategyPlot
                        result={result}
                        ticker={ticker}
                        startDate={startDate}
                        endDate={endDate}
                        strategyName={selectedStrategy}
                    />
                </>
            )}
        </div>
    )
}

export default RunStrategy
