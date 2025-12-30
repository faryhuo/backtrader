import { useState } from 'react';
import PropTypes from 'prop-types';
import { useTranslation } from 'react-i18next';
import { Table, Card, Empty, Timeline, Segmented, Tag, Typography } from 'antd';
import {
    UnorderedListOutlined,
    FieldTimeOutlined,
    TableOutlined,
    ArrowRightOutlined
} from '@ant-design/icons';
import { formatCurrency, formatPercent } from '../../utils/formatters';

const { Text } = Typography;

/**
 * Format currency for display
 */
const formatCurrencyDisplay = (value) => {
    if (value === undefined || value === null) return '-';
    return '$' + Math.abs(value).toLocaleString(undefined, {
        minimumFractionDigits: 2,
        maximumFractionDigits: 2
    });
};

/**
 * Single trade event item for timeline view
 */
const TradeEventItem = ({ trade, t }) => {
    const isProfitable = trade.net_pnl >= 0;

    return (
        <div style={{ padding: '4px 0' }}>
            {/* Trade summary tags */}
            <div style={{ marginBottom: 8, display: 'flex', flexWrap: 'wrap', gap: 4 }}>
                <Tag color="blue">#{trade.trade_num}</Tag>
                <Tag color={isProfitable ? 'green' : 'red'}>
                    {isProfitable ? t('trade_log.profit', 'Profit') : t('trade_log.loss', 'Loss')}: {formatCurrencyDisplay(trade.net_pnl)}
                </Tag>
                <Tag color={isProfitable ? 'green' : 'red'}>
                    {formatPercent(trade.return_pct, 2, 1)}
                </Tag>
            </div>

            {/* Trade details */}
            <div style={{
                background: 'rgba(0,0,0,0.15)',
                borderRadius: 4,
                padding: 8,
                fontSize: 11
            }}>
                {/* Open */}
                <div style={{
                    display: 'flex',
                    alignItems: 'center',
                    gap: 8,
                    marginBottom: 4
                }}>
                    <Tag color="green" style={{ margin: 0, minWidth: 45 }}>
                        {t('trade_log.open', 'Open')}
                    </Tag>
                    <Text type="secondary">{trade.open_date}</Text>
                    <Text>@</Text>
                    <Text strong>{formatCurrencyDisplay(trade.open_price)}</Text>
                    <Text type="secondary">×</Text>
                    <Text>{trade.size} {t('trade_log.shares', 'shares')}</Text>
                </div>

                {/* Arrow indicator */}
                <div style={{ textAlign: 'center', marginBottom: 4 }}>
                    <ArrowRightOutlined style={{ color: isProfitable ? '#52c41a' : '#ff4d4f' }} />
                </div>

                {/* Close */}
                <div style={{
                    display: 'flex',
                    alignItems: 'center',
                    gap: 8
                }}>
                    <Tag color="red" style={{ margin: 0, minWidth: 45 }}>
                        {t('trade_log.close', 'Close')}
                    </Tag>
                    <Text type="secondary">{trade.close_date}</Text>
                    <Text>@</Text>
                    <Text strong>{formatCurrencyDisplay(trade.close_price)}</Text>
                    <Text type="secondary">=</Text>
                    <Text style={{ color: isProfitable ? '#52c41a' : '#ff4d4f' }}>
                        {formatCurrencyDisplay(trade.net_pnl)}
                    </Text>
                </div>
            </div>
        </div>
    );
};

TradeEventItem.propTypes = {
    trade: PropTypes.object.isRequired,
    t: PropTypes.func.isRequired,
};

/**
 * TradeLog - Displays all trades from strategy backtest
 * Supports two view modes: Table and Timeline
 */
function TradeLog({ trades }) {
    const { t } = useTranslation();
    const [viewMode, setViewMode] = useState('table');

    if (!trades || trades.length === 0) {
        return (
            <Card>
                <Empty description={t('trade_log.no_trades', 'No trades executed')} />
            </Card>
        );
    }

    // Table columns
    const columns = [
        {
            title: '#',
            dataIndex: 'trade_num',
            key: 'trade_num',
            width: 50,
        },
        {
            title: t('trade_log.open_date'),
            dataIndex: 'open_date',
            key: 'open_date',
            width: 100,
        },
        {
            title: t('trade_log.open_price'),
            dataIndex: 'open_price',
            key: 'open_price',
            width: 100,
            align: 'right',
            render: (price) => formatCurrency(price),
        },
        {
            title: t('trade_log.close_date'),
            dataIndex: 'close_date',
            key: 'close_date',
            width: 100,
        },
        {
            title: t('trade_log.close_price'),
            dataIndex: 'close_price',
            key: 'close_price',
            width: 100,
            align: 'right',
            render: (price) => formatCurrency(price),
        },
        {
            title: t('trade_log.size'),
            dataIndex: 'size',
            key: 'size',
            width: 80,
            align: 'right',
        },
        {
            title: t('trade_log.net_pnl'),
            dataIndex: 'net_pnl',
            key: 'net_pnl',
            width: 100,
            align: 'right',
            render: (value) => (
                <span style={{ color: value >= 0 ? '#52c41a' : '#ff4d4f' }}>
                    {formatCurrency(value)}
                </span>
            ),
        },
        {
            title: t('trade_log.return'),
            dataIndex: 'return_pct',
            key: 'return_pct',
            width: 80,
            align: 'right',
            render: (value) => (
                <span style={{ color: value >= 0 ? '#52c41a' : '#ff4d4f' }}>
                    {formatPercent(value, 2, 1)}
                </span>
            ),
        },
    ];

    // Create timeline items - group by close date
    const timelineItems = trades.map((trade) => ({
        color: trade.net_pnl >= 0 ? 'green' : 'red',
        label: trade.close_date,
        children: <TradeEventItem trade={trade} t={t} />,
    }));

    return (
        <Card
            title={
                <span>
                    <UnorderedListOutlined style={{ marginRight: 8 }} />
                    {t('trade_log.title', 'Trade Log')} ({trades.length})
                </span>
            }
            extra={
                <Segmented
                    value={viewMode}
                    onChange={setViewMode}
                    options={[
                        {
                            value: 'table',
                            icon: <TableOutlined />,
                            label: t('trade_log.table_view', 'Table'),
                        },
                        {
                            value: 'timeline',
                            icon: <FieldTimeOutlined />,
                            label: t('trade_log.timeline_view', 'Timeline'),
                        },
                    ]}
                    size="small"
                />
            }
        >
            {viewMode === 'table' ? (
                <Table
                    dataSource={trades.map((trade, idx) => ({ ...trade, key: trade.trade_num || idx }))}
                    columns={columns}
                    size="small"
                    pagination={{ pageSize: 20, showSizeChanger: true }}
                    scroll={{ y: 400 }}
                />
            ) : (
                <div style={{ maxHeight: 400, overflow: 'auto' }}>
                    <Timeline
                        mode="left"
                        items={timelineItems}
                    />
                </div>
            )}
        </Card>
    );
}

TradeLog.propTypes = {
    trades: PropTypes.array
};

export default TradeLog;
