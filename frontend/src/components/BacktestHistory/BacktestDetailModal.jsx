import { useState, useCallback } from 'react'
import { Modal, Tabs, Descriptions, Tag, Button, Dropdown, message, Space } from 'antd'
import { useTranslation } from 'react-i18next'
import { FileTextOutlined, DownloadOutlined, AreaChartOutlined, DownOutlined } from '@ant-design/icons'
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
    const { settings } = useSettingsContext()
    const [reportLoading, setReportLoading] = useState(false)
    const [pyfolioLoading, setPyfolioLoading] = useState(false)
    const [tearsheetLoading, setTearsheetLoading] = useState(false)

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
        analyses,
        activeTab,
        setActiveTab,
        aiLoading,
        runAnalysis,
    } = useAIAnalysis({
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

    const handleExportPyFolio = async () => {
        if (!backtest || !backtest.backtest_id) {
            return
        }
        setPyfolioLoading(true)

        try {
            const blob = await api.exportPyFolioData(backtest.backtest_id)

            // Create download link
            const url = URL.createObjectURL(blob)
            const link = document.createElement('a')
            link.href = url
            link.download = `pyfolio_export_${backtest.ticker}_${backtest.backtest_id.slice(0, 8)}.zip`
            document.body.appendChild(link)
            link.click()
            document.body.removeChild(link)
            URL.revokeObjectURL(url)

            message.success(t('history.pyfolio_export_success', 'PyFolio data exported successfully'))
        } catch (err) {
            console.error('Failed to export PyFolio data:', err)
            message.error(t('history.pyfolio_export_failed', 'Failed to export PyFolio data'))
        } finally {
            setPyfolioLoading(false)
        }
    }

    const handleGenerateTearSheet = async () => {
        if (!backtest || !backtest.backtest_id) {
            return
        }

        // Open window immediately on user click to avoid popup blocker
        const newWindow = window.open('', '_blank')
        if (!newWindow) {
            message.warning(t('history.tearsheet_popup_blocked', 'Popup blocked. Please allow popups and try again.'))
            return
        }

        // Show loading state in the new window
        newWindow.document.write(`
            <!DOCTYPE html>
            <html>
            <head>
                <title>Loading Tear Sheet...</title>
                <style>
                    body {
                        display: flex;
                        justify-content: center;
                        align-items: center;
                        height: 100vh;
                        margin: 0;
                        font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif;
                        background: #f5f5f5;
                    }
                    .loader {
                        text-align: center;
                    }
                    .spinner {
                        border: 4px solid #f3f3f3;
                        border-top: 4px solid #1890ff;
                        border-radius: 50%;
                        width: 40px;
                        height: 40px;
                        animation: spin 1s linear infinite;
                        margin: 0 auto 16px;
                    }
                    @keyframes spin {
                        0% { transform: rotate(0deg); }
                        100% { transform: rotate(360deg); }
                    }
                </style>
            </head>
            <body>
                <div class="loader">
                    <div class="spinner"></div>
                    <div>Generating Tear Sheet...</div>
                </div>
            </body>
            </html>
        `)

        setTearsheetLoading(true)

        try {
            const result = await api.generatePyFolioTearSheet(backtest.backtest_id)

            if (result.html) {
                // Write the tear sheet HTML to the already-opened window
                newWindow.document.open()
                newWindow.document.write(result.html)
                newWindow.document.close()
                message.success(t('history.tearsheet_generated', 'Tear sheet generated successfully'))
            } else {
                newWindow.close()
                message.error(t('history.tearsheet_failed', 'Failed to generate tear sheet.'))
            }
        } catch (err) {
            console.error('Failed to generate tear sheet:', err)
            newWindow.close()
            message.error(t('history.tearsheet_failed', 'Failed to generate tear sheet. QuantStats may not be installed on the server.'))
        } finally {
            setTearsheetLoading(false)
        }
    }

    const isExporting = pyfolioLoading || tearsheetLoading

    const pyfolioMenuItems = [
        {
            key: 'export',
            label: t('history.pyfolio_export_data', 'Export Data (ZIP)'),
            icon: <DownloadOutlined />,
            disabled: isExporting,
            onClick: handleExportPyFolio,
        },
        {
            key: 'tearsheet',
            label: t('history.pyfolio_tearsheet', 'Generate Tear Sheet'),
            icon: <AreaChartOutlined />,
            disabled: isExporting,
            onClick: handleGenerateTearSheet,
        },
    ]

    return (
        <Modal
            title={t('history.detail_title')}
            open={visible}
            onCancel={onClose}
            width="90%"
            footer={[
                <Dropdown
                    key="pyfolio"
                    menu={{ items: pyfolioMenuItems }}
                    trigger={['click']}
                    placement="top"
                    disabled={isExporting}
                    getPopupContainer={(triggerNode) => triggerNode.parentNode}
                >
                    <Button
                        icon={<AreaChartOutlined />}
                        loading={isExporting}
                        onClick={(e) => e.stopPropagation()}
                    >
                        <Space>
                            {t('history.pyfolio_export', 'PyFolio')}
                            <DownOutlined />
                        </Space>
                    </Button>
                </Dropdown>,
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
