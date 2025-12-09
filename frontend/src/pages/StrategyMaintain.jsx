import { useState, useEffect } from 'react'
import Editor from '@monaco-editor/react'
import { useTranslation } from 'react-i18next'
import '../index.css'
import { api } from '../services/api'

function StrategyMaintain() {
    const { t } = useTranslation();
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
            alert(t('maintain.saved'));
        } catch (err) {
            alert(t('maintain.save_failed'));
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
        alert(t('maintain.analysis_coming_soon'))
    }

    const handleAIRewrite = () => {
        alert(t('maintain.rewrite_coming_soon'))
    }

    return (
        <div className="page-container">
            <section className="card editor-card">
                <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: '1.5rem', borderBottom: '1px solid var(--border-color)', paddingBottom: '1rem' }}>
                    <h2 style={{ margin: 0, border: 'none', padding: 0 }}>{t('maintain.editor_title')}</h2>
                    <button
                        type="button"
                        className="btn-primary"
                        onClick={openNewStrategyModal}
                        disabled={codeLoading}
                        style={{ minWidth: '100px', padding: '0.5rem 1rem' }}
                    >
                        {t('maintain.new')}
                    </button>
                </div>
                <p className="subtitle">{t('maintain.subtitle')}</p>
                <div className="strategy-toolbar">
                    <div className="strategy-row">
                        <label htmlFor="editor-strategy-select">{t('maintain.active_strategy')}</label>
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
                            {t('maintain.reload')}
                        </button>
                        <button
                            type="button"
                            className="btn-ghost"
                            onClick={fetchStrategies}
                            disabled={codeLoading}
                        >
                            {t('maintain.refresh_list')}
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
                            {t('maintain.ai_analysis')}
                        </button>
                        <button
                            className="btn-secondary"
                            onClick={handleAIRewrite}
                            disabled={codeLoading}
                            style={{ margin: 0 }}
                        >
                            {t('maintain.ai_rewrite')}
                        </button>
                    </div>
                    <button className="btn-primary" onClick={saveStrategy} disabled={codeLoading}>
                        {codeLoading ? t('maintain.saving') : t('maintain.save_strategy')}
                    </button>
                </div>
            </section>

            {/* New Strategy Modal */}
            {showNewStrategyModal && (
                <div className="modal-overlay" onClick={() => setShowNewStrategyModal(false)}>
                    <div className="modal-content" onClick={(e) => e.stopPropagation()}>
                        <div className="modal-header">
                            <h3>{t('maintain.create_new_strategy')}</h3>
                        </div>
                        <div className="form-group">
                            <label htmlFor="modal-new-strategy-name">{t('maintain.strategy_name')}</label>
                            <input
                                id="modal-new-strategy-name"
                                type="text"
                                value={newStrategyName}
                                onChange={(e) => setNewStrategyName(e.target.value)}
                                placeholder={t('maintain.placeholder_name')}
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
                                {t('common.cancel')}
                            </button>
                            <button
                                className="btn-primary"
                                onClick={createStrategy}
                                disabled={!newStrategyName.trim()}
                            >
                                {t('maintain.create')}
                            </button>
                        </div>
                    </div>
                </div>
            )}
        </div>
    )
}

export default StrategyMaintain
