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

import { useState, useCallback, useMemo } from 'react';
import { useTranslation } from 'react-i18next';
import {
    Table,
    Button,
    Space,
    Modal,
    message,
    Select,
    Empty,
} from 'antd';
import {
    DownloadOutlined,
    ReloadOutlined,
} from '@ant-design/icons';

import { reportApi } from '../services/reportApi';
import { useReports, ReportStatus, ReportType } from '../hooks/useReports';
import { getReportColumns } from '../utils/tableColumns';
import { ShareReportModal } from '../components/ReportCenter';
import './ReportCenter.css';

const { Option } = Select;

function ReportCenter() {
    const { t } = useTranslation();

    // Use custom hook for reports management
    const {
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

    // Get table columns
    const columns = useMemo(() => getReportColumns({
        t,
        onView: handleView,
        onDownload: handleDownload,
        onShare: handleShare,
        onDelete: handleDelete,
    }), [t, handleView, handleDownload, handleShare, handleDelete]);

    return (
        <div className="report-center">
            <ReportCenterHeader t={t} loading={loading} onRefresh={fetchReports} />

            <ReportFilters
                t={t}
                filters={filters}
                onFilterChange={handleFilterChange}
            />

            {error && (
                <div className="report-center-error">
                    <p>{error}</p>
                </div>
            )}

            <Table
                columns={columns}
                dataSource={reports}
                loading={loading}
                rowKey="report_id"
                pagination={{
                    current: currentPage,
                    pageSize: filters.limit,
                    total: total,
                    onChange: handlePaginationChange,
                    showSizeChanger: true,
                    showTotal: (total) => t('reportCenter.total', `Total ${total} reports`, { total }),
                }}
                locale={{
                    emptyText: (
                        <Empty
                            description={t('reportCenter.emptyDesc', 'No reports yet. Generate reports from backtest/portfolio/walk-forward result pages.')}
                            image={Empty.PRESENTED_IMAGE_SIMPLE}
                        />
                    ),
                }}
            />

            {/* View Modal */}
            <Modal
                title={selectedReport?.title}
                open={viewModalVisible}
                onCancel={closeViewModal}
                width="90%"
                footer={[
                    <Button key="close" onClick={closeViewModal}>
                        {t('common.close', 'Close')}
                    </Button>,
                    <Button key="download" icon={<DownloadOutlined />} onClick={() => handleDownload(selectedReport)}>
                        {t('reportCenter.actions.download', 'Download')}
                    </Button>,
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

// Header component
function ReportCenterHeader({ t, loading, onRefresh }) {
    return (
        <div className="report-center-header">
            <h1>{t('reportCenter.title', 'Report Center')}</h1>
            <Button
                icon={<ReloadOutlined />}
                onClick={onRefresh}
                loading={loading}
            >
                {t('common.refresh', 'Refresh')}
            </Button>
        </div>
    );
}

// Filters component
function ReportFilters({ t, filters, onFilterChange }) {
    return (
        <div className="report-center-filters">
            <Space size="large">
                <Space>
                    <span>{t('reportCenter.filter.type', 'Type:')}</span>
                    <Select
                        style={{ width: 150 }}
                        value={filters.report_type}
                        onChange={(value) => onFilterChange('report_type', value)}
                        allowClear
                        placeholder={t('common.all', 'All')}
                    >
                        <Option value="">{t('common.all', 'All')}</Option>
                        <Option value={ReportType.BACKTEST}>{t('reportCenter.type.backtest', 'Backtest')}</Option>
                        <Option value={ReportType.PORTFOLIO}>{t('reportCenter.type.portfolio', 'Portfolio')}</Option>
                        <Option value={ReportType.WALKFORWARD}>{t('reportCenter.type.walkforward', 'Walk-Forward')}</Option>
                        <Option value={ReportType.COMPARISON}>{t('reportCenter.type.comparison', 'Comparison')}</Option>
                    </Select>
                </Space>
                <Space>
                    <span>{t('reportCenter.filter.status', 'Status:')}</span>
                    <Select
                        style={{ width: 150 }}
                        value={filters.status}
                        onChange={(value) => onFilterChange('status', value)}
                        allowClear
                        placeholder={t('common.all', 'All')}
                    >
                        <Option value="">{t('common.all', 'All')}</Option>
                        <Option value={ReportStatus.PENDING}>{t('reportCenter.status.pending', 'Pending')}</Option>
                        <Option value={ReportStatus.GENERATING}>{t('reportCenter.status.generating', 'Generating')}</Option>
                        <Option value={ReportStatus.COMPLETED}>{t('reportCenter.status.completed', 'Completed')}</Option>
                        <Option value={ReportStatus.FAILED}>{t('reportCenter.status.failed', 'Failed')}</Option>
                    </Select>
                </Space>
            </Space>
        </div>
    );
}

export default ReportCenter;
