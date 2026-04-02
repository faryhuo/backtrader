import { Table, Tag, Typography, Tooltip, Button, Popconfirm, Divider } from 'antd';
import { CheckCircleOutlined, ClockCircleOutlined, CloseCircleOutlined, SyncOutlined, DeleteOutlined } from '@ant-design/icons';
import dayjs from 'dayjs';
import { useTranslation } from 'react-i18next';
import './OrderLog.css';

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

  const formatDateTime = (value) => (value ? dayjs(value).format('YYYY-MM-DD HH:mm:ss') : '-');
  const formatTimeOnly = (value) => (value ? dayjs(value).format('HH:mm:ss') : '-');
  const formatPrice = (value) => (value ? `$${Number(value).toFixed(2)}` : '-');
  const formatSize = (value) => (value ? Math.abs(Number(value)) : '-');
  const formatQuoteQty = (value) => (value ? Number(value).toFixed(4) : '-');
  const formatFee = (fee, feeAsset) => {
    if (fee === null || fee === undefined) return '-';
    return `${Number(fee).toFixed(8)}${feeAsset ? ` ${feeAsset}` : ''}`;
  };

  const renderTime = (value) => value ? (
    <Tooltip title={formatDateTime(value)}>
      <Text type="secondary">{formatTimeOnly(value)}</Text>
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
      <div className="order-fill-list">
        {recentFills.length === 0 ? (
          <div className="order-fill-empty">
            {t('live.orders.empty_fills', 'No fills yet')}
          </div>
        ) : (
          recentFills.slice(0, 20).map((record) => {
            const statusCfg = STATUS_CONFIG[record.status] || { color: 'default', icon: null };
            return (
              <div
                key={`fill-${record.exchange_order_id || record.order_id || Math.random()}`}
                className="order-fill-card"
              >
                <div className="order-fill-top">
                  <div className="order-fill-time">
                    <div className="order-fill-label">{t('live.orders.fill_time', 'Fill Time')}</div>
                    <Tooltip title={formatDateTime(record.last_fill_at || record.updated_at || record.created_at)}>
                      <div className="order-fill-value">{formatTimeOnly(record.last_fill_at || record.updated_at || record.created_at)}</div>
                    </Tooltip>
                  </div>
                  <div className="order-fill-tags">
                    <Tag color={record.side === 'buy' ? 'green' : 'red'} style={{ margin: 0 }}>
                      {(record.side || '').toUpperCase()}
                    </Tag>
                    <Tag color={statusCfg.color} icon={statusCfg.icon} style={{ margin: 0 }}>
                      {(record.status || '').toUpperCase()}
                    </Tag>
                  </div>
                </div>

                <div className="order-fill-grid">
                  <div className="order-fill-metric">
                    <span className="order-fill-label">{t('live.orders.size', 'Size')}</span>
                    <strong>{formatSize(record.filled_size || record.size)}</strong>
                  </div>
                  <div className="order-fill-metric">
                    <span className="order-fill-label">{t('live.orders.filled_price', 'Filled Avg')}</span>
                    <strong>{formatPrice(record.filled_price || record.price)}</strong>
                  </div>
                  <div className="order-fill-metric">
                    <span className="order-fill-label">{t('live.orders.executed_quote_qty', 'Quote Qty')}</span>
                    <strong>{formatQuoteQty(record.executed_quote_qty)}</strong>
                  </div>
                  <div className="order-fill-metric">
                    <span className="order-fill-label">{t('live.orders.fee', 'Fee')}</span>
                    <strong>{formatFee(record.fee, record.fee_asset)}</strong>
                  </div>
                </div>
              </div>
            );
          })
        )}
      </div>
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
