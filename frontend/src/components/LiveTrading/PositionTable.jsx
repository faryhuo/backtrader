import React from 'react';
import { Table, Tag, Typography } from 'antd';
import { ArrowUpOutlined, ArrowDownOutlined } from '@ant-design/icons';
import { useTranslation } from 'react-i18next';

const { Text } = Typography;

/**
 * Position Table Component
 * Displays current open positions with real-time P&L
 */
const PositionTable = ({ positions, loading }) => {
  const { t } = useTranslation();

  const columns = [
    {
      title: t('live.symbol'),
      dataIndex: 'symbol',
      key: 'symbol',
      render: (symbol) => <Text strong>{symbol}</Text>
    },
    {
      title: t('live.side'),
      dataIndex: 'size',
      key: 'side',
      render: (size) => (
        <Tag color={size > 0 ? 'green' : 'red'} icon={size > 0 ? <ArrowUpOutlined /> : <ArrowDownOutlined />}>
          {size > 0 ? 'LONG' : 'SHORT'}
        </Tag>
      )
    },
    {
      title: t('live.size'),
      dataIndex: 'size',
      key: 'size',
      render: (size) => Math.abs(size).toFixed(4)
    },
    {
      title: t('live.avg_price'),
      dataIndex: 'avg_price',
      key: 'avg_price',
      render: (price) => `$${price?.toFixed(2) || '0.00'}`
    },
    {
      title: t('live.current_price'),
      dataIndex: 'current_price',
      key: 'current_price',
      render: (price) => `$${price?.toFixed(2) || '0.00'}`
    },
    {
      title: t('live.unrealized_pnl'),
      dataIndex: 'pnl',
      key: 'pnl',
      render: (pnl) => {
        const isPositive = pnl >= 0;
        return (
          <Text type={isPositive ? 'success' : 'danger'}>
            {isPositive ? '+' : ''}{pnl?.toFixed(2) || '0.00'} USD
          </Text>
        );
      }
    },
    {
      title: t('live.pnl_percent'),
      dataIndex: 'pnl_percent',
      key: 'pnl_percent',
      render: (pnlPercent, record) => {
        // Calculate P&L percentage if not provided
        let percent = pnlPercent;
        if (!percent && record.pnl && record.avg_price && record.size) {
          percent = (record.pnl / (record.avg_price * Math.abs(record.size))) * 100;
        }
        const isPositive = percent >= 0;
        return (
          <Text type={isPositive ? 'success' : 'danger'} strong>
            {isPositive ? '+' : ''}{percent?.toFixed(2) || '0.00'}%
          </Text>
        );
      }
    }
  ];

  return (
    <Table
      columns={columns}
      dataSource={positions}
      rowKey={(record, index) => record.symbol || index}
      loading={loading}
      pagination={false}
      locale={{
        emptyText: t('live.no_open_positions')
      }}
      size="middle"
    />
  );
};

export default PositionTable;
