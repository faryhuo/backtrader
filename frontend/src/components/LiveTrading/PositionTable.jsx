import { Table, Tag, Typography } from 'antd';
import { ArrowUpOutlined, ArrowDownOutlined } from '@ant-design/icons';
import { useTranslation } from 'react-i18next';

const { Text } = Typography;

/**
 * Position table with real-time price from ticker
 */
const PositionTable = ({ positions, ticker }) => {
  const { t } = useTranslation();

  // Merge ticker price into positions
  const enriched = positions.map(pos => {
    const currentPrice = (ticker && ticker.symbol === pos.symbol && ticker.last)
      ? Number(ticker.last)
      : pos.current_price;
    const hasCostBasis = pos.avg_price !== null && pos.avg_price !== undefined;
    const pnl = currentPrice && hasCostBasis
      ? (currentPrice - pos.avg_price) * pos.size
      : pos.pnl;
    const pnlPercent = hasCostBasis && pos.avg_price > 0 && pos.size !== 0
      ? (pnl / (Math.abs(pos.size) * pos.avg_price) * 100)
      : null;

    return { ...pos, current_price: currentPrice, pnl, pnl_percent: pnlPercent };
  });

  const columns = [
    {
      title: t('live.positions.symbol', 'Symbol'),
      dataIndex: 'symbol',
      key: 'symbol',
      width: 120,
    },
    {
      title: t('live.positions.side', 'Side'),
      dataIndex: 'side',
      key: 'side',
      width: 80,
      render: (side) => (
        <Tag color={side === 'long' ? 'green' : 'red'}>
          {(side || 'long').toUpperCase()}
        </Tag>
      ),
    },
    {
      title: t('live.positions.size', 'Size'),
      dataIndex: 'size',
      key: 'size',
      width: 100,
      render: (v) => Math.abs(v),
    },
    {
      title: t('live.positions.avg_price', 'Avg Price'),
      dataIndex: 'avg_price',
      key: 'avg_price',
      width: 120,
      render: (v) => v ? `$${Number(v).toFixed(2)}` : '-',
    },
    {
      title: t('live.positions.current_price', 'Current'),
      dataIndex: 'current_price',
      key: 'current_price',
      width: 120,
      render: (v) => v ? `$${Number(v).toFixed(2)}` : '-',
    },
    {
      title: t('live.positions.pnl', 'P&L'),
      key: 'pnl',
      width: 140,
      render: (_, record) => {
        if (record.pnl === null || record.pnl === undefined) {
          return '-';
        }
        const pnl = record.pnl;
        const pct = record.pnl_percent || 0;
        const color = pnl >= 0 ? '#4ade80' : '#f87171';
        const icon = pnl >= 0 ? <ArrowUpOutlined /> : <ArrowDownOutlined />;
        return (
          <Text style={{ color }}>
            {icon} ${pnl.toFixed(2)} ({pct.toFixed(2)}%)
          </Text>
        );
      },
    },
  ];

  return (
    <Table
      dataSource={enriched}
      columns={columns}
      rowKey="symbol"
      pagination={false}
      size="small"
      locale={{ emptyText: t('live.positions.empty', 'No open positions') }}
    />
  );
};

export default PositionTable;
