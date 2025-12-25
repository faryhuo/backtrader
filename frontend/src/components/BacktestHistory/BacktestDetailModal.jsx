import { useState, useCallback } from 'react'
import { Modal, Tabs, Descriptions, Tag, Button, Select } from 'antd'
import { useTranslation } from 'react-i18next'
import { FileTextOutlined } from '@ant-design/icons'
import dayjs from 'dayjs'
import { useSettingsContext } from '../../contexts/SettingsContext'
import { api } from '../../services/api'
import { useAIAnalysis } from '../../hooks/useAIAnalysis'
import PerformanceOverview from '../RunStrategy/PerformanceOverview'
import TradeLog from '../RunStrategy/TradeLog'
import AIInsight from '../RunStrategy/AIInsight'
import StrategyPlot from '../RunStrategy/StrategyPlot'
import CodeViewer from '../RunStrategy/CodeViewer'
import DeepAnalysis from '../DeepAnalysis'

function BacktestDetailModal({ visible, backtest, onClose, onAnalysisUpdate }) {
    const { t, i18n } = useTranslation()
    const { settings, getAvailableModels } = useSettingsContext()
    const [reportLoading, setReportLoading] = useState(false)

    // Persistence callback for saving AI analysis
    const handleSaveAnalysis = useCallback(async (backtestId, modelName, analysis) => {
        await api.updateBacktestAiAnalysis(backtestId, modelName, analysis)
        // Update backtest object with new analysis
        if (backtest) {
            backtest.ai_analysis = { ...backtest.ai_analysis, [modelName]: analysis }
        }
        // Notify parent component to refresh data if callback provided
        if (onAnalysisUpdate && backtest) {
            onAnalysisUpdate(backtest.backtest_id, backtest.ai_analysis)
        }
    }, [backtest, onAnalysisUpdate])

    // Use the unified AI analysis hook
    const {
        selectedModel,
        setSelectedModel,
        analyses,
        activeTab,
        setActiveTab,
        aiLoading,
        runAnalysis,
        availableModels,
    } = useAIAnalysis({
        getAvailableModels,
        settings,
        initialAnalyses: backtest?.ai_analysis || {},
        onAnalysisSaved: handleSaveAnalysis,
    })

    if (!backtest) return null

    const tradeList = backtest.metrics?.trade_details?.trades || []

    const result = {
        metrics: backtest.metrics,
        plot_url: backtest.plot_url
    }

    const handleAIAnalysis = async () => {
        if (!backtest || !backtest.plot_url) {
            return
        }
        await runAnalysis({
            result,
            strategyName: backtest.strategy_name,
            ticker: backtest.ticker,
            startDate: backtest.start_date,
            endDate: backtest.end_date,
            strategyCode: backtest.strategy_code,
            backtestId: backtest.backtest_id,
            t,
        })
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
                    include_ai_analysis: Object.keys(analyses).length > 0
                },
                language: i18n.language?.startsWith('zh') ? 'zh' : 'en'
            })

            // Use message from imported antd
            const { message } = await import('antd')
            message.success(t('history.report_generating', 'Report generation started. You can view it in the Report Center.'))
        } catch (err) {
            console.error('Failed to generate report:', err)
            const { message } = await import('antd')
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
                        {Object.keys(analyses).length > 0 ? (
                            <AIInsight
                                analyses={analyses}
                                activeTab={activeTab || Object.keys(analyses)[0]}
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
