import { useState, useEffect } from 'react'
import Editor from '@monaco-editor/react'
import '../index.css'
import { api } from '../services/api'

function StrategyMaintain() {
    // Strategy Editor State
    const [strategies, setStrategies] = useState([])
    const [selectedStrategy, setSelectedStrategy] = useState('')
    const [newStrategyName, setNewStrategyName] = useState('')
    const [code, setCode] = useState('')
    const [codeLoading, setCodeLoading] = useState(false)

    useEffect(() => {
        const init = async () => {
            const names = await fetchStrategies();
            if (names && names.length > 0) {
                setSelectedStrategy(names[0]);
                await fetchStrategy(names[0]);
            }
        }
        init();
        // eslint-disable-next-line react-hooks/exhaustive-deps
    }, [])

    useEffect(() => {
        if (selectedStrategy) {
            fetchStrategy(selectedStrategy);
        }
        // eslint-disable-next-line react-hooks/exhaustive-deps
    }, [selectedStrategy])

    const defaultTemplate = `import backtrader as bt

class UserStrategy(bt.Strategy):
    params = (
        ("fast_period", 10),
        ("slow_period", 30),
    )

    def __init__(self):
        self.fast_ma = bt.indicators.SMA(period=self.p.fast_period)
        self.slow_ma = bt.indicators.SMA(period=self.p.slow_period)
        self.crossover = bt.indicators.CrossOver(self.fast_ma, self.slow_ma)

    def next(self):
        if not self.position and self.crossover > 0:
            self.buy()
        elif self.position and self.crossover < 0:
            self.close()
`

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

    const fetchStrategy = async (name) => {
        if (!name) return
        try {
            setCodeLoading(true)
            const data = await api.getStrategy(name)
            if (data.code) {
                setCode(data.code)
            }
        } catch (err) {
            console.error("Failed to fetch strategy", err)
        } finally {
            setCodeLoading(false)
        }
    }

    const saveStrategy = async () => {
        try {
            setCodeLoading(true);
            await api.saveStrategy(selectedStrategy || 'default', code)
            await fetchStrategies();
            alert("Strategy Saved!");
        } catch (err) {
            alert("Failed to save strategy");
        } finally {
            setCodeLoading(false);
        }
    }

    const createStrategy = async () => {
        const name = newStrategyName.trim()
        if (!name) return
        setSelectedStrategy(name)
        setCode(defaultTemplate)
        setNewStrategyName('')
    }



    return (
        <div className="page-container">
            <section className="card editor-card">
                <h2>Strategy Editor (UserStrategy)</h2>
                <p className="subtitle">Edit only the strategy class below; backtest engine is fixed.</p>
                <div className="strategy-toolbar">
                    <div className="strategy-row">
                        <label htmlFor="editor-strategy-select">Active Strategy</label>
                        <select
                            id="editor-strategy-select"
                            value={selectedStrategy}
                            onChange={(e) => setSelectedStrategy(e.target.value)}
                            disabled={codeLoading}
                        >
                            {strategies.map((s) => (
                                <option key={s} value={s}>{s}</option>
                            ))}
                        </select>
                        <button
                            type="button"
                            className="btn-ghost"
                            onClick={() => fetchStrategy(selectedStrategy)}
                            disabled={codeLoading}
                        >
                            Reload
                        </button>
                        <button
                            type="button"
                            className="btn-ghost"
                            onClick={fetchStrategies}
                            disabled={codeLoading}
                        >
                            Refresh List
                        </button>
                    </div>
                    <div className="strategy-row">
                        <label htmlFor="new-strategy">New Strategy Name</label>
                        <input
                            id="new-strategy"
                            type="text"
                            value={newStrategyName}
                            onChange={(e) => setNewStrategyName(e.target.value)}
                            placeholder="e.g., breakout_v1"
                        />
                        <button
                            type="button"
                            className="btn-primary"
                            onClick={createStrategy}
                            disabled={codeLoading}
                        >
                            New
                        </button>
                    </div>

                </div>
                <div className="code-editor">
                    <Editor
                        height="60vh"
                        defaultLanguage="python"
                        language="python"
                        theme="vs-dark"
                        value={code}
                        onChange={(value) => setCode(value ?? '')}
                        options={{
                            fontSize: 14,
                            minimap: { enabled: false },
                            scrollBeyondLastLine: false,
                            wordWrap: 'on',
                            roundedSelection: false,
                            automaticLayout: true,
                        }}
                    />
                </div>
                <div className="form-actions">
                    <button className="btn-primary" onClick={saveStrategy} disabled={codeLoading}>
                        {codeLoading ? 'Saving...' : 'Save Strategy'}
                    </button>
                </div>
            </section>
        </div>
    )
}

export default StrategyMaintain
