import { useState } from 'react'
import { Modal, Tabs, Descriptions, Tag, Button, Select, message } from 'antd'
import { useTranslation } from 'react-i18next'
import { FileTextOutlined } from '@ant-design/icons'
import dayjs from 'dayjs'
import { performFullStrategyAnalysis } from '../../services/aiAnalysis'
import { useSettingsContext } from '../../contexts/SettingsContext'
import { api } from '../../services/api'
import PerformanceOverview from '../RunStrategy/PerformanceOverview'
import TradeLog from '../RunStrategy/TradeLog'
import AIInsight from '../RunStrategy/AIInsight'
import StrategyPlot from '../RunStrategy/StrategyPlot'
import CodeViewer from '../RunStrategy/CodeViewer'
import DeepAnalysis from '../DeepAnalysis'

function BacktestDetailModal({ visible, backtest, onClose, onAnalysisUpdate }) {
    const { t, i18n } = useTranslation()
    const { settings, getAvailableModels } = useSettingsContext()
    const [aiLoading, setAiLoading] = useState(false)
    const [reportLoading, setReportLoading] = useState(false)
    const [analyses, setAnalyses] = useState({})
    const [activeTab, setActiveTab] = useState(null)

    // Initialize available models from settings context
    const availableModels = getAvailableModels()
    const [selectedModel, setSelectedModel] = useState(availableModels[0] || 'gpt-4o')

    if (!backtest) return null

    // Load existing AI analyses from backtest data (stored as JSON: {model_name: analysis_content})
    const savedAnalyses = backtest.ai_analysis || {}

    // Merge saved analyses with new analyses from current session
    const allAnalyses = { ...savedAnalyses, ...analyses }

    const tradeList = backtest.metrics?.trade_details?.trades || []

    const result = {
        metrics: backtest.metrics,
        plot_url: backtest.plot_url
    }

    const handleAIAnalysis = async () => {
        if (!backtest || !backtest.plot_url) {
            return
        }
        setAiLoading(true)

        try {
            const data = await performFullStrategyAnalysis({
                result: result,
                strategyName: backtest.strategy_name,
                ticker: backtest.ticker,
                startDate: backtest.start_date,
                endDate: backtest.end_date,
                model: selectedModel,
                initialStrategyCode: backtest.strategy_code,
                settings: settings
            })

            setAnalyses(prev => {
                const newState = { ...prev, [selectedModel]: data.analysis }
                return newState
            })
            setActiveTab(selectedModel)

            // Save AI analysis to backtest history
            if (backtest.backtest_id) {
                try {
                    await api.updateBacktestAiAnalysis(backtest.backtest_id, selectedModel, data.analysis)
                    message.success(t('history.ai_analysis_saved', 'AI analysis saved successfully'))

                    // Update backtest object with new analysis
                    backtest.ai_analysis = { ...backtest.ai_analysis, [selectedModel]: data.analysis }

                    // Notify parent component to refresh data if callback provided
                    if (onAnalysisUpdate) {
                        onAnalysisUpdate(backtest.backtest_id, backtest.ai_analysis)
                    }
                } catch (err) {
                    console.error("Failed to save AI analysis to history:", err)
                    message.error(t('history.ai_analysis_save_error', 'Failed to save AI analysis'))
                }
            }

        } catch (err) {
            console.error(err)
            message.error(t('history.ai_analysis_failed', { error: err.message }))
        } finally {
            setAiLoading(false)
        }
    }

    const handleGenerateReport = async () => {
        if (!backtest || !backtest.backtest_id) {
            return
        }
        setReportLoading(true)

        try {
            const reportTitle = `${backtest.strategy_name} - ${backtest.ticker} (${backtest.start_date} ~ ${backtest.end_date})`

            await api.generateReport({
                report_type: 'backtest',
                title: reportTitle,
                source_ids: [backtest.backtest_id],
                config: {
                    include_ai_analysis: Object.keys(allAnalyses).length > 0
                },
                language: i18n.language?.startsWith('zh') ? 'zh' : 'en'
            })

            message.success(t('history.report_generating', 'Report generation started. You can view it in the Report Center.'))
        } catch (err) {
            console.error('Failed to generate report:', err)
            message.error(t('history.report_generation_failed', 'Failed to generate report'))
        } finally {
            setReportLoading(false)
        }
    }

    return (
        <Modal
            title={t('history.detail_title')}
            open={visible}
            onCancel={onClose}
            width="90%"
            footer={[
                <Button
                    key="generate-report"
                    type="primary"
                    icon={<FileTextOutlined />}
                    onClick={handleGenerateReport}
                    loading={reportLoading}
                >
                    {t('history.generate_report', 'Generate Report')}
                </Button>,
                <Button key="close" onClick={onClose}>
                    {t('common.close', 'Close')}
                </Button>
            ]}
            style={{ top: 20 }}
        >
            <Tabs defaultActiveKey="overview">
                <Tabs.TabPane tab={t('history.tab_overview')} key="overview">
                    <Descriptions bordered column={2} size="small">
                        <Descriptions.Item label={t('history.backtest_id')}>
                            {backtest.backtest_id}
                        </Descriptions.Item>
                        <Descriptions.Item label={t('history.run_date')}>
                            {backtest.created_at ? dayjs(backtest.created_at).format('YYYY-MM-DD HH:mm:ss') : 'N/A'}
                        </Descriptions.Item>
                        <Descriptions.Item label={t('config_form.ticker')}>
                            <Tag color="blue">{backtest.ticker}</Tag>
                        </Descriptions.Item>
                        <Descriptions.Item label={t('config_form.strategy')}>
                            {backtest.strategy_name}
                        </Descriptions.Item>
                        <Descriptions.Item label={t('history.test_period')}>
                            {backtest.start_date} ~ {backtest.end_date}
                        </Descriptions.Item>
                        <Descriptions.Item label={t('config_form.initial_cash')}>
                            ${backtest.initial_cash?.toLocaleString()}
                        </Descriptions.Item>
                        <Descriptions.Item label={t('config_form.commission')}>
                            {backtest.commission}
                        </Descriptions.Item>
                        <Descriptions.Item label={t('config_form.stake')}>
                            {backtest.stake}
                        </Descriptions.Item>
                        {backtest.params && Object.keys(backtest.params).length > 0 && (
                            <Descriptions.Item label={t('history.strategy_params', 'Strategy Params')} span={2}>
                                <div style={{ display: 'flex', flexWrap: 'wrap', gap: '8px' }}>
                                    {Object.entries(backtest.params).map(([key, value]) => (
                                        <Tag key={key} color="purple">
                                            {key}: {typeof value === 'number' ? value.toLocaleString() : String(value)}
                                        </Tag>
                                    ))}
                                </div>
                            </Descriptions.Item>
                        )}
                    </Descriptions>

                    <div style={{ marginTop: 20 }}>
                        <PerformanceOverview
                            result={result}
                        />
                    </div>
                </Tabs.TabPane>

                <Tabs.TabPane tab={t('history.tab_chart')} key="chart">
                    <div style={{ padding: '20px 0' }}>
                        <StrategyPlot
                            result={result}
                        />
                    </div>
                </Tabs.TabPane>

                <Tabs.TabPane tab={t('history.tab_trades')} key="trades">
                    <TradeLog trades={tradeList} />
                </Tabs.TabPane>

                <Tabs.TabPane tab={t('history.tab_ai_insight', 'AI Insight')} key="ai_insight">
                    <div style={{ padding: '20px' }}>
                        {/* AI Analysis Controls */}
                        <div style={{
                            display: 'flex',
                            justifyContent: 'center',
                            gap: '1rem',
                            alignItems: 'center',
                            padding: '1rem',
                            background: 'rgba(22, 27, 34, 0.6)',
                            borderRadius: '8px',
                            marginBottom: '1.5rem'
                        }}>
                            <Select
                                value={selectedModel}
                                onChange={(value) => setSelectedModel(value)}
                                style={{ width: 150 }}
                            >
                                {availableModels.map(m => (
                                    <Select.Option key={m} value={m}>{m}</Select.Option>
                                ))}
                            </Select>
                            <Button
                                type="primary"
                                onClick={handleAIAnalysis}
                                loading={aiLoading}
                            >
                                {aiLoading ? t('strategy_plot.interpreting', 'Analyzing...') : t('strategy_plot.ai_interpretation', 'AI Analysis')}
                            </Button>
                        </div>

                        {/* AI Analysis Results */}
                        {Object.keys(allAnalyses).length > 0 ? (
                            <AIInsight
                                analyses={allAnalyses}
                                activeTab={activeTab || Object.keys(allAnalyses)[0]}
                                onTabChange={setActiveTab}
                            />
                        ) : (
                            <div style={{
                                textAlign: 'center',
                                padding: '2rem',
                                color: '#888'
                            }}>
                                {t('history.no_ai_analysis', 'No AI analysis available. Click the button above to generate one.')}
                            </div>
                        )}
                    </div>
                </Tabs.TabPane>

                <Tabs.TabPane tab={t('history.tab_deep_analysis', 'Deep Analysis')} key="deep_analysis">
                    <DeepAnalysis backtest={backtest} />
                </Tabs.TabPane>

                {backtest.strategy_code && (
                    <Tabs.TabPane tab={t('history.tab_strategy_code', 'Strategy Code')} key="strategy_code">
                        <div style={{ padding: '20px' }}>
                            <CodeViewer
                                code={backtest.strategy_code}
                                language="python"
                                params={backtest.params}
                                maxHeight={500}
                            />
                        </div>
                    </Tabs.TabPane>
                )}
            </Tabs>
        </Modal>
    )
}

export default BacktestDetailModal
