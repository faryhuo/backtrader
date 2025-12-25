import { useState, useEffect, useCallback } from 'react';
import { message } from 'antd';
import { api } from '../services/api';

/**
 * Custom hook for BacktestHistory page data management
 * 
 * Encapsulates all fetch, pagination, filtering, and sorting logic
 * for both strategy backtests and portfolio backtests.
 * 
 * @param {Object} options - Configuration options
 * @param {string} options.initialRecordType - Initial record type ('strategy' or 'portfolio')
 * @param {Function} options.t - Translation function
 * @returns {Object} Data and handlers for BacktestHistory page
 */
export function useBacktestHistory({ initialRecordType = 'strategy', t }) {
    // Record type toggle
    const [recordType, setRecordType] = useState(initialRecordType);

    // Data state
    const [backtests, setBacktests] = useState([]);
    const [portfolios, setPortfolios] = useState([]);
    const [loading, setLoading] = useState(false);

    // Filter state
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
            const queryParams = buildQueryParams(params, {
                ticker: params.ticker !== undefined ? params.ticker : ticker,
                strategyName: params.strategyName !== undefined ? params.strategyName : strategyName,
                dateRange: params.dateRange || dateRange,
                sortField: params.sortField || sortField,
                sortOrder: params.sortOrder || sortOrder,
                pageSize: params.pageSize || pagination.pageSize,
                current: params.current || pagination.current,
            });

            const result = await api.getBacktestHistory(queryParams);
            setBacktests(result.backtests || []);
            updatePagination(result.total || 0, params);
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
            updatePagination(result.count || 0, params);
        } catch (err) {
            message.error(t('history.fetch_error'));
            console.error(err);
        } finally {
            setLoading(false);
        }
    }, [sortField, sortOrder, pagination.pageSize, pagination.current, t]);

    // Helper: Build query params for backtest fetch
    const buildQueryParams = (params, config) => ({
        ticker: config.ticker,
        strategy_name: config.strategyName,
        start_date: config.dateRange?.[0],
        end_date: config.dateRange?.[1],
        sort_by: config.sortField,
        sort_order: config.sortOrder,
        limit: config.pageSize,
        offset: (config.current - 1) * config.pageSize
    });

    // Helper: Update pagination state
    const updatePagination = (total, params) => {
        setPagination(prev => ({
            ...prev,
            total,
            current: params.current || prev.current,
            pageSize: params.pageSize || prev.pageSize
        }));
    };

    // Handle table change (pagination + sorting)
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

    // Handle filter button click
    const handleFilter = useCallback(() => {
        setPagination(prev => ({ ...prev, current: 1 }));
        fetchBacktests({ current: 1 });
    }, [fetchBacktests]);

    // Handle reset button click
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

    // Handle record type change
    const handleRecordTypeChange = useCallback((value) => {
        setRecordType(value);
        setPagination(prev => ({ ...prev, current: 1 }));
    }, []);

    // Refetch current data
    const refetchCurrent = useCallback(() => {
        if (recordType === 'strategy') {
            fetchBacktests();
        } else {
            fetchPortfolios();
        }
    }, [recordType, fetchBacktests, fetchPortfolios]);

    return {
        // Data
        backtests,
        portfolios,
        loading,
        strategies,

        // Record type
        recordType,
        handleRecordTypeChange,

        // Filters
        ticker,
        setTicker,
        strategyName,
        setStrategyName,
        dateRange,
        setDateRange,

        // Pagination
        pagination,
        handleTableChange,

        // Actions
        handleFilter,
        handleReset,
        refetchCurrent,
        fetchBacktests,
        fetchPortfolios,
    };
}

export default useBacktestHistory;
