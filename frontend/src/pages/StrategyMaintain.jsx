import { useState, useEffect } from 'react'
import { useTranslation } from 'react-i18next'
import { PlusOutlined } from '@ant-design/icons'
import '../index.css'
import '../components/StrategyMaintain/StrategyMaintain.css'
import { api } from '../services/api'
import { analyzeCode, rewriteCode } from '../services/aiAnalysis'
import NewStrategyModal from '../components/StrategyMaintain/NewStrategyModal'
import StrategyEditorPanel from '../components/StrategyMaintain/StrategyEditorPanel'
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
            const result = await analyzeCode(code);
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
            const newCode = await rewriteCode(code);
            setCode(newCode);
        } catch (err) {
            console.error("AI Rewrite failed", err);
            alert("AI Rewrite failed: " + err.message);
        } finally {
            setCodeLoading(false);
        }
    }

    return (
        <div className="strategy-maintain-container">
            <div className="strategy-header">
                <h1>{t('maintain.title')}</h1>
                <button className="btn-primary" onClick={openNewStrategyModal}>
                    <PlusOutlined /> {t('maintain.new')}
                </button>
            </div>

            <StrategyEditorPanel
                strategies={strategies}
                selectedStrategy={selectedStrategy}
                setSelectedStrategy={setSelectedStrategy}
                fetchStrategy={fetchStrategy}
                fetchStrategies={fetchStrategies}
                handleAIAnalysis={handleAIAnalysis}
                handleAIRewrite={handleAIRewrite}
                codeLoading={codeLoading}
                code={code}
                setCode={setCode}
                saveStrategy={saveStrategy}
                t={t}
            />

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
