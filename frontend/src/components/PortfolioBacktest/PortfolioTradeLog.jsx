import { useState } from 'react';
import { Table, Tag, Card, Empty, Timeline, Segmented, Typography } from 'antd';
import { UnorderedListOutlined, FieldTimeOutlined, SwapOutlined, TableOutlined } from '@ant-design/icons';

const { Text } = Typography;

/**
 * Format currency value
 */
const formatCurrency = (value) => {
    if (value === undefined || value === null) return '-';
    return '$' + Math.abs(value).toLocaleString(undefined, {
        minimumFractionDigits: 2,
        maximumFractionDigits: 2
    });
};

/**
 * Get color based on trade trigger type
 */
const getTriggerColor = (trigger) => {
    if (trigger === 'initial_position') return 'blue';
    if (trigger === 'strategy') return 'cyan';
    return 'default';
};

/**
 * Single trade event item for timeline view
 */
const TradeEventItem = ({ trades, t }) => {
    const buys = trades.filter(t => t.action?.toLowerCase() === 'buy');
    const sells = trades.filter(t => t.action?.toLowerCase() === 'sell');

    // Calculate total value for this date
    const totalBuyValue = buys.reduce((sum, t) => sum + (t.value || 0), 0);
    const totalSellValue = sells.reduce((sum, t) => sum + (t.value || 0), 0);

    // Get unique triggers
    const triggers = [...new Set(trades.map(t => t.trigger))];

    return (
        <div style={{ padding: '4px 0' }}>
            {/* Trigger tags */}
            <div style={{ marginBottom: 8, display: 'flex', flexWrap: 'wrap', gap: 4 }}>
                {triggers.map(trigger => {
                    const isInitial = trigger === 'initial_position';
                    const isStrategy = trigger === 'strategy';
                    let label = t('portfolio.other_trigger', 'Other');
                    if (isInitial) label = t('portfolio.initial_position', 'Initial Position');
                    else if (isStrategy) label = t('portfolio.strategy_trigger', 'Strategy');

                    return (
                        <Tag key={trigger} color={getTriggerColor(trigger)}>
                            {label}
                        </Tag>
                    );
                })}
                {totalBuyValue > 0 && (
                    <Tag color="green">
                        {t('portfolio.buy', 'Buy')}: {formatCurrency(totalBuyValue)}
                    </Tag>
                )}
                {totalSellValue > 0 && (
                    <Tag color="red">
                        {t('portfolio.sell', 'Sell')}: {formatCurrency(totalSellValue)}
                    </Tag>
                )}
            </div>

            {/* Trade details */}
            <div style={{
                background: 'rgba(0,0,0,0.15)',
                borderRadius: 4,
                padding: 8,
                fontSize: 11
            }}>
                {/* Buys */}
                {buys.length > 0 && (
                    <div style={{ marginBottom: sells.length > 0 ? 6 : 0 }}>
                        {buys.map((trade, idx) => (
                            <div key={idx} style={{
                                display: 'flex',
                                alignItems: 'center',
                                gap: 8,
                                marginBottom: 2
                            }}>
                                <Tag color="green" style={{ margin: 0, minWidth: 35 }}>
                                    {t('portfolio.buy', 'Buy')}
                                </Tag>
                                <Text strong style={{ minWidth: 50 }}>{trade.ticker}</Text>
                                <Text>{trade.shares} {t('portfolio.shares', 'shares')}</Text>
                                <Text type="secondary">@</Text>
                                <Text>${trade.price?.toFixed(2) || '-'}</Text>
                                <Text type="secondary">=</Text>
                                <Text style={{ color: '#52c41a' }}>{formatCurrency(trade.value)}</Text>
                            </div>
                        ))}
                    </div>
                )}

                {/* Sells */}
                {sells.length > 0 && (
                    <div>
                        {sells.map((trade, idx) => (
                            <div key={idx} style={{
                                display: 'flex',
                                alignItems: 'center',
                                gap: 8,
                                marginBottom: 2
                            }}>
                                <Tag color="red" style={{ margin: 0, minWidth: 35 }}>
                                    {t('portfolio.sell', 'Sell')}
                                </Tag>
                                <Text strong style={{ minWidth: 50 }}>{trade.ticker}</Text>
                                <Text>{trade.shares} {t('portfolio.shares', 'shares')}</Text>
                                <Text type="secondary">@</Text>
                                <Text>${trade.price?.toFixed(2) || '-'}</Text>
                                <Text type="secondary">=</Text>
                                <Text style={{ color: '#ff4d4f' }}>{formatCurrency(trade.value)}</Text>
                            </div>
                        ))}
                    </div>
                )}
            </div>
        </div>
    );
};

/**
 * PortfolioTradeLog - Displays all trades from portfolio backtest
 * Supports two view modes: Table and Timeline
 */
function PortfolioTradeLog({ allTrades, t }) {
    const [viewMode, setViewMode] = useState('table');

    // Use all_trades directly if available
    let trades = [];

    if (allTrades && allTrades.length > 0) {
        // Use the all_trades directly from backend
        trades = allTrades.map((trade, index) => ({
            key: index + 1,
            trade_num: index + 1,
            date: trade.date,
            ticker: trade.ticker,
            action: trade.action?.toLowerCase() || 'buy', // Normalize to lowercase
            shares: trade.shares,
            price: trade.price,
            value: trade.value,
            trigger: trade.trigger || 'strategy',
        }));
    }

    // Group trades by date for timeline view
    const tradesByDate = trades.reduce((groups, trade) => {
        const date = trade.date;
        if (!groups[date]) {
            groups[date] = [];
        }
        groups[date].push(trade);
        return groups;
    }, {});

    // Sort dates
    const sortedDates = Object.keys(tradesByDate).sort();

    const columns = [
        {
            title: '#',
            dataIndex: 'trade_num',
            key: 'trade_num',
            width: 50,
        },
        {
            title: t('portfolio.trade_date', 'Date'),
            dataIndex: 'date',
            key: 'date',
            width: 120,
        },
        {
            title: t('portfolio.ticker', 'Ticker'),
            dataIndex: 'ticker',
            key: 'ticker',
            width: 80,
            render: (ticker) => <Tag color="blue">{ticker}</Tag>,
        },
        {
            title: t('portfolio.trade_action', 'Action'),
            dataIndex: 'action',
            key: 'action',
            width: 80,
            render: (action) => {
                const isBuy = action?.toLowerCase() === 'buy';
                return (
                    <Tag color={isBuy ? 'green' : 'red'}>
                        {isBuy ? t('portfolio.buy', 'Buy') : t('portfolio.sell', 'Sell')}
                    </Tag>
                );
            },
        },
        {
            title: t('portfolio.shares', 'Shares'),
            dataIndex: 'shares',
            key: 'shares',
            width: 80,
            align: 'right',
        },
        {
            title: t('portfolio.price', 'Price'),
            dataIndex: 'price',
            key: 'price',
            width: 100,
            align: 'right',
            render: (price) => price ? `$${price.toFixed(2)}` : '-',
        },
        {
            title: t('portfolio.trade_value', 'Value'),
            dataIndex: 'value',
            key: 'value',
            width: 120,
            align: 'right',
            render: (value, record) => {
                const isBuy = record.action?.toLowerCase() === 'buy';
                return (
                    <span style={{ color: isBuy ? '#52c41a' : '#ff4d4f' }}>
                        ${value.toLocaleString(undefined, { minimumFractionDigits: 2, maximumFractionDigits: 2 })}
                    </span>
                );
            },
        },
        {
            title: t('portfolio.trigger', 'Trigger'),
            dataIndex: 'trigger',
            key: 'trigger',
            width: 100,
            render: (trigger) => {
                const isInitial = trigger === 'initial_position';
                const isStrategy = trigger === 'strategy';
                let color = 'purple';
                let label = t('portfolio.rebalance_trigger', 'Rebalance');

                if (isInitial) {
                    color = 'blue';
                    label = t('portfolio.initial_position', 'Initial');
                } else if (isStrategy) {
                    color = 'cyan';
                    label = t('portfolio.strategy_trigger', 'Strategy');
                }

                return <Tag color={color}>{label}</Tag>;
            },
        },
    ];

    if (trades.length === 0) {
        return (
            <Card>
                <Empty description={t('portfolio.no_trades', 'No trades executed')} />
            </Card>
        );
    }

    // Create timeline items
    const timelineItems = sortedDates.map((date) => ({
        color: getTriggerColor(tradesByDate[date][0]?.trigger),
        dot: <SwapOutlined />,
        label: date,
        children: <TradeEventItem trades={tradesByDate[date]} t={t} />,
    }));

    return (
        <Card
            title={
                <span>
                    <UnorderedListOutlined style={{ marginRight: 8 }} />
                    {t('portfolio.trade_log', 'Trade Log')} ({trades.length})
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
                            label: t('portfolio.table_view', 'Table'),
                        },
                        {
                            value: 'timeline',
                            icon: <FieldTimeOutlined />,
                            label: t('portfolio.timeline_view', 'Timeline'),
                        },
                    ]}
                    size="small"
                />
            }
        >
            {viewMode === 'table' ? (
                <Table
                    dataSource={trades}
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

export default PortfolioTradeLog;
