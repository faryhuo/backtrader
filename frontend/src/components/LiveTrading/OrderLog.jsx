import React from 'react';
import { Table, Tag, Typography, Tooltip } from 'antd';
import { CheckCircleOutlined, ClockCircleOutlined, CloseCircleOutlined, SyncOutlined } from '@ant-design/icons';
import dayjs from 'dayjs';
import { useTranslation } from 'react-i18next';

const { Text } = Typography;

/**
 * Order Log Component
 * Displays order execution history with real-time updates
 */
const OrderLog = ({ orders, loading }) => {
  const { t } = useTranslation();

  const getStatusConfig = (status) => {
    const configs = {
      'created': { color: 'default', icon: <ClockCircleOutlined />, text: 'Created' },
      'submitted': { color: 'processing', icon: <SyncOutlined spin />, text: 'Submitted' },
      'accepted': { color: 'blue', icon: <SyncOutlined />, text: 'Accepted' },
      'partial': { color: 'orange', icon: <SyncOutlined spin />, text: 'Partial Fill' },
      'filled': { color: 'success', icon: <CheckCircleOutlined />, text: 'Filled' },
      'canceled': { color: 'default', icon: <CloseCircleOutlined />, text: 'Canceled' },
      'rejected': { color: 'error', icon: <CloseCircleOutlined />, text: 'Rejected' }
    };
    return configs[status] || { color: 'default', icon: null, text: status };
  };

  const columns = [
    {
      title: t('live.time'),
      dataIndex: 'created_at',
      key: 'created_at',
      width: 120,
      render: (time) => {
        const date = dayjs(time);
        return (
          <Tooltip title={date.format('YYYY-MM-DD HH:mm:ss')}>
            {date.format('HH:mm:ss')}
          </Tooltip>
        );
      }
    },
    {
      title: t('live.symbol'),
      dataIndex: 'symbol',
      key: 'symbol',
      render: (symbol) => <Text strong>{symbol}</Text>
    },
    {
      title: t('live.side'),
      dataIndex: 'side',
      key: 'side',
      render: (side) => (
        <Tag color={side === 'buy' ? 'green' : 'red'}>
          {side?.toUpperCase()}
        </Tag>
      )
    },
    {
      title: t('live.type'),
      dataIndex: 'type',
      key: 'type',
      render: (type) => type?.toUpperCase() || 'MARKET'
    },
    {
      title: t('live.size'),
      dataIndex: 'size',
      key: 'size',
      render: (size) => size?.toFixed(4) || '0'
    },
    {
      title: t('live.price'),
      dataIndex: 'price',
      key: 'price',
      render: (price) => price ? `$${price.toFixed(2)}` : 'Market'
    },
    {
      title: t('live.filled'),
      dataIndex: 'filled_size',
      key: 'filled_size',
      render: (filled, record) => {
        const fillPercent = record.size ? (filled / record.size * 100) : 0;
        return (
          <Tooltip title={`${fillPercent.toFixed(1)}% filled`}>
            {filled?.toFixed(4) || '0'} / {record.size?.toFixed(4) || '0'}
          </Tooltip>
        );
      }
    },
    {
      title: t('live.avg_fill_price'),
      dataIndex: 'filled_price',
      key: 'filled_price',
      render: (price) => price ? `$${price.toFixed(2)}` : '-'
    },
    {
      title: t('live.status'),
      dataIndex: 'status',
      key: 'status',
      render: (status) => {
        const config = getStatusConfig(status);
        return (
          <Tag color={config.color} icon={config.icon}>
            {config.text}
          </Tag>
        );
      }
    },
    {
      title: t('live.commission'),
      dataIndex: 'commission',
      key: 'commission',
      render: (commission) => commission ? `$${commission.toFixed(4)}` : '-'
    }
  ];

  return (
    <Table
      columns={columns}
      dataSource={orders}
      rowKey={(record) => record.order_id || record.created_at}
      loading={loading}
      pagination={{
        pageSize: 20,
        showSizeChanger: true,
        showTotal: (total) => `Total ${total}`
      }}
      locale={{
        emptyText: t('live.no_orders')
      }}
      size="small"
      scroll={{ x: 'max-content' }}
    />
  );
};

export default OrderLog;
