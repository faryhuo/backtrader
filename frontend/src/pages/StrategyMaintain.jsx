import { useState, useEffect } from 'react'
import Editor from '@monaco-editor/react'
import '../index.css'
import { api } from '../services/api'

function StrategyMaintain() {
    // Strategy Editor State
    const [strategies, setStrategies] = useState([])
    const [selectedStrategy, setSelectedStrategy] = useState('')
    const [newStrategyName, setNewStrategyName] = useState('')
    const [showNewStrategyModal, setShowNewStrategyModal] = useState(false)
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
        setShowNewStrategyModal(false)
    }

    const openNewStrategyModal = () => {
        setNewStrategyName('')
        setShowNewStrategyModal(true)
    }

    const handleAIAnalysis = () => {
        alert("AI Analysis feature coming soon!")
    }

    const handleAIRewrite = () => {
        alert("AI Rewrite feature coming soon!")
    }



    return (
        <div className="page-container">
            <section className="card editor-card">
                <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: '1.5rem', borderBottom: '1px solid var(--border-color)', paddingBottom: '1rem' }}>
                    <h2 style={{ margin: 0, border: 'none', padding: 0 }}>Strategy Editor (UserStrategy)</h2>
                    <button
                        type="button"
                        className="btn-primary"
                        onClick={openNewStrategyModal}
                        disabled={codeLoading}
                        style={{ minWidth: '100px', padding: '0.5rem 1rem' }}
                    >
                        New
                    </button>
                </div>
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
                    <div style={{ display: 'flex', gap: '0.75rem', marginRight: 'auto' }}>
                        <button
                            className="btn-secondary"
                            onClick={handleAIAnalysis}
                            disabled={codeLoading}
                            style={{ margin: 0 }}
                        >
                            AI Analysis
                        </button>
                        <button
                            className="btn-secondary"
                            onClick={handleAIRewrite}
                            disabled={codeLoading}
                            style={{ margin: 0 }}
                        >
                            AI - Rewrite
                        </button>
                    </div>
                    <button className="btn-primary" onClick={saveStrategy} disabled={codeLoading}>
                        {codeLoading ? 'Saving...' : 'Save Strategy'}
                    </button>
                </div>
            </section>

            {/* New Strategy Modal */}
            {showNewStrategyModal && (
                <div className="modal-overlay" onClick={() => setShowNewStrategyModal(false)}>
                    <div className="modal-content" onClick={(e) => e.stopPropagation()}>
                        <div className="modal-header">
                            <h3>Create New Strategy</h3>
                        </div>
                        <div className="form-group">
                            <label htmlFor="modal-new-strategy-name">Strategy Name</label>
                            <input
                                id="modal-new-strategy-name"
                                type="text"
                                value={newStrategyName}
                                onChange={(e) => setNewStrategyName(e.target.value)}
                                placeholder="e.g., breakout_v2"
                                autoFocus
                                onKeyDown={(e) => {
                                    if (e.key === 'Enter') createStrategy()
                                    if (e.key === 'Escape') setShowNewStrategyModal(false)
                                }}
                            />
                        </div>
                        <div className="modal-actions">
                            <button
                                className="btn-ghost"
                                onClick={() => setShowNewStrategyModal(false)}
                            >
                                Cancel
                            </button>
                            <button
                                className="btn-primary"
                                onClick={createStrategy}
                                disabled={!newStrategyName.trim()}
                            >
                                Create
                            </button>
                        </div>
                    </div>
                </div>
            )}
        </div>
    )
}

export default StrategyMaintain
