import { useState, useEffect, useCallback, useMemo } from 'react';
import { Table, Input, Select, DatePicker, Button, Space, message, Segmented } from 'antd';
import { ReloadOutlined, FilterOutlined, FundOutlined, PieChartOutlined } from '@ant-design/icons';
import dayjs from 'dayjs';
import { useTranslation } from 'react-i18next';
import { api } from '../services/api';
import { getStrategyBacktestColumns, getPortfolioBacktestColumns } from '../utils/tableColumns';
import BacktestDetailModal from '../components/BacktestHistory/BacktestDetailModal';
import PortfolioDetailModal from '../components/BacktestHistory/PortfolioDetailModal';
import '../index.css';

const { RangePicker } = DatePicker;

function BacktestHistory() {
    const { t } = useTranslation();

    // Record type toggle
    const [recordType, setRecordType] = useState('strategy');

    // Data state
    const [backtests, setBacktests] = useState([]);
    const [portfolios, setPortfolios] = useState([]);
    const [loading, setLoading] = useState(false);

    // Modal state
    const [selectedBacktest, setSelectedBacktest] = useState(null);
    const [selectedPortfolio, setSelectedPortfolio] = useState(null);
    const [detailModalVisible, setDetailModalVisible] = useState(false);
    const [portfolioModalVisible, setPortfolioModalVisible] = useState(false);

    // Filters
    const [ticker, setTicker] = useState(null);
    const [strategyName, setStrategyName] = useState(null);
    const [dateRange, setDateRange] = useState(null);
    const [strategies, setStrategies] = useState([]);

    // Pagination & Sorting
    const [pagination, setPagination] = useState({
        current: 1,
        pageSize: 20,
        total: 0
    });
    const [sortField, setSortField] = useState('created_at');
    const [sortOrder, setSortOrder] = useState('desc');

    // Fetch strategies on mount
    useEffect(() => {
        fetchStrategies();
    }, []);

    // Fetch data when record type changes
    useEffect(() => {
        if (recordType === 'strategy') {
            fetchBacktests();
        } else {
            fetchPortfolios();
        }
        // eslint-disable-next-line react-hooks/exhaustive-deps
    }, [recordType]);

    const fetchStrategies = async () => {
        try {
            const names = await api.getStrategies();
            setStrategies(names);
        } catch (err) {
            console.error('Failed to fetch strategies:', err);
        }
    };

    const fetchBacktests = useCallback(async (params = {}) => {
        setLoading(true);
        try {
            const queryParams = {
                ticker: params.ticker !== undefined ? params.ticker : ticker,
                strategy_name: params.strategyName !== undefined ? params.strategyName : strategyName,
                start_date: params.dateRange?.[0] || dateRange?.[0],
                end_date: params.dateRange?.[1] || dateRange?.[1],
                sort_by: params.sortField || sortField,
                sort_order: params.sortOrder || sortOrder,
                limit: params.pageSize || pagination.pageSize,
                offset: ((params.current || pagination.current) - 1) * (params.pageSize || pagination.pageSize)
            };

            const result = await api.getBacktestHistory(queryParams);
            setBacktests(result.backtests || []);
            setPagination(prev => ({
                ...prev,
                total: result.total || 0,
                current: params.current || prev.current,
                pageSize: params.pageSize || prev.pageSize
            }));
        } catch (err) {
            message.error(t('history.fetch_error'));
            console.error(err);
        } finally {
            setLoading(false);
        }
    }, [ticker, strategyName, dateRange, sortField, sortOrder, pagination.pageSize, pagination.current, t]);

    const fetchPortfolios = useCallback(async (params = {}) => {
        setLoading(true);
        try {
            const queryParams = {
                sort_by: params.sortField || sortField,
                sort_order: params.sortOrder || sortOrder,
                limit: params.pageSize || pagination.pageSize,
                offset: ((params.current || pagination.current) - 1) * (params.pageSize || pagination.pageSize)
            };

            const result = await api.getPortfolioHistory(queryParams);
            setPortfolios(result.results || []);
            setPagination(prev => ({
                ...prev,
                total: result.count || 0,
                current: params.current || prev.current,
                pageSize: params.pageSize || prev.pageSize
            }));
        } catch (err) {
            message.error(t('history.fetch_error'));
            console.error(err);
        } finally {
            setLoading(false);
        }
    }, [sortField, sortOrder, pagination.pageSize, pagination.current, t]);

    // Handlers
    const handleTableChange = useCallback((newPagination, _filters, sorter) => {
        const sortFieldMap = {
            'created_at': 'created_at',
            'total_return': 'total_return',
            'sharpe_ratio': 'sharpe_ratio',
            'weighted_sharpe': 'weighted_sharpe'
        };

        const newSortField = sorter.field ? sortFieldMap[sorter.field] : 'created_at';
        const newSortOrder = sorter.order === 'ascend' ? 'asc' : 'desc';

        setSortField(newSortField);
        setSortOrder(newSortOrder);

        const fetchFn = recordType === 'strategy' ? fetchBacktests : fetchPortfolios;
        fetchFn({
            current: newPagination.current,
            pageSize: newPagination.pageSize,
            sortField: newSortField,
            sortOrder: newSortOrder
        });
    }, [recordType, fetchBacktests, fetchPortfolios]);

    const handleFilter = useCallback(() => {
        setPagination(prev => ({ ...prev, current: 1 }));
        fetchBacktests({ current: 1 });
    }, [fetchBacktests]);

    const handleReset = useCallback(() => {
        setTicker(null);
        setStrategyName(null);
        setDateRange(null);
        setPagination(prev => ({ ...prev, current: 1 }));
        const fetchFn = recordType === 'strategy' ? fetchBacktests : fetchPortfolios;
        fetchFn({
            current: 1,
            ticker: null,
            strategyName: null,
            dateRange: null
        });
    }, [recordType, fetchBacktests, fetchPortfolios]);

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

    const handleRecordTypeChange = useCallback((value) => {
        setRecordType(value);
        setPagination(prev => ({ ...prev, current: 1 }));
    }, []);

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

// Filter bar component
function FilterBar({
    t, recordType, onRecordTypeChange, ticker, setTicker, strategyName, setStrategyName,
    dateRange, setDateRange, strategies, onFilter, onReset
}) {
    return (
        <div className="card" style={{ marginBottom: '1rem', padding: '1rem' }}>
            <Space wrap style={{ width: '100%', justifyContent: 'space-between' }}>
                <Segmented
                    options={[
                        {
                            label: (
                                <Space>
                                    <FundOutlined />
                                    {t('history.type_strategy')}
                                </Space>
                            ),
                            value: 'strategy'
                        },
                        {
                            label: (
                                <Space>
                                    <PieChartOutlined />
                                    {t('history.type_portfolio')}
                                </Space>
                            ),
                            value: 'portfolio'
                        }
                    ]}
                    value={recordType}
                    onChange={onRecordTypeChange}
                />

                {recordType === 'strategy' && (
                    <Space wrap>
                        <Input
                            placeholder={t('history.filter_ticker')}
                            value={ticker}
                            onChange={(e) => setTicker(e.target.value || null)}
                            style={{ width: 120 }}
                            allowClear
                        />
                        <Select
                            placeholder={t('history.filter_strategy')}
                            value={strategyName}
                            onChange={setStrategyName}
                            style={{ width: 200 }}
                            allowClear
                        >
                            {strategies.map(name => (
                                <Select.Option key={name} value={name}>{name}</Select.Option>
                            ))}
                        </Select>
                        <RangePicker
                            value={dateRange ? [dayjs(dateRange[0]), dayjs(dateRange[1])] : null}
                            onChange={(dates) => setDateRange(dates ? [dates[0].format('YYYY-MM-DD'), dates[1].format('YYYY-MM-DD')] : null)}
                            placeholder={[t('history.start_date'), t('history.end_date')]}
                        />
                        <Button
                            type="primary"
                            icon={<FilterOutlined />}
                            onClick={onFilter}
                        >
                            {t('common.filter')}
                        </Button>
                    </Space>
                )}

                <Button
                    icon={<ReloadOutlined />}
                    onClick={onReset}
                >
                    {t('common.reset')}
                </Button>
            </Space>
        </div>
    );
}

export default BacktestHistory;
