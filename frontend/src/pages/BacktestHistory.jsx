import { useState, useCallback, useMemo } from 'react';
import { Table, message } from 'antd';
import { useTranslation } from 'react-i18next';
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
                <Table
                    columns={columns}
                    dataSource={dataSource}
                    rowKey={rowKey}
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
