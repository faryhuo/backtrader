import { useCallback, useEffect, useMemo, useState } from 'react';
import { useNavigate } from 'react-router-dom';
import { useTranslation } from 'react-i18next';
import Editor from '@monaco-editor/react';
import {
    Alert,
    Button,
    Card,
    Empty,
    Input,
    List,
    Space,
    Spin,
    Tag,
    Typography,
    message,
} from 'antd';
import {
    AppstoreOutlined,
    CheckCircleOutlined,
    CodeOutlined,
    HistoryOutlined,
    PlayCircleOutlined,
    PlusOutlined,
    RobotOutlined,
    SaveOutlined,
    SyncOutlined,
    ThunderboltOutlined,
    WarningOutlined,
} from '@ant-design/icons';
import dayjs from 'dayjs';
import '../index.css';
import '../components/StrategyMaintain/StrategyMaintain.css';
import { api } from '../services/api';
import { analyzeCode, rewriteCode } from '../services/aiAnalysis';
import { useSettingsContext } from '../contexts/SettingsContext';
import NewStrategyModal from '../components/StrategyMaintain/NewStrategyModal';
import AnalysisModal from '../components/StrategyMaintain/AnalysisModal';
import { TemplateLibrary } from '../components/StrategyMaintain/TemplateLibrary';
import VersionTimeline from '../components/StrategyMaintain/VersionTimeline';
import VersionDiffViewer from '../components/StrategyMaintain/VersionDiffViewer';

const { Paragraph, Text, Title } = Typography;

const DEFAULT_RUN_CONFIG = {
    ticker: 'AAPL',
    startDate: dayjs().subtract(3, 'month').format('YYYY-MM-DD'),
    endDate: dayjs().format('YYYY-MM-DD'),
    initialCash: '100000',
    timeframe: '1d',
};

const DEFAULT_TEMPLATE = `import backtrader as bt

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
`;

function StrategyMaintain() {
    const { t } = useTranslation();
    const { settings } = useSettingsContext();
    const navigate = useNavigate();

    const [strategies, setStrategies] = useState([]);
    const [selectedStrategy, setSelectedStrategy] = useState('');
    const [strategySearch, setStrategySearch] = useState('');
    const [showNewStrategyModal, setShowNewStrategyModal] = useState(false);
    const [showTemplateLibrary, setShowTemplateLibrary] = useState(false);
    const [showAnalysisModal, setShowAnalysisModal] = useState(false);
    const [showDiffViewer, setShowDiffViewer] = useState(false);

    const [code, setCode] = useState('');
    const [savedCode, setSavedCode] = useState('');
    const [codeLoading, setCodeLoading] = useState(false);
    const [analysisResult, setAnalysisResult] = useState('');
    const [strategyParams, setStrategyParams] = useState([]);
    const [paramsLoading, setParamsLoading] = useState(false);
    const [compileState, setCompileState] = useState(null);
    const [runConfig, setRunConfig] = useState(DEFAULT_RUN_CONFIG);

    const [showVersionPanel, setShowVersionPanel] = useState(true);
    const [versions, setVersions] = useState([]);
    const [versionsLoading, setVersionsLoading] = useState(false);
    const [selectedForCompare, setSelectedForCompare] = useState([]);
    const [diffData, setDiffData] = useState(null);

    useEffect(() => {
        const init = async () => {
            const names = await fetchStrategies();
            if (names.length > 0) {
                setSelectedStrategy(names[0]);
            }
        };
        init();
        // eslint-disable-next-line react-hooks/exhaustive-deps
    }, []);

    useEffect(() => {
        if (!selectedStrategy) {
            setCode('');
            setSavedCode('');
            setStrategyParams([]);
            return;
        }

        const loadSelectedStrategy = async () => {
            await Promise.all([
                fetchStrategy(selectedStrategy),
                fetchStrategyParams(selectedStrategy),
                showVersionPanel ? fetchVersions(selectedStrategy) : Promise.resolve(),
            ]);
        };

        loadSelectedStrategy();
        setSelectedForCompare([]);
        setCompileState(null);
        // eslint-disable-next-line react-hooks/exhaustive-deps
    }, [selectedStrategy, showVersionPanel]);

    const filteredStrategies = useMemo(() => {
        const keyword = strategySearch.trim().toLowerCase();
        if (!keyword) return strategies;
        return strategies.filter((name) => name.toLowerCase().includes(keyword));
    }, [strategies, strategySearch]);

    const strategyStats = useMemo(() => {
        const lines = code ? code.split(/\r?\n/).length : 0;
        const characters = code.length;
        const functions = (code.match(/^\s*def\s+/gm) || []).length;
        const classes = (code.match(/^\s*class\s+/gm) || []).length;
        return { lines, characters, functions, classes };
    }, [code]);

    const isDirty = code !== savedCode;

    const fetchStrategies = useCallback(async () => {
        try {
            const names = await api.getStrategies();
            setStrategies(names);
            return names;
        } catch (err) {
            console.error('Failed to fetch strategies', err);
            message.error(t('maintain.fetch_failed', 'Failed to load strategies'));
            return [];
        }
    }, [t]);

    const fetchStrategy = useCallback(async (name) => {
        if (!name) return;
        try {
            setCodeLoading(true);
            const data = await api.getStrategy(name);
            const nextCode = data?.code || '';
            setCode(nextCode);
            setSavedCode(nextCode);
        } catch (err) {
            console.error('Failed to fetch strategy', err);
            message.error(t('maintain.load_failed', 'Failed to load strategy'));
        } finally {
            setCodeLoading(false);
        }
    }, [t]);

    const fetchStrategyParams = useCallback(async (name) => {
        if (!name) return;
        try {
            setParamsLoading(true);
            const data = await api.getStrategyParams(name);
            setStrategyParams(data?.params || []);
        } catch (err) {
            console.error('Failed to fetch strategy params', err);
            setStrategyParams([]);
        } finally {
            setParamsLoading(false);
        }
    }, []);

    const fetchVersions = useCallback(async (name) => {
        if (!name) return;
        try {
            setVersionsLoading(true);
            const data = await api.getStrategyVersions(name);
            setVersions(data.versions || []);
        } catch (err) {
            console.error('Failed to fetch versions', err);
            setVersions([]);
        } finally {
            setVersionsLoading(false);
        }
    }, []);

    async function saveStrategy() {
        if (!selectedStrategy) {
            message.warning(t('maintain.select_strategy_first', 'Select or create a strategy first'));
            return;
        }

        try {
            setCodeLoading(true);
            await api.saveStrategy(selectedStrategy, code);
            setSavedCode(code);
            await Promise.all([fetchStrategies(), fetchStrategyParams(selectedStrategy)]);
            if (showVersionPanel) {
                await fetchVersions(selectedStrategy);
            }
            message.success(t('maintain.saved', 'Strategy Saved!'));
        } catch (err) {
            console.error('Failed to save strategy', err);
            message.error(err?.message || t('maintain.save_failed', 'Failed to save strategy'));
        } finally {
            setCodeLoading(false);
        }
    }

    function handleCodeChange(value) {
        setCode(value ?? '');
        if (compileState) {
            setCompileState(null);
        }
    }

    async function handleCompile() {
        if (!code.trim()) {
            message.warning(t('maintain.compile_empty', 'Strategy code is empty'));
            return;
        }

        try {
            setCodeLoading(true);
            const result = await api.validateStrategy(selectedStrategy, code);
            setCompileState({
                status: 'success',
                message: result?.message || t('maintain.compile_success', 'Strategy compiled successfully'),
            });
            message.success(result?.message || t('maintain.compile_success', 'Strategy compiled successfully'));
        } catch (err) {
            const detail = err?.message || t('maintain.compile_failed', 'Strategy compile failed');
            setCompileState({
                status: 'error',
                message: detail,
            });
            message.error(detail);
        } finally {
            setCodeLoading(false);
        }
    }

    async function handleRunStrategy() {
        if (!selectedStrategy) {
            message.warning(t('maintain.select_strategy_first', 'Select or create a strategy first'));
            return;
        }

        if (isDirty) {
            try {
                setCodeLoading(true);
                await api.saveStrategy(selectedStrategy, code);
                setSavedCode(code);
                await Promise.all([fetchStrategies(), fetchStrategyParams(selectedStrategy)]);
                if (showVersionPanel) {
                    await fetchVersions(selectedStrategy);
                }
                message.success(t('maintain.run_saved_latest', 'Latest strategy changes saved before running'));
            } catch (err) {
                console.error('Failed to save strategy before run', err);
                message.error(err?.message || t('maintain.run_save_failed', 'Save the strategy before running'));
                return;
            } finally {
                setCodeLoading(false);
            }
        }

        localStorage.setItem('runStrategy.strategy', selectedStrategy);
        localStorage.setItem('runStrategy.ticker', runConfig.ticker);
        localStorage.setItem('runStrategy.startDate', runConfig.startDate);
        localStorage.setItem('runStrategy.endDate', runConfig.endDate);
        localStorage.setItem('runStrategy.initialCash', runConfig.initialCash);
        localStorage.setItem('runStrategy.timeframe', runConfig.timeframe);

        navigate('/strategy');
    }

    async function createStrategy(name) {
        if (!name) return;

        try {
            setCodeLoading(true);
            await api.saveStrategy(name, DEFAULT_TEMPLATE);
            const names = await fetchStrategies();
            setSelectedStrategy(name);
            if (!names.includes(name)) {
                setStrategies((prev) => [...prev, name].sort());
            }
            setCode(DEFAULT_TEMPLATE);
            setSavedCode(DEFAULT_TEMPLATE);
            setShowNewStrategyModal(false);
            message.success(t('maintain.created', 'Strategy created'));
        } catch (err) {
            console.error('Failed to create strategy', err);
            message.error(err?.message || t('maintain.save_failed', 'Failed to save strategy'));
        } finally {
            setCodeLoading(false);
        }
    }

    async function handleAIAnalysis() {
        if (!code) return;
        try {
            setCodeLoading(true);
            const result = await analyzeCode(code, null, settings);
            setAnalysisResult(result.analysis);
            setShowAnalysisModal(true);
        } catch (err) {
            console.error('AI Analysis failed', err);
            message.error(err?.message || t('maintain.ai_analysis_failed', 'AI analysis failed'));
        } finally {
            setCodeLoading(false);
        }
    }

    async function handleAIRewrite() {
        if (!code) return;
        if (!window.confirm(t('maintain.ai_rewrite_confirm', 'This will overwrite the current editor content with an AI rewrite. Continue?'))) {
            return;
        }

        try {
            setCodeLoading(true);
            const newCode = await rewriteCode(code, null, settings);
            setCode(newCode);
            message.success(t('maintain.ai_rewrite_done', 'AI rewrite completed'));
        } catch (err) {
            console.error('AI Rewrite failed', err);
            message.error(err?.message || t('maintain.ai_rewrite_failed', 'AI rewrite failed'));
        } finally {
            setCodeLoading(false);
        }
    }

    async function handleTemplateImport(name) {
        setShowTemplateLibrary(false);
        await fetchStrategies();
        setSelectedStrategy(name);
    }

    async function handleVersionSelect(versionNumber) {
        try {
            const versionData = await api.getStrategyVersion(selectedStrategy, versionNumber);
            if (versionData?.code) {
                setCode(versionData.code);
            }
        } catch (err) {
            console.error('Failed to load version', err);
            message.error(t('maintain.version_load_failed', 'Failed to load version'));
        }
    }

    async function handleCompare(versionNumber) {
        if (versions.length === 0) return;
        const latestVersion = versions[0].version_number;
        if (versionNumber === latestVersion) return;

        try {
            const diff = await api.compareVersions(selectedStrategy, versionNumber, latestVersion);
            setDiffData({
                ...diff,
                oldVersion: versionNumber,
                newVersion: latestVersion,
            });
            setShowDiffViewer(true);
        } catch (err) {
            console.error('Failed to compare versions', err);
            message.error(t('maintain.compare_failed', 'Version compare failed'));
        }
    }

    async function handleRollback(versionNumber) {
        if (!window.confirm(t('maintain.versions.rollback_confirm', { version: versionNumber }))) {
            return;
        }

        try {
            await api.rollbackVersion(selectedStrategy, versionNumber);
            message.success(t('maintain.versions.rollback_success', { version: versionNumber }));
            await Promise.all([fetchStrategy(selectedStrategy), fetchVersions(selectedStrategy)]);
        } catch (err) {
            console.error('Rollback failed', err);
            message.error(t('maintain.versions.rollback_failed', 'Failed to rollback'));
        }
    }

    return (
        <div className="strategy-maintain-shell">
            <aside className="strategy-maintain-sidebar">
                <Card className="strategy-panel strategy-library-panel" bordered={false}>
                    <div className="strategy-panel-header">
                        <div>
                            <Title level={3}>{t('maintain.title', 'Strategy Management')}</Title>
                            <Paragraph type="secondary">
                                {t('maintain.subtitle', 'Edit only the strategy class below; backtest engine is fixed.')}
                            </Paragraph>
                        </div>
                        <Space>
                            <Button icon={<AppstoreOutlined />} onClick={() => setShowTemplateLibrary(true)}>
                                {t('maintain.template_library', 'Template Library')}
                            </Button>
                            <Button type="primary" icon={<PlusOutlined />} onClick={() => setShowNewStrategyModal(true)}>
                                {t('maintain.new', 'New')}
                            </Button>
                        </Space>
                    </div>

                    <Input.Search
                        allowClear
                        value={strategySearch}
                        onChange={(event) => setStrategySearch(event.target.value)}
                        placeholder={t('maintain.search_placeholder', 'Search strategies')}
                        className="strategy-search"
                    />

                    <div className="strategy-list-wrap custom-scrollbar">
                        {filteredStrategies.length > 0 ? (
                            <List
                                dataSource={filteredStrategies}
                                renderItem={(item) => (
                                    <List.Item
                                        className={`strategy-list-item ${item === selectedStrategy ? 'active' : ''}`}
                                        onClick={() => setSelectedStrategy(item)}
                                    >
                                        <div className="strategy-list-item-main">
                                            <Text strong={item === selectedStrategy}>{item}</Text>
                                            <Text type="secondary">{t('maintain.strategy_file', 'Python Strategy')}</Text>
                                        </div>
                                        {item === selectedStrategy ? (
                                            <Tag color="cyan">{t('maintain.active', 'Active')}</Tag>
                                        ) : null}
                                    </List.Item>
                                )}
                            />
                        ) : (
                            <div className="strategy-empty-state">
                                <Empty description={t('maintain.no_matching_strategies', 'No matching strategies')} />
                            </div>
                        )}
                    </div>
                </Card>

                <Card className="strategy-panel" bordered={false}>
                    <div className="strategy-side-section-header">
                        <Title level={5}>{t('maintain.parameters', 'Parameters')}</Title>
                        {paramsLoading ? <Spin size="small" /> : null}
                    </div>
                    {strategyParams.length > 0 ? (
                        <div className="strategy-params-grid">
                            {strategyParams.map((param) => (
                                <div key={param.name} className="strategy-param-chip">
                                    <span className="strategy-param-name">{param.name}</span>
                                    <span className="strategy-param-value">{String(param.value)}</span>
                                </div>
                            ))}
                        </div>
                    ) : (
                        <Text type="secondary">{t('maintain.no_parameters', 'No extracted parameters')}</Text>
                    )}
                </Card>

                {showVersionPanel ? (
                    <div className="strategy-version-panel">
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
                ) : null}
            </aside>

            <main className="strategy-maintain-main">
                <Card className="strategy-panel strategy-workbench-panel" bordered={false}>
                    <div className="strategy-workbench-header">
                        <div className="strategy-workbench-title">
                            <Space align="center">
                                <Title level={3}>{selectedStrategy || t('maintain.editor_title', 'Strategy Editor')}</Title>
                                {isDirty ? <Tag color="gold">{t('maintain.unsaved', 'Unsaved')}</Tag> : <Tag color="green">{t('maintain.saved_state', 'Saved')}</Tag>}
                            </Space>
                            <Text type="secondary">
                                {t('maintain.workbench_hint', 'Compile current code, save revisions, or jump straight into backtesting with the selected strategy.')}
                            </Text>
                        </div>

                        <Space wrap>
                            <Button icon={<SyncOutlined />} onClick={() => fetchStrategy(selectedStrategy)} disabled={!selectedStrategy || codeLoading}>
                                {t('maintain.reload', 'Reload')}
                            </Button>
                            <Button icon={<RobotOutlined />} onClick={handleAIAnalysis} disabled={!code || codeLoading}>
                                {t('maintain.ai_analysis', 'AI Analysis')}
                            </Button>
                            <Button icon={<ThunderboltOutlined />} onClick={handleAIRewrite} disabled={!code || codeLoading}>
                                {t('maintain.ai_rewrite', 'AI - Rewrite')}
                            </Button>
                            <Button icon={<CodeOutlined />} onClick={handleCompile} disabled={!code || codeLoading}>
                                {t('maintain.compile', 'Compile')}
                            </Button>
                            <Button type="primary" icon={<SaveOutlined />} onClick={saveStrategy} disabled={!selectedStrategy || codeLoading}>
                                {codeLoading ? t('maintain.saving', 'Saving...') : t('maintain.save_strategy', 'Save Strategy')}
                            </Button>
                        </Space>
                    </div>

                    <div className="strategy-workbench-meta">
                        <div className="strategy-meta-stat">
                            <span>{t('maintain.lines', 'Lines')}</span>
                            <strong>{strategyStats.lines}</strong>
                        </div>
                        <div className="strategy-meta-stat">
                            <span>{t('maintain.functions', 'Functions')}</span>
                            <strong>{strategyStats.functions}</strong>
                        </div>
                        <div className="strategy-meta-stat">
                            <span>{t('maintain.classes', 'Classes')}</span>
                            <strong>{strategyStats.classes}</strong>
                        </div>
                        <div className="strategy-meta-stat">
                            <span>{t('maintain.characters', 'Characters')}</span>
                            <strong>{strategyStats.characters}</strong>
                        </div>
                    </div>

                    <div className="strategy-workbench-grid">
                        <div className="strategy-editor-pane">
                            <div className="strategy-editor-surface">
                                <Editor
                                    height="100%"
                                    defaultLanguage="python"
                                    language="python"
                                    theme="vs-dark"
                                    value={code}
                                    onChange={handleCodeChange}
                                    options={{
                                        fontSize: 14,
                                        minimap: { enabled: false },
                                        scrollBeyondLastLine: false,
                                        wordWrap: 'on',
                                        roundedSelection: false,
                                        automaticLayout: true,
                                        padding: { top: 16 },
                                    }}
                                />
                            </div>
                        </div>

                        <div className="strategy-ops-pane">
                            <Card className="strategy-side-card" bordered={false}>
                                <div className="strategy-side-section-header">
                                    <Title level={5}>{t('maintain.compile_panel', 'Compile Status')}</Title>
                                    {compileState?.status === 'success' ? <CheckCircleOutlined className="compile-success-icon" /> : null}
                                </div>
                                {compileState ? (
                                    <Alert
                                        type={compileState.status === 'success' ? 'success' : 'error'}
                                        showIcon
                                        message={
                                            compileState.status === 'success'
                                                ? t('maintain.compile_ready', 'Ready to run')
                                                : t('maintain.compile_error', 'Compile error')
                                        }
                                        description={compileState.message}
                                    />
                                ) : (
                                    <Alert
                                        type="info"
                                        showIcon
                                        message={t('maintain.compile_hint_title', 'Check before you run')}
                                        description={t('maintain.compile_hint_desc', 'Compile validates the current editor content without saving it to disk.')}
                                    />
                                )}
                            </Card>

                            <Card className="strategy-side-card" bordered={false}>
                                <div className="strategy-side-section-header">
                                    <Title level={5}>{t('maintain.run_panel', 'Run Strategy')}</Title>
                                    <PlayCircleOutlined className="run-icon" />
                                </div>
                                <div className="strategy-run-form">
                                    <label>
                                        <span>{t('config_form.ticker', 'Ticker')}</span>
                                        <Input
                                            value={runConfig.ticker}
                                            onChange={(event) => setRunConfig((prev) => ({ ...prev, ticker: event.target.value.toUpperCase() }))}
                                        />
                                    </label>
                                    <label>
                                        <span>{t('history.start_date', 'Start Date')}</span>
                                        <Input
                                            type="date"
                                            value={runConfig.startDate}
                                            onChange={(event) => setRunConfig((prev) => ({ ...prev, startDate: event.target.value }))}
                                        />
                                    </label>
                                    <label>
                                        <span>{t('history.end_date', 'End Date')}</span>
                                        <Input
                                            type="date"
                                            value={runConfig.endDate}
                                            onChange={(event) => setRunConfig((prev) => ({ ...prev, endDate: event.target.value }))}
                                        />
                                    </label>
                                    <label>
                                        <span>{t('history.initial_cash', 'Initial Cash')}</span>
                                        <Input
                                            value={runConfig.initialCash}
                                            onChange={(event) => setRunConfig((prev) => ({ ...prev, initialCash: event.target.value }))}
                                        />
                                    </label>
                                    <label>
                                        <span>{t('config_form.timeframe', 'Timeframe')}</span>
                                        <select
                                            value={runConfig.timeframe}
                                            onChange={(event) => setRunConfig((prev) => ({ ...prev, timeframe: event.target.value }))}
                                            className="strategy-native-select"
                                        >
                                            <option value="1d">1d</option>
                                            <option value="1h">1h</option>
                                            <option value="15m">15m</option>
                                            <option value="5m">5m</option>
                                            <option value="1m">1m</option>
                                        </select>
                                    </label>
                                </div>
                                <Button
                                    type="primary"
                                    size="large"
                                    icon={<PlayCircleOutlined />}
                                    onClick={handleRunStrategy}
                                    disabled={!selectedStrategy}
                                    block
                                >
                                    {t('maintain.run_related_strategy', 'Run This Strategy')}
                                </Button>
                            </Card>

                            <Card className="strategy-side-card" bordered={false}>
                                <div className="strategy-side-section-header">
                                    <Title level={5}>{t('maintain.workspace_tools', 'Workspace Tools')}</Title>
                                    <HistoryOutlined />
                                </div>
                                <Space direction="vertical" style={{ width: '100%' }}>
                                    <Button block onClick={() => setShowVersionPanel((prev) => !prev)}>
                                        {showVersionPanel ? t('maintain.hide_history', 'Hide Version History') : t('maintain.show_history', 'Show Version History')}
                                    </Button>
                                    <Button block onClick={() => fetchStrategies()}>
                                        {t('maintain.refresh_list', 'Refresh List')}
                                    </Button>
                                    <Button block icon={<WarningOutlined />} disabled={!isDirty} onClick={() => setCode(savedCode)}>
                                        {t('maintain.revert_changes', 'Revert Unsaved Changes')}
                                    </Button>
                                </Space>
                            </Card>
                        </div>
                    </div>
                </Card>
            </main>

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
                title={t('maintain.ai_analysis', 'AI Analysis')}
                t={t}
            />

            {showTemplateLibrary ? (
                <TemplateLibrary
                    onImport={handleTemplateImport}
                    onClose={() => setShowTemplateLibrary(false)}
                />
            ) : null}

            {showDiffViewer && diffData ? (
                <VersionDiffViewer
                    isOpen={showDiffViewer}
                    onClose={() => {
                        setShowDiffViewer(false);
                        setDiffData(null);
                        setSelectedForCompare([]);
                    }}
                    oldCode={diffData.old_code}
                    newCode={diffData.new_code}
                    oldVersion={diffData.oldVersion}
                    newVersion={diffData.newVersion}
                    linesAdded={diffData.lines_added}
                    linesRemoved={diffData.lines_removed}
                    t={t}
                />
            ) : null}
        </div>
    );
}

export default StrategyMaintain;
