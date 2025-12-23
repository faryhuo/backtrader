import { useState, useCallback, useEffect } from 'react';
import { message } from 'antd';
import { reportApi } from '../services/reportApi';

// Report status constants
export const ReportStatus = {
    PENDING: 'pending',
    GENERATING: 'generating',
    COMPLETED: 'completed',
    FAILED: 'failed',
};

// Report type constants
export const ReportType = {
    BACKTEST: 'backtest',
    PORTFOLIO: 'portfolio',
    WALKFORWARD: 'walkforward',
    COMPARISON: 'comparison',
};

/**
 * Hook for managing reports with CRUD operations and filtering.
 * Includes auto-refresh polling for generating reports.
 *
 * @param {Object} options - Configuration options
 * @param {number} options.pollInterval - Polling interval in ms (default: 5000)
 * @param {boolean} options.autoRefresh - Enable auto-refresh (default: true)
 * @returns {Object} Reports state and handlers
 */
export function useReports({
    pollInterval = 5000,
    autoRefresh = true,
} = {}) {
    const [reports, setReports] = useState([]);
    const [total, setTotal] = useState(0);
    const [loading, setLoading] = useState(true);
    const [error, setError] = useState(null);

    const [filters, setFilters] = useState({
        report_type: '',
        status: '',
        limit: 20,
        offset: 0,
        sort_by: 'created_at',
        sort_order: 'desc',
    });

    // Fetch reports
    const fetchReports = useCallback(async () => {
        try {
            setLoading(true);
            const result = await reportApi.listReports({
                ...filters,
                report_type: filters.report_type || undefined,
                status: filters.status || undefined,
            });
            setReports(result.reports || []);
            setTotal(result.total || 0);
            setError(null);
        } catch (err) {
            setError(err.message);
        } finally {
            setLoading(false);
        }
    }, [filters]);

    // Auto-refresh effect
    useEffect(() => {
        fetchReports();
        if (autoRefresh) {
            const interval = setInterval(fetchReports, pollInterval);
            return () => clearInterval(interval);
        }
    }, [fetchReports, autoRefresh, pollInterval]);

    // Handle filter change
    const handleFilterChange = useCallback((key, value) => {
        setFilters(prev => ({
            ...prev,
            [key]: value,
            offset: 0, // Reset pagination
        }));
    }, []);

    // Handle pagination change
    const handlePaginationChange = useCallback((page, pageSize) => {
        setFilters(prev => ({
            ...prev,
            offset: (page - 1) * pageSize,
            limit: pageSize,
        }));
    }, []);

    // Download report
    const downloadReport = useCallback(async (reportId, t) => {
        try {
            await reportApi.downloadReport(reportId);
            message.success(t?.('reportCenter.downloadSuccess') || 'Report downloaded');
        } catch (err) {
            message.error(t?.('reportCenter.downloadError') || 'Failed to download report');
        }
    }, []);

    // Delete report
    const deleteReport = useCallback(async (reportId, t) => {
        try {
            await reportApi.deleteReport(reportId);
            message.success(t?.('reportCenter.deleteSuccess') || 'Report deleted');
            fetchReports();
            return true;
        } catch (err) {
            message.error(t?.('reportCenter.deleteError') || 'Failed to delete report');
            return false;
        }
    }, [fetchReports]);

    // Get current page number
    const currentPage = Math.floor(filters.offset / filters.limit) + 1;

    return {
        reports,
        total,
        loading,
        error,
        filters,
        currentPage,
        fetchReports,
        handleFilterChange,
        handlePaginationChange,
        downloadReport,
        deleteReport,
    };
}

export default useReports;
