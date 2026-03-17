import { useState } from 'react';
import { Table, Tag, Typography, Tooltip, Button, Popconfirm, Segmented } from 'antd';
import { CheckCircleOutlined, ClockCircleOutlined, CloseCircleOutlined, SyncOutlined, DeleteOutlined } from '@ant-design/icons';
import dayjs from 'dayjs';
import { useTranslation } from 'react-i18next';

const { Text } = Typography;

const STATUS_CONFIG = {
  submitted: { color: 'blue', icon: <ClockCircleOutlined /> },
  accepted: { color: 'cyan', icon: <SyncOutlined spin /> },
  partial: { color: 'orange', icon: <SyncOutlined /> },
  filled: { color: 'green', icon: <CheckCircleOutlined /> },
  cancelled: { color: 'default', icon: <CloseCircleOutlined /> },
  canceled: { color: 'default', icon: <CloseCircleOutlined /> },
  rejected: { color: 'red', icon: <CloseCircleOutlined /> },
  open: { color: 'blue', icon: <ClockCircleOutlined /> },
};

/**
 * Order log with tabs (Open / Filled / All) and cancel button
 */
const OrderLog = ({ orders, onCancelOrder }) => {
  const { t } = useTranslation();
  const [filter, setFilter] = useState('all');

  const filtered = orders.filter(o => {
    if (filter === 'open') return ['submitted', 'accepted', 'partial', 'open'].includes(o.status);
    if (filter === 'filled') return o.status === 'filled';
    return true;
  });

  const columns = [
    {
      title: t('live.orders.time', 'Time'),
      dataIndex: 'created_at',
      key: 'time',
      width: 80,
      render: (v) => v ? (
        <Tooltip title={dayjs(v).format('YYYY-MM-DD HH:mm:ss')}>
          <Text type="secondary">{dayjs(v).format('HH:mm:ss')}</Text>
        </Tooltip>
      ) : '-',
    },
    {
      title: t('live.orders.side', 'Side'),
      dataIndex: 'side',
      key: 'side',
      width: 60,
      render: (side) => (
        <Tag color={side === 'buy' ? 'green' : 'red'} style={{ margin: 0 }}>
          {(side || '').toUpperCase()}
        </Tag>
      ),
    },
    {
      title: t('live.orders.size', 'Size'),
      dataIndex: 'size',
      key: 'size',
      width: 80,
      render: (v) => v ? Math.abs(v) : '-',
    },
    {
      title: t('live.orders.price', 'Price'),
      key: 'price',
      width: 90,
      render: (_, record) => {
        const price = record.filled_price || record.price;
        return price ? `$${Number(price).toFixed(2)}` : 'Market';
      },
    },
    {
      title: t('live.orders.status', 'Status'),
      dataIndex: 'status',
      key: 'status',
      width: 90,
      render: (status) => {
        const cfg = STATUS_CONFIG[status] || { color: 'default', icon: null };
        return (
          <Tag color={cfg.color} icon={cfg.icon} style={{ margin: 0 }}>
            {(status || '').toUpperCase()}
          </Tag>
        );
      },
    },
    {
      title: '',
      key: 'action',
      width: 40,
      render: (_, record) => {
        const isOpen = ['submitted', 'accepted', 'partial', 'open'].includes(record.status);
        if (!isOpen || !onCancelOrder) return null;
        return (
          <Popconfirm
            title={t('live.orders.confirm_cancel', 'Cancel this order?')}
            onConfirm={() => onCancelOrder(record.order_id || record.ccxt_order_id)}
            okText={t('common.yes', 'Yes')}
            cancelText={t('common.no', 'No')}
          >
            <Button type="text" danger size="small" icon={<DeleteOutlined />} />
          </Popconfirm>
        );
      },
    },
  ];

  return (
    <div>
      <div style={{ padding: '8px 16px' }}>
        <Segmented
          value={filter}
          onChange={setFilter}
          options={[
            { label: t('live.orders.tab_all', 'All'), value: 'all' },
            { label: t('live.orders.tab_open', 'Open'), value: 'open' },
            { label: t('live.orders.tab_filled', 'Filled'), value: 'filled' },
          ]}
          size="small"
        />
      </div>
      <Table
        dataSource={filtered}
        columns={columns}
        rowKey={(r) => r.order_id || r.ccxt_order_id || Math.random()}
        pagination={{ pageSize: 20, size: 'small', showSizeChanger: false }}
        size="small"
        locale={{ emptyText: t('live.orders.empty', 'No orders yet') }}
      />
    </div>
  );
};

export default OrderLog;
