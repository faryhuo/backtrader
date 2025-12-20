import { useState, useEffect } from 'react'
import { useTranslation } from 'react-i18next'
import { PlusOutlined, AppstoreOutlined, HistoryOutlined } from '@ant-design/icons'
import '../index.css'
import '../components/StrategyMaintain/StrategyMaintain.css'
import { api } from '../services/api'
import { analyzeCode, rewriteCode } from '../services/aiAnalysis'
import NewStrategyModal from '../components/StrategyMaintain/NewStrategyModal'
import StrategyEditorPanel from '../components/StrategyMaintain/StrategyEditorPanel'
import AnalysisModal from '../components/StrategyMaintain/AnalysisModal'
import { TemplateLibrary } from '../components/StrategyMaintain/TemplateLibrary'
import VersionTimeline from '../components/StrategyMaintain/VersionTimeline'
import VersionDiffViewer from '../components/StrategyMaintain/VersionDiffViewer'

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
    const [showTemplateLibrary, setShowTemplateLibrary] = useState(false)

    // Version Management State
    const [showVersionPanel, setShowVersionPanel] = useState(false)
    const [versions, setVersions] = useState([])
    const [versionsLoading, setVersionsLoading] = useState(false)
    const [selectedForCompare, setSelectedForCompare] = useState([])
    const [showDiffViewer, setShowDiffViewer] = useState(false)
    const [diffData, setDiffData] = useState(null)

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
            // Reset version state when strategy changes
            setVersions([]);
            setSelectedForCompare([]);
            if (showVersionPanel) {
                fetchVersions(selectedStrategy);
            }
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

    const fetchVersions = async (name) => {
        if (!name) return
        try {
            setVersionsLoading(true)
            const data = await api.getStrategyVersions(name)
            setVersions(data.versions || [])
        } catch (err) {
            console.error("Failed to fetch versions", err)
            setVersions([])
        } finally {
            setVersionsLoading(false)
        }
    }

    const saveStrategy = async () => {
        try {
            setCodeLoading(true);
            await api.saveStrategy(selectedStrategy || 'default', code)
            await fetchStrategies();
            // Refresh versions after save
            if (showVersionPanel) {
                await fetchVersions(selectedStrategy);
            }
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

    const handleTemplateImport = async (name) => {
        setShowTemplateLibrary(false);
        await fetchStrategies();
        setSelectedStrategy(name);
        await fetchStrategy(name);
    }

    // Version Management Handlers
    const toggleVersionPanel = () => {
        const newState = !showVersionPanel;
        setShowVersionPanel(newState);
        if (newState && selectedStrategy) {
            fetchVersions(selectedStrategy);
        }
    }

    const handleVersionSelect = async (versionNumber) => {
        try {
            const versionData = await api.getStrategyVersion(selectedStrategy, versionNumber);
            if (versionData && versionData.code) {
                setCode(versionData.code);
            }
        } catch (err) {
            console.error("Failed to load version", err);
        }
    }

    const handleCompare = (versionNumber) => {
        setSelectedForCompare(prev => {
            if (prev.includes(versionNumber)) {
                return prev.filter(v => v !== versionNumber);
            }
            if (prev.length >= 2) {
                return [prev[1], versionNumber];
            }
            return [...prev, versionNumber];
        });
    }

    useEffect(() => {
        const compareVersions = async () => {
            if (selectedForCompare.length === 2) {
                try {
                    const [fromVersion, toVersion] = selectedForCompare.sort((a, b) => a - b);
                    const diff = await api.compareVersions(selectedStrategy, fromVersion, toVersion);
                    setDiffData({
                        ...diff,
                        oldVersion: fromVersion,
                        newVersion: toVersion
                    });
                    setShowDiffViewer(true);
                } catch (err) {
                    console.error("Failed to compare versions", err);
                }
            }
        };
        compareVersions();
        // eslint-disable-next-line react-hooks/exhaustive-deps
    }, [selectedForCompare]);

    const handleRollback = async (versionNumber) => {
        if (!window.confirm(t('maintain.versions.rollback_confirm', { version: versionNumber }))) {
            return;
        }
        try {
            await api.rollbackVersion(selectedStrategy, versionNumber);
            alert(t('maintain.versions.rollback_success', { version: versionNumber }));
            // Refresh strategy and versions
            await fetchStrategy(selectedStrategy);
            await fetchVersions(selectedStrategy);
        } catch (err) {
            console.error("Rollback failed", err);
            alert(t('maintain.versions.rollback_failed'));
        }
    }

    const closeDiffViewer = () => {
        setShowDiffViewer(false);
        setDiffData(null);
        setSelectedForCompare([]);
    }

    return (
        <div className="strategy-maintain-container">
            <div className="strategy-header">
                <h1>{t('maintain.title')}</h1>
                <div className="header-actions">
                    <button
                        className={`btn-secondary ${showVersionPanel ? 'active' : ''}`}
                        onClick={toggleVersionPanel}
                    >
                        <HistoryOutlined /> {t('maintain.versions.history')}
                    </button>
                    <button className="btn-secondary" onClick={() => setShowTemplateLibrary(true)}>
                        <AppstoreOutlined /> {t('maintain.template_library')}
                    </button>
                    <button className="btn-primary" onClick={openNewStrategyModal}>
                        <PlusOutlined /> {t('maintain.new')}
                    </button>
                </div>
            </div>

            <div className={`strategy-content ${showVersionPanel ? 'with-sidebar' : ''}`}>
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

                {showVersionPanel && (
                    <div className="version-sidebar">
                        <VersionTimeline
                            versions={versions}
                            loading={versionsLoading}
                            onVersionSelect={handleVersionSelect}
                            onCompare={handleCompare}
                            onRollback={handleRollback}
                            selectedForCompare={selectedForCompare}
                            t={t}
                        />
                    </div>
                )}
            </div>

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

            {showTemplateLibrary && (
                <TemplateLibrary
                    onImport={handleTemplateImport}
                    onClose={() => setShowTemplateLibrary(false)}
                />
            )}

            {showDiffViewer && diffData && (
                <VersionDiffViewer
                    isOpen={showDiffViewer}
                    onClose={closeDiffViewer}
                    oldCode={diffData.old_code}
                    newCode={diffData.new_code}
                    oldVersion={diffData.oldVersion}
                    newVersion={diffData.newVersion}
                    linesAdded={diffData.lines_added}
                    linesRemoved={diffData.lines_removed}
                    t={t}
                />
            )}
        </div>
    )
}

export default StrategyMaintain
