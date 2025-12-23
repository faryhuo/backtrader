import { Tag, Space, Button, Tooltip, Progress, Badge } from 'antd';
import {
    DownloadOutlined,
    ShareAltOutlined,
    DeleteOutlined,
    EyeOutlined,
    FileTextOutlined,
    LinkOutlined,
} from '@ant-design/icons';

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
 * Get status tag element for report status.
 *
 * @param {string} status - Report status
 * @param {number} progress - Progress percentage (for generating status)
 * @param {function} t - Translation function
 * @returns {JSX.Element} Status tag element
 */
export function getReportStatusTag(status, progress, t) {
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
}

/**
 * Get report type tag element.
 *
 * @param {string} type - Report type
 * @param {function} t - Translation function
 * @returns {JSX.Element} Type tag element
 */
export function getReportTypeTag(type, t) {
    const typeConfig = {
        [ReportType.BACKTEST]: { color: 'blue', text: t('reportCenter.type.backtest', 'Backtest') },
        [ReportType.PORTFOLIO]: { color: 'purple', text: t('reportCenter.type.portfolio', 'Portfolio') },
        [ReportType.WALKFORWARD]: { color: 'orange', text: t('reportCenter.type.walkforward', 'Walk-Forward') },
        [ReportType.COMPARISON]: { color: 'cyan', text: t('reportCenter.type.comparison', 'Comparison') },
    };

    const config = typeConfig[type] || { color: 'default', text: type };
    return <Tag color={config.color}>{config.text}</Tag>;
}

/**
 * Generate column definitions for reports table.
 *
 * @param {Object} options - Column configuration
 * @param {function} options.t - Translation function
 * @param {function} options.onView - View handler
 * @param {function} options.onDownload - Download handler
 * @param {function} options.onShare - Share handler
 * @param {function} options.onDelete - Delete handler
 * @returns {Array} Column definitions
 */
export function getReportColumns({ t, onView, onDownload, onShare, onDelete }) {
    return [
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
            render: (type) => getReportTypeTag(type, t),
        },
        {
            title: t('reportCenter.table.status', 'Status'),
            dataIndex: 'status',
            key: 'status',
            width: 200,
            render: (status, record) => getReportStatusTag(status, record.progress, t),
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
                                onClick={() => onView(record)}
                                className="action-btn"
                            />
                        </Tooltip>
                        <Tooltip title={t('reportCenter.actions.download', 'Download')}>
                            <Button
                                type="text"
                                icon={<DownloadOutlined />}
                                disabled={!isCompleted}
                                onClick={() => onDownload(record)}
                                className="action-btn"
                            />
                        </Tooltip>
                        <Tooltip title={t('reportCenter.actions.share', 'Share')}>
                            <Button
                                type="text"
                                icon={<ShareAltOutlined />}
                                disabled={!isCompleted}
                                onClick={() => onShare(record)}
                                className="action-btn"
                            />
                        </Tooltip>
                        <Tooltip title={t('reportCenter.actions.delete', 'Delete')}>
                            <Button
                                type="text"
                                danger
                                icon={<DeleteOutlined />}
                                onClick={() => onDelete(record)}
                                className="action-btn action-btn-danger"
                            />
                        </Tooltip>
                    </Space>
                );
            },
        },
    ];
}
