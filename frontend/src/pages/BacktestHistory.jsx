import { useState, useCallback, useMemo } from 'react';
import { Button, Space, Table, message } from 'antd';
import { FileTextOutlined } from '@ant-design/icons';
import { useTranslation } from 'react-i18next';
import i18n from '../i18n';
import { api } from '../services/api';
import { getStrategyBacktestColumns, getPortfolioBacktestColumns } from '../utils/tableColumns';
import { useBacktestHistory } from '../hooks/useBacktestHistory';
import FilterBar from '../components/BacktestHistory/FilterBar';
import BacktestDetailModal from '../components/BacktestHistory/BacktestDetailModal';
import PortfolioDetailModal from '../components/BacktestHistory/PortfolioDetailModal';
import '../index.css';

/**
 * BacktestHistory Page - Container Component
 * 
 * Displays history of strategy and portfolio backtests with filtering,
 * pagination, and detail modals. Uses useBacktestHistory hook for
 * all data management logic.
 */
function BacktestHistory() {
    const { t } = useTranslation();
    const reportLanguage = i18n.language?.startsWith('zh') ? 'zh' : 'en';

    // Use custom hook for all data management
    const {
        backtests,
        portfolios,
        loading,
        strategies,
        recordType,
        handleRecordTypeChange,
        ticker,
        setTicker,
        strategyName,
        setStrategyName,
        dateRange,
        setDateRange,
        pagination,
        handleTableChange,
        handleFilter,
        handleReset,
        fetchBacktests,
        fetchPortfolios,
    } = useBacktestHistory({ initialRecordType: 'strategy', t });

    // Modal state (kept in page component for simplicity)
    const [selectedBacktest, setSelectedBacktest] = useState(null);
    const [selectedPortfolio, setSelectedPortfolio] = useState(null);
    const [detailModalVisible, setDetailModalVisible] = useState(false);
    const [portfolioModalVisible, setPortfolioModalVisible] = useState(false);
    const [selectedComparisonRowKeys, setSelectedComparisonRowKeys] = useState([]);
    const [selectedComparisonRows, setSelectedComparisonRows] = useState([]);
    const [comparisonReportLoading, setComparisonReportLoading] = useState(false);

    // Modal handlers
    const handleViewDetail = useCallback(async (record) => {
        try {
            const detail = await api.getBacktestDetail(record.backtest_id);
            setSelectedBacktest(detail);
            setDetailModalVisible(true);
        } catch (err) {
            message.error(t('history.detail_error'));
            console.error(err);
        }
    }, [t]);

    const handleViewPortfolioDetail = useCallback(async (record) => {
        try {
            const detail = await api.getPortfolioDetail(record.portfolio_id);
            setSelectedPortfolio(detail);
            setPortfolioModalVisible(true);
        } catch (err) {
            message.error(t('history.portfolio_detail_error'));
            console.error(err);
        }
    }, [t]);

    const handleAnalysisUpdate = useCallback((_backtestId, analysis) => {
        setSelectedBacktest(prev => ({
            ...prev,
            ai_analysis: analysis
        }));
    }, []);

    const handleDelete = useCallback(async (backtestId) => {
        try {
            await api.deleteBacktest(backtestId);
            message.success(t('history.delete_success'));
            fetchBacktests();
        } catch (err) {
            message.error(t('history.delete_error'));
            console.error(err);
        }
    }, [t, fetchBacktests]);

    const handleDeletePortfolio = useCallback(async (portfolioId) => {
        try {
            await api.deletePortfolio(portfolioId);
            message.success(t('history.portfolio_delete_success'));
            fetchPortfolios();
        } catch (err) {
            message.error(t('history.portfolio_delete_error'));
            console.error(err);
        }
    }, [t, fetchPortfolios]);

    const handleCloseBacktestModal = useCallback(() => {
        setDetailModalVisible(false);
        setSelectedBacktest(null);
    }, []);

    const handleClosePortfolioModal = useCallback(() => {
        setPortfolioModalVisible(false);
        setSelectedPortfolio(null);
    }, []);

    const handleGenerateComparisonReport = useCallback(async () => {
        if (selectedComparisonRowKeys.length < 2) {
            message.warning(t('history.comparison_select_min', 'Select at least two backtests to generate a comparison report.'));
            return;
        }

        try {
            setComparisonReportLoading(true);
            const title = t('history.comparison_report_title', {
                count: selectedComparisonRowKeys.length,
                defaultValue: 'Backtest Comparison ({{count}} runs)',
            });

            await api.generateReport({
                report_type: 'comparison',
                title,
                source_ids: selectedComparisonRowKeys,
                config: {
                    selected_backtests: selectedComparisonRows.map((row) => ({
                        backtest_id: row.backtest_id,
                        ticker: row.ticker,
                        strategy_name: row.strategy_name,
                    })),
                },
                language: reportLanguage,
            });

            message.success(t('history.comparison_report_generating', 'Comparison report generation started. You can view it in the Report Center.'));
            setSelectedComparisonRowKeys([]);
            setSelectedComparisonRows([]);
        } catch (err) {
            console.error('Failed to generate comparison report:', err);
            message.error(t('history.comparison_report_failed', 'Failed to generate comparison report'));
        } finally {
            setComparisonReportLoading(false);
        }
    }, [reportLanguage, selectedComparisonRowKeys, selectedComparisonRows, t]);

    const rowSelection = useMemo(() => {
        if (recordType !== 'strategy') {
            return undefined;
        }

        return {
            selectedRowKeys: selectedComparisonRowKeys,
            preserveSelectedRowKeys: true,
            onChange: (newSelectedRowKeys, newSelectedRows) => {
                setSelectedComparisonRowKeys(newSelectedRowKeys);
                setSelectedComparisonRows(newSelectedRows);
            },
        };
    }, [recordType, selectedComparisonRowKeys]);

    // Get columns from utilities
    const strategyColumns = useMemo(() => getStrategyBacktestColumns({
        t,
        onView: handleViewDetail,
        onDelete: handleDelete,
    }), [t, handleViewDetail, handleDelete]);

    const portfolioColumns = useMemo(() => getPortfolioBacktestColumns({
        t,
        onView: handleViewPortfolioDetail,
        onDelete: handleDeletePortfolio,
    }), [t, handleViewPortfolioDetail, handleDeletePortfolio]);

    // Derived values
    const columns = recordType === 'strategy' ? strategyColumns : portfolioColumns;
    const dataSource = recordType === 'strategy' ? backtests : portfolios;
    const rowKey = recordType === 'strategy' ? 'backtest_id' : 'portfolio_id';
    const emptyText = recordType === 'strategy' ? t('history.no_history') : t('history.no_portfolio_history');

    return (
        <div className="page-container">
            <div className="page-header">
                <h1>{t('history.title')}</h1>
                <p>{t('history.subtitle')}</p>
            </div>

            <FilterBar
                t={t}
                recordType={recordType}
                onRecordTypeChange={handleRecordTypeChange}
                ticker={ticker}
                setTicker={setTicker}
                strategyName={strategyName}
                setStrategyName={setStrategyName}
                dateRange={dateRange}
                setDateRange={setDateRange}
                strategies={strategies}
                onFilter={handleFilter}
                onReset={handleReset}
            />

            <div className="card">
                {recordType === 'strategy' && (
                    <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', gap: '1rem', marginBottom: '1rem', flexWrap: 'wrap' }}>
                        <div style={{ color: 'var(--text-secondary)' }}>
                            {t('history.comparison_selection_count', {
                                count: selectedComparisonRowKeys.length,
                                defaultValue: '{{count}} backtests selected for comparison',
                            })}
                        </div>
                        <Space wrap>
                            <Button onClick={() => {
                                setSelectedComparisonRowKeys([]);
                                setSelectedComparisonRows([]);
                            }}
                            disabled={selectedComparisonRowKeys.length === 0}
                            >
                                {t('history.clear_selection', 'Clear Selection')}
                            </Button>
                            <Button
                                type="primary"
                                icon={<FileTextOutlined />}
                                onClick={handleGenerateComparisonReport}
                                loading={comparisonReportLoading}
                                disabled={selectedComparisonRowKeys.length < 2}
                            >
                                {t('history.generate_comparison_report', 'Generate Comparison Report')}
                            </Button>
                        </Space>
                    </div>
                )}
                <Table
                    columns={columns}
                    dataSource={dataSource}
                    rowKey={rowKey}
                    rowSelection={rowSelection}
                    loading={loading}
                    pagination={pagination}
                    onChange={handleTableChange}
                    scroll={{ x: 'max-content' }}
                    locale={{ emptyText }}
                />
            </div>

            {selectedBacktest && (
                <BacktestDetailModal
                    visible={detailModalVisible}
                    backtest={selectedBacktest}
                    onClose={handleCloseBacktestModal}
                    onAnalysisUpdate={handleAnalysisUpdate}
                />
            )}

            {selectedPortfolio && (
                <PortfolioDetailModal
                    visible={portfolioModalVisible}
                    portfolio={selectedPortfolio}
                    onClose={handleClosePortfolioModal}
                />
            )}
        </div>
    );
}

export default BacktestHistory;
