import { useState, useEffect } from 'react'
import '../index.css'
import '../components/RunStrategy/RunStrategy.css'
import { api } from '../services/api'
import StrategyConfigForm from '../components/RunStrategy/StrategyConfigForm'
import PerformanceOverview from '../components/RunStrategy/PerformanceOverview'
import TradeLog from '../components/RunStrategy/TradeLog'
import StrategyPlot from '../components/RunStrategy/StrategyPlot'
import AIInsight from '../components/RunStrategy/AIInsight'
import { RobotOutlined, BulbOutlined } from '@ant-design/icons'
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
    const [result, setResult] = useState(null)
    const [loading, setLoading] = useState(false)
    const [error, setError] = useState(null)

        // AI Analysis State
        const [aiAnalyses, setAiAnalyses] = useState({})
        const [activeAiTab, setActiveAiTab] = useState('gpt-4o')
        const [analyzing, setAnalyzing] = useState(false)
        const [selectedModel, setSelectedModel] = useState('gpt-4o')
    
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
            setAiAnalyses({}) // Reset AI analysis on new run
    
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
    
        const handleAIAnalysis = async () => {
            if (!result) return;
            setAnalyzing(true);
            try {
                // Simplify metrics for AI to avoid token limits
                const metrics = {
                    strategy: selectedStrategy,
                    ticker: ticker,
                    period: `${startDate} to ${endDate}`,
                    final_value: result.metrics.final_value,
                    sharpe: result.metrics.sharpe,
                    returns: result.metrics.returns,
                    max_drawdown: result.metrics.drawdown,
                    win_rate: result.metrics.trades?.won?.total ? (result.metrics.trades.won.total / result.metrics.trades.total.closed * 100).toFixed(2) + '%' : 'N/A',
                    total_trades: result.metrics.trades?.total?.closed,
                    sqn: result.metrics.sqn,
                    annual_returns: result.metrics.annual_returns
                };
                
                const analysis = await api.analyzeBacktest(metrics, selectedModel);
                setAiAnalyses(prev => ({ ...prev, [selectedModel]: analysis }));
                setActiveAiTab(selectedModel);
            } catch (err) {
                console.error("AI Analysis failed", err);
            } finally {
                setAnalyzing(false);
            }
        };
    
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
    
                {result ? (
                    <div className="results-animate-in">
                        <PerformanceOverview result={result} />
                        
                        <div style={{ display: 'flex', justifyContent: 'center', marginTop: '2rem', gap: '1rem', alignItems: 'center' }}>
                            <div className="strategy-input-wrapper">
                                <select 
                                    className="styled-select"
                                    value={selectedModel}
                                    onChange={(e) => setSelectedModel(e.target.value)}
                                    disabled={analyzing}
                                    style={{ minWidth: '120px' }}
                                >
                                    <option value="gpt-4o">GPT-4o</option>
                                    <option value="o1-mini">o1 Mini</option>
                                    <option value="gpt-4-turbo">GPT-4 Turbo</option>
                                    <option value="gpt-3.5-turbo">GPT-3.5</option>
                                </select>
                            </div>
                            
                            {!analyzing ? (
                                <button className="primary-btn" onClick={handleAIAnalysis} style={{ gap: '8px', display: 'flex', alignItems: 'center' }}>
                                    <BulbOutlined /> {t('ai_insight.analyze_button', 'Analyze Results with AI')}
                                </button>
                            ) : (
                                 <div className="loading-indicator" style={{ display: 'flex', alignItems: 'center', gap: '8px', color: 'var(--text-secondary)' }}>
                                    <RobotOutlined spin /> {t('common.analyzing', 'AI is analyzing...')}
                                </div>
                            )}
                        </div>
    
                        <AIInsight 
                            analyses={aiAnalyses} 
                            activeTab={activeAiTab} 
                            onTabChange={setActiveAiTab} 
                        />
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
