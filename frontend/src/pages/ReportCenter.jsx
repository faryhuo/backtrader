/**
 * ReportCenter Page - Report management.
 *
 * Features:
 * - List generated reports with filters
 * - View, download, and share reports
 * - Manage share links
 *
 * Note: Report generation is integrated into backtest/portfolio/walkforward detail modals
 */

import { useState, useCallback } from 'react';
import { useTranslation } from 'react-i18next';
import { Modal, message } from 'antd';
import {
    DownloadOutlined,
    EyeOutlined,
    ShareAltOutlined,
    DeleteOutlined,
} from '@ant-design/icons';

import { reportApi } from '../services/reportApi';
import { useReports, ReportStatus, ReportType } from '../hooks/useReports';
import { ShareReportModal } from '../components/ReportCenter';
import './ReportCenter.css';

// Helper to get report type label
function getReportTypeLabel(type, t) {
    const labels = {
        [ReportType.BACKTEST]: t('reportCenter.type.backtest', 'Backtest'),
        [ReportType.PORTFOLIO]: t('reportCenter.type.portfolio', 'Portfolio'),
        [ReportType.WALKFORWARD]: t('reportCenter.type.walkforward', 'Walk-Forward'),
        [ReportType.COMPARISON]: t('reportCenter.type.comparison', 'Comparison'),
    };
    return labels[type] || type;
}

// Helper to get report status label
function getReportStatusLabel(status, t) {
    const labels = {
        [ReportStatus.PENDING]: t('reportCenter.status.pending', 'Pending'),
        [ReportStatus.GENERATING]: t('reportCenter.status.generating', 'Generating'),
        [ReportStatus.COMPLETED]: t('reportCenter.status.completed', 'Completed'),
        [ReportStatus.FAILED]: t('reportCenter.status.failed', 'Failed'),
    };
    return labels[status] || status;
}

// Format date
const formatDate = (isoString) => {
    if (!isoString) return '-';
    return new Date(isoString).toLocaleString();
};

function ReportCenter() {
    const { t } = useTranslation();

    // Use custom hook for reports management
    const {
        reports,
        total,
        loading,
        error,
        filters,
        fetchReports,
        handleFilterChange,
        downloadReport,
    } = useReports();

    // Modal state
    const [selectedReport, setSelectedReport] = useState(null);
    const [viewModalVisible, setViewModalVisible] = useState(false);
    const [shareModalVisible, setShareModalVisible] = useState(false);

    // Handle view report
    const handleView = useCallback((report) => {
        if (report.status !== ReportStatus.COMPLETED) {
            message.warning(t('reportCenter.notReady', 'Report is not ready yet'));
            return;
        }
        setSelectedReport(report);
        setViewModalVisible(true);
    }, [t]);

    // Handle download
    const handleDownload = useCallback(async (report) => {
        if (report.status !== ReportStatus.COMPLETED) {
            message.warning(t('reportCenter.notReady', 'Report is not ready yet'));
            return;
        }
        await downloadReport(report.report_id, t);
    }, [downloadReport, t]);

    // Handle share
    const handleShare = useCallback((report) => {
        if (report.status !== ReportStatus.COMPLETED) {
            message.warning(t('reportCenter.notReady', 'Report is not ready yet'));
            return;
        }
        setSelectedReport(report);
        setShareModalVisible(true);
    }, [t]);

    // Handle delete
    const handleDelete = useCallback((report) => {
        Modal.confirm({
            title: t('reportCenter.deleteConfirm', 'Delete Report'),
            content: t('reportCenter.deleteMessage', `Are you sure you want to delete "${report.title}"?`),
            okText: t('common.delete', 'Delete'),
            okType: 'danger',
            cancelText: t('common.cancel', 'Cancel'),
            onOk: async () => {
                try {
                    await reportApi.deleteReport(report.report_id);
                    message.success(t('reportCenter.deleteSuccess', 'Report deleted'));
                    fetchReports();
                } catch (err) {
                    console.error('Failed to delete report:', err);
                    message.error(t('reportCenter.deleteError', 'Failed to delete report'));
                }
            },
        });
    }, [t, fetchReports]);

    // Close modals
    const closeViewModal = useCallback(() => {
        setViewModalVisible(false);
    }, []);

    const closeShareModal = useCallback(() => {
        setShareModalVisible(false);
        setSelectedReport(null);
    }, []);

    // Render table content - extracted to avoid nested ternary
    const renderTableContent = useCallback(() => {
        if (loading) {
            return (
                <div className="report-loading">
                    {t('common.loading', 'Loading...')}
                </div>
            );
        }

        if (reports.length === 0) {
            return (
                <div className="report-empty">
                    <div className="report-empty-icon">📄</div>
                    <h3>{t('reportCenter.noReports', 'No Reports')}</h3>
                    <p>{t('reportCenter.emptyDesc', 'Generate reports from backtest/portfolio/walk-forward result pages.')}</p>
                </div>
            );
        }

        return (
            <table className="report-table">
                <thead>
                    <tr>
                        <th>{t('reportCenter.table.title', 'Title')}</th>
                        <th>{t('reportCenter.table.type', 'Type')}</th>
                        <th>{t('reportCenter.table.status', 'Status')}</th>
                        <th>{t('reportCenter.table.sources', 'Sources')}</th>
                        <th>{t('reportCenter.table.created', 'Created')}</th>
                        <th>{t('reportCenter.table.actions', 'Actions')}</th>
                    </tr>
                </thead>
                <tbody>
                    {reports.map(report => (
                        <tr key={report.report_id}>
                            <td>
                                <div className="report-title">
                                    {report.title || 'Unnamed Report'}
                                    {report.has_share_link && (
                                        <span className="share-indicator" title={t('reportCenter.shared', 'Shared')}>🔗</span>
                                    )}
                                </div>
                                <div className="report-id">{report.report_id.substring(0, 8)}...</div>
                            </td>
                            <td>
                                <span className={`report-type-badge ${report.report_type}`}>
                                    {getReportTypeLabel(report.report_type, t)}
                                </span>
                            </td>
                            <td>
                                <span className={`report-status-badge ${report.status}`}>
                                    <span className={`status-dot ${report.status}`} />
                                    {getReportStatusLabel(report.status, t)}
                                </span>
                                {report.status === ReportStatus.GENERATING && report.progress > 0 && (
                                    <div className="report-progress">
                                        <div className="progress-bar">
                                            <div
                                                className="progress-fill"
                                                style={{ width: `${report.progress || 0}%` }}
                                            />
                                        </div>
                                        <span className="progress-text">{report.progress}%</span>
                                    </div>
                                )}
                                {report.error_message && (
                                    <div className="report-error-message" title={report.error_message}>
                                        {report.error_message}
                                    </div>
                                )}
                            </td>
                            <td className="report-sources">
                                {report.source_ids?.length || 0}
                            </td>
                            <td>
                                {formatDate(report.created_at)}
                            </td>
                            <td>
                                <div className="report-actions">
                                    {/* View button */}
                                    <button
                                        className="report-action-btn view"
                                        onClick={() => handleView(report)}
                                        disabled={report.status !== ReportStatus.COMPLETED}
                                        title={t('reportCenter.actions.view', 'View')}
                                    >
                                        <EyeOutlined />
                                    </button>

                                    {/* Download button */}
                                    <button
                                        className="report-action-btn download"
                                        onClick={() => handleDownload(report)}
                                        disabled={report.status !== ReportStatus.COMPLETED}
                                        title={t('reportCenter.actions.download', 'Download')}
                                    >
                                        <DownloadOutlined />
                                    </button>

                                    {/* Share button */}
                                    <button
                                        className="report-action-btn share"
                                        onClick={() => handleShare(report)}
                                        disabled={report.status !== ReportStatus.COMPLETED}
                                        title={t('reportCenter.actions.share', 'Share')}
                                    >
                                        <ShareAltOutlined />
                                    </button>

                                    {/* Delete button */}
                                    <button
                                        className="report-action-btn delete"
                                        onClick={() => handleDelete(report)}
                                        title={t('reportCenter.actions.delete', 'Delete')}
                                    >
                                        <DeleteOutlined />
                                    </button>
                                </div>
                            </td>
                        </tr>
                    ))}
                </tbody>
            </table>
        );
    }, [loading, reports, t, handleView, handleDownload, handleShare, handleDelete]);

    return (
        <div className="report-center">
            {/* Header */}
            <div className="report-center-header">
                <h1>{t('reportCenter.title', 'Report Center')}</h1>

                <div className="report-stats">
                    <div className="report-stat">
                        <span className="stat-label">{t('reportCenter.pending', 'Pending')}</span>
                        <span className="stat-value pending">
                            {reports.filter(r => r.status === ReportStatus.PENDING || r.status === ReportStatus.GENERATING).length}
                        </span>
                    </div>
                    <div className="report-stat">
                        <span className="stat-label">{t('reportCenter.failed', 'Failed')}</span>
                        <span className="stat-value failed">
                            {reports.filter(r => r.status === ReportStatus.FAILED).length}
                        </span>
                    </div>
                    <div className="report-stat">
                        <span className="stat-label">{t('reportCenter.totalReports', 'Total')}</span>
                        <span className="stat-value">{total || 0}</span>
                    </div>
                    <button className="refresh-btn" onClick={fetchReports} disabled={loading}>
                        {loading ? t('common.loading', 'Loading...') : t('common.refresh', 'Refresh')}
                    </button>
                </div>
            </div>

            {/* Filters */}
            <div className="report-filters">
                <div className="report-filter">
                    <label>{t('reportCenter.filter.type', 'Type')}</label>
                    <select
                        value={filters.report_type}
                        onChange={(e) => handleFilterChange('report_type', e.target.value)}
                    >
                        <option value="">{t('common.all', 'All Types')}</option>
                        <option value={ReportType.BACKTEST}>{getReportTypeLabel(ReportType.BACKTEST, t)}</option>
                        <option value={ReportType.PORTFOLIO}>{getReportTypeLabel(ReportType.PORTFOLIO, t)}</option>
                        <option value={ReportType.WALKFORWARD}>{getReportTypeLabel(ReportType.WALKFORWARD, t)}</option>
                        <option value={ReportType.COMPARISON}>{getReportTypeLabel(ReportType.COMPARISON, t)}</option>
                    </select>
                </div>

                <div className="report-filter">
                    <label>{t('reportCenter.filter.status', 'Status')}</label>
                    <select
                        value={filters.status}
                        onChange={(e) => handleFilterChange('status', e.target.value)}
                    >
                        <option value="">{t('common.all', 'All Status')}</option>
                        <option value={ReportStatus.PENDING}>{getReportStatusLabel(ReportStatus.PENDING, t)}</option>
                        <option value={ReportStatus.GENERATING}>{getReportStatusLabel(ReportStatus.GENERATING, t)}</option>
                        <option value={ReportStatus.COMPLETED}>{getReportStatusLabel(ReportStatus.COMPLETED, t)}</option>
                        <option value={ReportStatus.FAILED}>{getReportStatusLabel(ReportStatus.FAILED, t)}</option>
                    </select>
                </div>
            </div>

            {/* Error */}
            {error && (
                <div className="report-error" style={{ color: 'red', marginBottom: '1rem' }}>
                    {error}
                </div>
            )}

            {/* Report Table */}
            <div className="report-table-container">
                {renderTableContent()}
            </div>

            {/* Total count */}
            {!loading && reports.length > 0 && (
                <div style={{ marginTop: '1rem', color: 'var(--text-secondary)', fontSize: '0.875rem' }}>
                    {t('reportCenter.showingReports', 'Showing {{count}} of {{total}} reports', {
                        count: reports.length,
                        total: total,
                    })}
                </div>
            )}

            {/* View Modal */}
            <Modal
                title={selectedReport?.title}
                open={viewModalVisible}
                onCancel={closeViewModal}
                width="90%"
                footer={[
                    <button key="close" className="modal-btn secondary" onClick={closeViewModal}>
                        {t('common.close', 'Close')}
                    </button>,
                    <button key="download" className="modal-btn primary" onClick={() => handleDownload(selectedReport)}>
                        <DownloadOutlined /> {t('reportCenter.actions.download', 'Download')}
                    </button>,
                ]}
            >
                <p>{t('reportCenter.viewPlaceholder', 'Report viewer coming soon. Use download to view the full report.')}</p>
            </Modal>

            {/* Share Modal */}
            <ShareReportModal
                visible={shareModalVisible}
                report={selectedReport}
                onClose={closeShareModal}
                onShareUpdate={fetchReports}
            />
        </div>
    );
}

export default ReportCenter;
