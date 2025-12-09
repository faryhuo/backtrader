import { useState, useEffect } from 'react'
import Editor from '@monaco-editor/react'
import { useTranslation } from 'react-i18next'
import '../index.css'
import { api } from '../services/api'
import NewStrategyModal from '../components/StrategyMaintain/NewStrategyModal'
import StrategySelector from '../components/StrategyMaintain/StrategySelector'
import EditorActions from '../components/StrategyMaintain/EditorActions'
import AnalysisModal from '../components/StrategyMaintain/AnalysisModal'

function StrategyMaintain() {
    const { t } = useTranslation();
    // Strategy Editor State
    const [strategies, setStrategies] = useState([])
    const [selectedStrategy, setSelectedStrategy] = useState('')
    const [showNewStrategyModal, setShowNewStrategyModal] = useState(false)
    const [code, setCode] = useState('')
    const [codeLoading, setCodeLoading] = useState(false)
    const [analysisResult, setAnalysisResult] = useState('')
    const [showAnalysisModal, setShowAnalysisModal] = useState(false)

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

    const createStrategy = async (name) => {
        if (!name) return
        setSelectedStrategy(name)
        setCode(defaultTemplate)
        setShowNewStrategyModal(false)
    }

    const openNewStrategyModal = () => {
        setShowNewStrategyModal(true)
    }

    const handleAIAnalysis = async () => {
        if (!code) return;
        try {
            setCodeLoading(true);
            const result = await api.analyzeCode(code);
            setAnalysisResult(result);
            setShowAnalysisModal(true);
        } catch (err) {
            console.error("AI Analysis failed", err);
            alert("AI Analysis failed: " + err.message);
        } finally {
            setCodeLoading(false);
        }
    }

    const handleAIRewrite = async () => {
        if (!code) return;
        if (!window.confirm("This will overwrite your current code with the AI optimized version. Are you sure?")) {
            return;
        }
        try {
            setCodeLoading(true);
            const newCode = await api.rewriteCode(code);
            setCode(newCode);
        } catch (err) {
            console.error("AI Rewrite failed", err);
            alert("AI Rewrite failed: " + err.message);
        } finally {
            setCodeLoading(false);
        }
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
                
                <StrategySelector
                    strategies={strategies}
                    selectedStrategy={selectedStrategy}
                    onSelectStrategy={setSelectedStrategy}
                    onReload={() => fetchStrategy(selectedStrategy)}
                    onRefreshList={fetchStrategies}
                    onAIAnalysis={handleAIAnalysis}
                    onAIRewrite={handleAIRewrite}
                    loading={codeLoading}
                    t={t}
                />

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
                
                <EditorActions
                    onSave={saveStrategy}
                    loading={codeLoading}
                    t={t}
                />
            </section>

            <NewStrategyModal
                isOpen={showNewStrategyModal}
                onClose={() => setShowNewStrategyModal(false)}
                onCreate={createStrategy}
                t={t}
            />

            <AnalysisModal
                isOpen={showAnalysisModal}
                onClose={() => setShowAnalysisModal(false)}
                content={analysisResult}
                title={t('maintain.ai_analysis')}
                t={t}
            />
        </div>
    )
}

export default StrategyMaintain
