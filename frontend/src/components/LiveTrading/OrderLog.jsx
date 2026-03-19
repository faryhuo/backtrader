import { Table, Tag, Typography, Tooltip, Button, Popconfirm, Divider } from 'antd';
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
 * Order log grouped as open orders, session fills, and historical orders
 */
const OrderLog = ({ orders, onCancelOrder }) => {
  const { t } = useTranslation();
  const openStatuses = ['submitted', 'accepted', 'partial', 'open'];
  const fillStatuses = ['filled'];

  const sortedOrders = [...orders].sort((a, b) => {
    const aTime = a.last_fill_at || a.updated_at || a.created_at || '';
    const bTime = b.last_fill_at || b.updated_at || b.created_at || '';
    return `${bTime}`.localeCompare(`${aTime}`);
  });

  const openOrders = sortedOrders.filter((o) => openStatuses.includes(o.status));
  const recentFills = sortedOrders.filter(
    (o) => fillStatuses.includes(o.status) && o?.metadata?.in_session !== false,
  );
  const historicalOrders = sortedOrders.filter(
    (o) => !openStatuses.includes(o.status) && (
      o?.metadata?.in_session === false || !fillStatuses.includes(o.status)
    ),
  );

  const renderTime = (value) => value ? (
    <Tooltip title={dayjs(value).format('YYYY-MM-DD HH:mm:ss')}>
      <Text type="secondary">{dayjs(value).format('HH:mm:ss')}</Text>
    </Tooltip>
  ) : '-';

  const baseColumns = [
    {
      title: t('live.orders.time', 'Time'),
      dataIndex: 'created_at',
      key: 'time',
      width: 80,
      render: renderTime,
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
      width: 90,
      render: (v) => v ? Math.abs(v) : '-',
    },
    {
      title: t('live.orders.price', 'Price'),
      key: 'price',
      width: 90,
      render: (_, record) => {
        const price = (record.price && Number(record.price) > 0)
          ? record.price
          : record.filled_price;
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
  ];

  const openColumns = [
    ...baseColumns,
    {
      title: '',
      key: 'action',
      width: 40,
      render: (_, record) => {
        const isOpen = openStatuses.includes(record.status);
        if (!isOpen || !onCancelOrder) return null;
        return (
          <Popconfirm
            title={t('live.orders.confirm_cancel', 'Cancel this order?')}
            onConfirm={() => onCancelOrder(record.exchange_order_id || record.order_id || record.ccxt_order_id)}
            okText={t('common.yes', 'Yes')}
            cancelText={t('common.no', 'No')}
          >
            <Button type="text" danger size="small" icon={<DeleteOutlined />} />
          </Popconfirm>
        );
      },
    },
  ];

  const fillColumns = [
    {
      title: t('live.orders.fill_time', 'Fill Time'),
      dataIndex: 'last_fill_at',
      key: 'fill_time',
      width: 90,
      render: renderTime,
    },
    ...baseColumns.slice(1, 3),
    {
      title: t('live.orders.filled_price', 'Filled Avg'),
      dataIndex: 'filled_price',
      key: 'filled_price',
      width: 100,
      render: (v) => v ? `$${Number(v).toFixed(2)}` : '-',
    },
    {
      title: t('live.orders.executed_quote_qty', 'Quote Qty'),
      dataIndex: 'executed_quote_qty',
      key: 'executed_quote_qty',
      width: 110,
      render: (v) => v ? Number(v).toFixed(4) : '-',
    },
    {
      title: t('live.orders.fee', 'Fee'),
      key: 'fee',
      width: 110,
      render: (_, record) => {
        if (record.fee === null || record.fee === undefined) return '-';
        return `${Number(record.fee).toFixed(8)}${record.fee_asset ? ` ${record.fee_asset}` : ''}`;
      },
    },
    {
      title: t('live.orders.trades', 'Trades'),
      dataIndex: 'trade_count',
      key: 'trade_count',
      width: 70,
      render: (v) => v || '-',
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
  ];

  const historyColumns = [
    {
      title: t('live.orders.time', 'Time'),
      dataIndex: 'updated_at',
      key: 'updated_at',
      width: 90,
      render: renderTime,
    },
    ...baseColumns.slice(1),
  ];

  return (
    <div>
      <div style={{ padding: '8px 16px 0' }}>
        <Text strong>{t('live.orders.group_open', 'Open Orders')}</Text>
      </div>
      <Table
        dataSource={openOrders}
        columns={openColumns}
        rowKey={(r) => `open-${r.exchange_order_id || r.order_id || Math.random()}`}
        pagination={false}
        size="small"
        locale={{ emptyText: t('live.orders.empty_open', 'No open orders') }}
      />
      <Divider style={{ margin: '12px 0' }} />
      <div style={{ padding: '0 16px 8px' }}>
        <Text strong>{t('live.orders.group_fills', 'Session Fills')}</Text>
      </div>
      <Table
        dataSource={recentFills}
        columns={fillColumns}
        rowKey={(r) => `fill-${r.exchange_order_id || r.order_id || Math.random()}`}
        pagination={{ pageSize: 20, size: 'small', showSizeChanger: false }}
        size="small"
        locale={{ emptyText: t('live.orders.empty_fills', 'No fills yet') }}
      />
      <Divider style={{ margin: '12px 0' }} />
      <div style={{ padding: '0 16px 8px' }}>
        <Text strong>{t('live.orders.group_history', 'History')}</Text>
      </div>
      <Table
        dataSource={historicalOrders}
        columns={historyColumns}
        rowKey={(r) => `history-${r.exchange_order_id || r.order_id || Math.random()}`}
        pagination={{ pageSize: 20, size: 'small', showSizeChanger: false }}
        size="small"
        locale={{ emptyText: t('live.orders.empty_history', 'No historical orders') }}
      />
    </div>
  );
};

export default OrderLog;
