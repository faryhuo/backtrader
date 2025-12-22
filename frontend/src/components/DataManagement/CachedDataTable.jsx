/**
 * Cached Data Table Component
 * Displays a table of cached tickers with management actions
 */
import { Card, Table, Button, Tag, Popconfirm } from 'antd';
import { DatabaseOutlined, DeleteOutlined, ReloadOutlined } from '@ant-design/icons';
import { useTranslation } from 'react-i18next';
import dayjs from 'dayjs';

function CachedDataTable({ tickers, loading, onRefresh, onDelete }) {
    const { t } = useTranslation();

    const columns = [
        {
            title: t('datamanagement.cached_data.ticker'),
            dataIndex: 'ticker',
            key: 'ticker',
            render: (text) => <Tag color="blue">{text}</Tag>
        },
        {
            title: t('datamanagement.cached_data.records'),
            dataIndex: 'record_count',
            key: 'record_count',
            render: (val) => val?.toLocaleString()
        },
        {
            title: t('datamanagement.cached_data.date_range'),
            key: 'date_range',
            render: (_, record) => (
                <span>
                    {record.date_range?.start} ~ {record.date_range?.end}
                </span>
            )
        },
        {
            title: t('datamanagement.cached_data.last_updated'),
            dataIndex: 'last_updated',
            key: 'last_updated',
            render: (val) => val ? dayjs(val).format('YYYY-MM-DD HH:mm') : '-'
        },
        {
            title: t('datamanagement.cached_data.actions'),
            key: 'actions',
            render: (_, record) => (
                <Popconfirm
                    title={t('datamanagement.cached_data.delete_confirm', { ticker: record.ticker })}
                    onConfirm={() => onDelete(record.ticker)}
                    okText={t('common.confirm')}
                    cancelText={t('common.cancel')}
                >
                    <Button
                        danger
                        size="small"
                        icon={<DeleteOutlined />}
                    >
                        {t('datamanagement.cached_data.delete')}
                    </Button>
                </Popconfirm>
            )
        }
    ];

    return (
        <Card
            title={
                <span>
                    <DatabaseOutlined className="card-icon" />
                    {t('datamanagement.cached_data.title')}
                </span>
            }
            extra={
                <Button
                    icon={<ReloadOutlined />}
                    onClick={onRefresh}
                    loading={loading}
                >
                    {t('datamanagement.cached_data.refresh')}
                </Button>
            }
            className="feature-card cached-data-card"
            style={{ marginTop: 16 }}
        >
            <Table
                dataSource={tickers || []}
                columns={columns}
                rowKey="ticker"
                size="small"
                pagination={{ pageSize: 10 }}
                locale={{
                    emptyText: t('datamanagement.cached_data.empty')
                }}
            />
        </Card>
    );
}

export default CachedDataTable;
