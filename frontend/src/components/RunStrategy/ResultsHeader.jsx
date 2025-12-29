import { useState } from 'react';
import { Tabs, Button, Dropdown, Space, message } from 'antd';
import {
    BarChartOutlined,
    StockOutlined,
    CodeOutlined,
    CalendarOutlined,
    DollarOutlined,
    FileTextOutlined,
    AreaChartOutlined,
    DownloadOutlined,
    DownOutlined
} from '@ant-design/icons';
import { useTranslation } from 'react-i18next';
import { api } from '../../services/api';

/**
 * Results section with header card and tabs
 * Displays backtest results with parameters summary and tab navigation
 */
function ResultsHeader({ t, ticker, selectedStrategy, startDate, endDate, initialCash, paramOverrides, tabItems, backtestId, analyses }) {
    const { i18n } = useTranslation();
    const [reportLoading, setReportLoading] = useState(false);
    const [pyfolioLoading, setPyfolioLoading] = useState(false);
    const [tearsheetLoading, setTearsheetLoading] = useState(false);

    const handleGenerateReport = async () => {
        if (!backtestId) {
            message.warning(t('history.no_backtest_id', 'No backtest ID available'));
            return;
        }
        setReportLoading(true);

        try {
            const reportTitle = `${selectedStrategy} - ${ticker} (${startDate} ~ ${endDate})`;

            await api.generateReport({
                report_type: 'backtest',
                title: reportTitle,
                source_ids: [backtestId],
                config: {
                    include_ai_analysis: analyses && Object.keys(analyses).length > 0
                },
                language: i18n.language?.startsWith('zh') ? 'zh' : 'en'
            });

            message.success(t('history.report_generating', 'Report generation started. You can view it in the Report Center.'));
        } catch (err) {
            console.error('Failed to generate report:', err);
            message.error(t('history.report_generation_failed', 'Failed to generate report'));
        } finally {
            setReportLoading(false);
        }
    };

    const handleExportPyFolio = async () => {
        if (!backtestId) {
            message.warning(t('history.no_backtest_id', 'No backtest ID available'));
            return;
        }
        setPyfolioLoading(true);

        try {
            const blob = await api.exportPyFolioData(backtestId);

            // Create download link
            const url = URL.createObjectURL(blob);
            const link = document.createElement('a');
            link.href = url;
            link.download = `pyfolio_export_${ticker}_${backtestId.slice(0, 8)}.zip`;
            document.body.appendChild(link);
            link.click();
            document.body.removeChild(link);
            URL.revokeObjectURL(url);

            message.success(t('history.pyfolio_export_success', 'PyFolio data exported successfully'));
        } catch (err) {
            console.error('Failed to export PyFolio data:', err);
            message.error(t('history.pyfolio_export_failed', 'Failed to export PyFolio data'));
        } finally {
            setPyfolioLoading(false);
        }
    };

    const handleGenerateTearSheet = async () => {
        if (!backtestId) {
            message.warning(t('history.no_backtest_id', 'No backtest ID available'));
            return;
        }

        // Open window immediately on user click to avoid popup blocker
        const newWindow = window.open('', '_blank');
        if (!newWindow) {
            message.warning(t('history.tearsheet_popup_blocked', 'Popup blocked. Please allow popups and try again.'));
            return;
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
        `);

        setTearsheetLoading(true);

        try {
            const result = await api.generatePyFolioTearSheet(backtestId);

            if (result.html) {
                // Write the tear sheet HTML to the already-opened window
                newWindow.document.open();
                newWindow.document.write(result.html);
                newWindow.document.close();
                message.success(t('history.tearsheet_generated', 'Tear sheet generated successfully'));
            } else {
                newWindow.close();
                message.error(t('history.tearsheet_failed', 'Failed to generate tear sheet.'));
            }
        } catch (err) {
            console.error('Failed to generate tear sheet:', err);
            newWindow.close();
            message.error(t('history.tearsheet_failed', 'Failed to generate tear sheet. QuantStats may not be installed on the server.'));
        } finally {
            setTearsheetLoading(false);
        }
    };

    const isExporting = pyfolioLoading || tearsheetLoading;

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
    ];
    return (
        <div className="results-animate-in">
            <div className="backtest-header-card">
                <div className="backtest-header-icon">
                    <BarChartOutlined />
                </div>
                <div className="backtest-header-content">
                    <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}>
                        <h2 className="backtest-header-title">{t('history.backtest_results', 'Backtest Results')}</h2>
                        {backtestId && (
                            <Space>
                                <Dropdown
                                    menu={{ items: pyfolioMenuItems }}
                                    trigger={['click']}
                                    placement="bottom"
                                    disabled={isExporting}
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
                                </Dropdown>
                                <Button
                                    type="primary"
                                    icon={<FileTextOutlined />}
                                    onClick={handleGenerateReport}
                                    loading={reportLoading}
                                >
                                    {t('history.generate_report', 'Generate Report')}
                                </Button>
                            </Space>
                        )}
                    </div>
                    <div className="backtest-header-meta">
                        <div className="backtest-meta-item">
                            <StockOutlined />
                            <span className="backtest-meta-value">{ticker}</span>
                        </div>
                        <div className="backtest-meta-item">
                            <CodeOutlined />
                            <span className="backtest-meta-value">{selectedStrategy}</span>
                        </div>
                        <div className="backtest-meta-item">
                            <CalendarOutlined />
                            <span className="backtest-meta-value">{startDate} ~ {endDate}</span>
                        </div>
                        <div className="backtest-meta-item">
                            <DollarOutlined />
                            <span className="backtest-meta-value">${parseFloat(initialCash).toLocaleString()}</span>
                        </div>
                    </div>
                    {paramOverrides && Object.keys(paramOverrides).length > 0 && (
                        <div className="param-pills">
                            {Object.entries(paramOverrides).map(([key, value]) => (
                                <span key={key} className="param-pill">
                                    <span className="param-pill-key">{key}:</span>
                                    {typeof value === 'number' ? value.toLocaleString() : String(value)}
                                </span>
                            ))}
                        </div>
                    )}
                </div>
            </div>

            <Tabs
                defaultActiveKey="overview"
                className="strategy-results-tabs"
                items={tabItems}
            />
        </div>
    );
}

export default ResultsHeader;
