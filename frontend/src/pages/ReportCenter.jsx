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

import { useState, useEffect, useCallback } from 'react';
import { useNavigate } from 'react-router-dom';
import { useTranslation } from 'react-i18next';
import {
    Table,
    Button,
    Space,
    Tag,
    Modal,
    message,
    Select,
    Progress,
    Empty,
    Tooltip,
    Badge,
    Input,
    Slider,
    Typography,
    Divider,
    Spin,
    Alert,
} from 'antd';
import {
    DownloadOutlined,
    ShareAltOutlined,
    DeleteOutlined,
    EyeOutlined,
    ReloadOutlined,
    FileTextOutlined,
    LinkOutlined,
    CopyOutlined,
    StopOutlined,
    CheckOutlined,
} from '@ant-design/icons';

const { Text, Paragraph } = Typography;
import { reportApi } from '../services/reportApi';
import './ReportCenter.css';

const { Option } = Select;

// Report status constants
const ReportStatus = {
    PENDING: 'pending',
    GENERATING: 'generating',
    COMPLETED: 'completed',
    FAILED: 'failed',
};

const ReportType = {
    BACKTEST: 'backtest',
    PORTFOLIO: 'portfolio',
    WALKFORWARD: 'walkforward',
    COMPARISON: 'comparison',
};

function ReportCenter() {
    const { t } = useTranslation();
    const navigate = useNavigate();

    // State
    const [reports, setReports] = useState([]);
    const [total, setTotal] = useState(0);
    const [loading, setLoading] = useState(true);
    const [error, setError] = useState(null);
    const [selectedReport, setSelectedReport] = useState(null);
    const [viewModalVisible, setViewModalVisible] = useState(false);
    const [shareModalVisible, setShareModalVisible] = useState(false);

    // Share modal state
    const [shareLoading, setShareLoading] = useState(false);
    const [shareData, setShareData] = useState(null);
    const [expiresInHours, setExpiresInHours] = useState(168); // 7 days default
    const [copied, setCopied] = useState(false);
    const [revoking, setRevoking] = useState(false);

    // Filters
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
            message.error(t('reportCenter.fetchError', 'Failed to load reports'));
        } finally {
            setLoading(false);
        }
    }, [filters, t]);

    // Initial load
    useEffect(() => {
        fetchReports();
        const interval = setInterval(fetchReports, 5000); // Poll for updates
        return () => clearInterval(interval);
    }, [fetchReports]);

    // Handle filter change
    const handleFilterChange = (key, value) => {
        setFilters(prev => ({
            ...prev,
            [key]: value,
            offset: 0, // Reset pagination
        }));
    };

    // Handle view report
    const handleView = async (report) => {
        if (report.status !== ReportStatus.COMPLETED) {
            message.warning(t('reportCenter.notReady', 'Report is not ready yet'));
            return;
        }
        setSelectedReport(report);
        setViewModalVisible(true);
    };

    // Handle download
    const handleDownload = async (report) => {
        if (report.status !== ReportStatus.COMPLETED) {
            message.warning(t('reportCenter.notReady', 'Report is not ready yet'));
            return;
        }
        try {
            await reportApi.downloadReport(report.report_id);
            message.success(t('reportCenter.downloadSuccess', 'Report downloaded'));
        } catch (err) {
            message.error(t('reportCenter.downloadError', 'Failed to download report'));
        }
    };

    // Handle share
    const handleShare = (report) => {
        if (report.status !== ReportStatus.COMPLETED) {
            message.warning(t('reportCenter.notReady', 'Report is not ready yet'));
            return;
        }
        setSelectedReport(report);
        setShareData(null);
        setCopied(false);
        setExpiresInHours(168);
        setShareModalVisible(true);
    };

    // Generate share link
    const generateShareLink = async () => {
        if (!selectedReport) return;

        try {
            setShareLoading(true);
            const result = await reportApi.createShareLink(selectedReport.report_id, expiresInHours);
            const fullUrl = `${window.location.origin}${result.share_url}`;
            setShareData({
                ...result,
                full_url: fullUrl,
            });
            fetchReports(); // Refresh to update has_share_link status
            message.success(t('reportCenter.share.generateSuccess', 'Share link generated'));
        } catch (err) {
            console.error('Failed to generate share link:', err);
            message.error(t('reportCenter.share.generateError', 'Failed to generate share link'));
        } finally {
            setShareLoading(false);
        }
    };

    // Revoke share link
    const revokeShareLink = async () => {
        if (!selectedReport) return;

        try {
            setRevoking(true);
            await reportApi.revokeShareLink(selectedReport.report_id);
            setShareData(null);
            fetchReports(); // Refresh to update has_share_link status
            message.success(t('reportCenter.share.revokeSuccess', 'Share link revoked'));
        } catch (err) {
            console.error('Failed to revoke share link:', err);
            message.error(t('reportCenter.share.revokeError', 'Failed to revoke share link'));
        } finally {
            setRevoking(false);
        }
    };

    // Copy share link to clipboard
    const copyShareLink = async () => {
        if (!shareData?.full_url) return;

        try {
            await navigator.clipboard.writeText(shareData.full_url);
            setCopied(true);
            message.success(t('reportCenter.share.copied', 'Link copied to clipboard'));
            setTimeout(() => setCopied(false), 3000);
        } catch (err) {
            message.error(t('reportCenter.share.copyError', 'Failed to copy link'));
        }
    };

    // Close share modal
    const closeShareModal = () => {
        setShareModalVisible(false);
        setShareData(null);
        setSelectedReport(null);
        setCopied(false);
    };

    // Handle delete
    const handleDelete = async (report) => {
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
    };

    // Get status tag
    const getStatusTag = (status, progress) => {
        const statusConfig = {
            [ReportStatus.PENDING]: { color: 'default', text: t('reportCenter.status.pending', 'Pending') },
            [ReportStatus.GENERATING]: { color: 'processing', text: t('reportCenter.status.generating', 'Generating') },
            [ReportStatus.COMPLETED]: { color: 'success', text: t('reportCenter.status.completed', 'Completed') },
            [ReportStatus.FAILED]: { color: 'error', text: t('reportCenter.status.failed', 'Failed') },
        };

        const config = statusConfig[status] || statusConfig[ReportStatus.PENDING];

        if (status === ReportStatus.GENERATING && progress > 0) {
            return (
                <Space size={4}>
                    <Tag color={config.color}>{config.text}</Tag>
                    <Progress percent={progress} size="small" style={{ width: 100 }} />
                </Space>
            );
        }

        return <Tag color={config.color}>{config.text}</Tag>;
    };

    // Get report type tag
    const getReportTypeTag = (type) => {
        const typeConfig = {
            [ReportType.BACKTEST]: { color: 'blue', text: t('reportCenter.type.backtest', 'Backtest') },
            [ReportType.PORTFOLIO]: { color: 'purple', text: t('reportCenter.type.portfolio', 'Portfolio') },
            [ReportType.WALKFORWARD]: { color: 'orange', text: t('reportCenter.type.walkforward', 'Walk-Forward') },
            [ReportType.COMPARISON]: { color: 'cyan', text: t('reportCenter.type.comparison', 'Comparison') },
        };

        const config = typeConfig[type] || { color: 'default', text: type };
        return <Tag color={config.color}>{config.text}</Tag>;
    };

    // Table columns
    const columns = [
        {
            title: t('reportCenter.table.title', 'Title'),
            dataIndex: 'title',
            key: 'title',
            render: (text, record) => (
                <Space>
                    <FileTextOutlined />
                    <span>{text}</span>
                    {record.has_share_link && (
                        <Tooltip title={t('reportCenter.shared', 'Shared')}>
                            <LinkOutlined style={{ color: '#22d3ee' }} />
                        </Tooltip>
                    )}
                </Space>
            ),
        },
        {
            title: t('reportCenter.table.type', 'Type'),
            dataIndex: 'report_type',
            key: 'report_type',
            width: 120,
            render: (type) => getReportTypeTag(type),
        },
        {
            title: t('reportCenter.table.status', 'Status'),
            dataIndex: 'status',
            key: 'status',
            width: 200,
            render: (status, record) => getStatusTag(status, record.progress),
        },
        {
            title: t('reportCenter.table.sources', 'Sources'),
            dataIndex: 'source_ids',
            key: 'source_ids',
            width: 100,
            render: (sources) => (
                <Badge count={sources?.length || 0} style={{ backgroundColor: '#52c41a' }} />
            ),
        },
        {
            title: t('reportCenter.table.created', 'Created'),
            dataIndex: 'created_at',
            key: 'created_at',
            width: 180,
            render: (date) => new Date(date).toLocaleString(),
        },
        {
            title: t('reportCenter.table.actions', 'Actions'),
            key: 'actions',
            width: 180,
            render: (_, record) => {
                const isCompleted = record.status === ReportStatus.COMPLETED;

                return (
                    <Space size={4} className="report-actions">
                        <Tooltip title={t('reportCenter.actions.view', 'View')}>
                            <Button
                                type="text"
                                icon={<EyeOutlined />}
                                disabled={!isCompleted}
                                onClick={() => handleView(record)}
                                className="action-btn"
                            />
                        </Tooltip>
                        <Tooltip title={t('reportCenter.actions.download', 'Download')}>
                            <Button
                                type="text"
                                icon={<DownloadOutlined />}
                                disabled={!isCompleted}
                                onClick={() => handleDownload(record)}
                                className="action-btn"
                            />
                        </Tooltip>
                        <Tooltip title={t('reportCenter.actions.share', 'Share')}>
                            <Button
                                type="text"
                                icon={<ShareAltOutlined />}
                                disabled={!isCompleted}
                                onClick={() => handleShare(record)}
                                className="action-btn"
                            />
                        </Tooltip>
                        <Tooltip title={t('reportCenter.actions.delete', 'Delete')}>
                            <Button
                                type="text"
                                danger
                                icon={<DeleteOutlined />}
                                onClick={() => handleDelete(record)}
                                className="action-btn action-btn-danger"
                            />
                        </Tooltip>
                    </Space>
                );
            },
        },
    ];

    return (
        <div className="report-center">
            <div className="report-center-header">
                <h1>{t('reportCenter.title', 'Report Center')}</h1>
                <Button
                    icon={<ReloadOutlined />}
                    onClick={fetchReports}
                    loading={loading}
                >
                    {t('common.refresh', 'Refresh')}
                </Button>
            </div>

            <div className="report-center-filters">
                <Space size="large">
                    <Space>
                        <span>{t('reportCenter.filter.type', 'Type:')}</span>
                        <Select
                            style={{ width: 150 }}
                            value={filters.report_type}
                            onChange={(value) => handleFilterChange('report_type', value)}
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
                            onChange={(value) => handleFilterChange('status', value)}
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
                    current: Math.floor(filters.offset / filters.limit) + 1,
                    pageSize: filters.limit,
                    total: total,
                    onChange: (page, pageSize) => {
                        setFilters(prev => ({
                            ...prev,
                            offset: (page - 1) * pageSize,
                            limit: pageSize,
                        }));
                    },
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

            {/* View Modal - Placeholder for now */}
            <Modal
                title={selectedReport?.title}
                open={viewModalVisible}
                onCancel={() => setViewModalVisible(false)}
                width="90%"
                footer={[
                    <Button key="close" onClick={() => setViewModalVisible(false)}>
                        {t('common.close', 'Close')}
                    </Button>,
                    <Button key="download" icon={<DownloadOutlined />} onClick={() => handleDownload(selectedReport)}>
                        {t('reportCenter.actions.download', 'Download')}
                    </Button>,
                ]}
            >
                <p>{t('reportCenter.viewPlaceholder', 'Report viewer coming soon. Use download to view the full report.')}</p>
            </Modal>

            {/* Share Modal - Full Implementation */}
            <Modal
                title={
                    <Space>
                        <ShareAltOutlined />
                        {t('reportCenter.shareTitle', 'Share Report')}
                    </Space>
                }
                open={shareModalVisible}
                onCancel={closeShareModal}
                footer={null}
                width={520}
                destroyOnClose
            >
                <div className="share-modal-content">
                    {/* Report title */}
                    <div className="share-report-info">
                        <Text strong>{selectedReport?.title}</Text>
                    </div>

                    <Divider />

                    {/* Share link exists - show link and options */}
                    {shareData ? (
                        <div className="share-link-section">
                            <Alert
                                type="success"
                                showIcon
                                icon={<LinkOutlined />}
                                message={t('reportCenter.share.linkActive', 'Share link is active')}
                                description={
                                    <Text type="secondary">
                                        {t('reportCenter.share.expiresAt', 'Expires')}: {new Date(shareData.expires_at).toLocaleString()}
                                    </Text>
                                }
                                style={{ marginBottom: 16 }}
                            />

                            <Input.Group compact style={{ display: 'flex', marginBottom: 16 }}>
                                <Input
                                    value={shareData.full_url}
                                    readOnly
                                    style={{ flex: 1 }}
                                />
                                <Tooltip title={copied ? t('reportCenter.share.copied', 'Copied!') : t('reportCenter.share.copy', 'Copy link')}>
                                    <Button
                                        icon={copied ? <CheckOutlined /> : <CopyOutlined />}
                                        onClick={copyShareLink}
                                        type={copied ? 'primary' : 'default'}
                                    />
                                </Tooltip>
                            </Input.Group>

                            <Button
                                danger
                                icon={<StopOutlined />}
                                onClick={revokeShareLink}
                                loading={revoking}
                                block
                            >
                                {t('reportCenter.share.revoke', 'Revoke Share Link')}
                            </Button>
                        </div>
                    ) : (
                        <div className="share-generate-section">
                            {/* Expiration selection */}
                            <div className="expiration-section">
                                <Text strong style={{ display: 'block', marginBottom: 8 }}>
                                    {t('reportCenter.share.expirationLabel', 'Link expiration')}
                                </Text>
                                <div className="expiration-slider">
                                    <Slider
                                        min={24}
                                        max={720}
                                        step={24}
                                        value={expiresInHours}
                                        onChange={setExpiresInHours}
                                        marks={{
                                            24: '1d',
                                            168: '7d',
                                            336: '14d',
                                            720: '30d',
                                        }}
                                        tooltip={{
                                            formatter: (value) => `${Math.round(value / 24)} ${t('reportCenter.share.days', 'days')}`
                                        }}
                                    />
                                </div>
                                <Text type="secondary" style={{ display: 'block', textAlign: 'center', marginTop: 8 }}>
                                    {t('reportCenter.share.expiresIn', 'Link will expire in')} {Math.round(expiresInHours / 24)} {t('reportCenter.share.days', 'days')}
                                </Text>
                            </div>

                            <Divider />

                            {/* Generate button */}
                            <Button
                                type="primary"
                                icon={<LinkOutlined />}
                                onClick={generateShareLink}
                                loading={shareLoading}
                                block
                                size="large"
                            >
                                {t('reportCenter.share.generate', 'Generate Share Link')}
                            </Button>

                            <Paragraph type="secondary" style={{ marginTop: 16, textAlign: 'center', marginBottom: 0 }}>
                                {t('reportCenter.share.description', 'Anyone with this link can view the report without signing in.')}
                            </Paragraph>
                        </div>
                    )}
                </div>
            </Modal>
        </div>
    );
}

export default ReportCenter;
