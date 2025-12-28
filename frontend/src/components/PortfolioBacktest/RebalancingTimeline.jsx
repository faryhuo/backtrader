import React from 'react';
import { Card, Timeline, Empty, Tag, Space, Tooltip, Typography } from 'antd';
import { SyncOutlined, DollarOutlined, SwapOutlined } from '@ant-design/icons';

const { Text } = Typography;

/**
 * Format currency value
 */
const formatCurrency = (value) => {
    if (value === undefined || value === null) return '-';
    return '$' + Math.abs(value).toLocaleString(undefined, {
        minimumFractionDigits: 0,
        maximumFractionDigits: 0
    });
};

/**
 * Format percentage value
 */
const formatPercent = (value) => {
    if (value === undefined || value === null) return '-';
    return (value * 100).toFixed(1) + '%';
};

/**
 * Get color based on transaction cost
 */
const getCostColor = (cost) => {
    if (!cost) return 'blue';
    if (cost < 50) return 'green';
    if (cost < 200) return 'blue';
    if (cost < 500) return 'orange';
    return 'red';
};

/**
 * Weight change indicator
 */
const WeightChange = ({ ticker, from, to }) => {
    const diff = to - from;
    const color = diff > 0 ? '#52c41a' : diff < 0 ? '#ff4d4f' : '#8c8c8c';
    const arrow = diff > 0 ? '\u2191' : diff < 0 ? '\u2193' : '-';

    return (
        <div style={{ display: 'flex', alignItems: 'center', gap: 8, fontSize: 12 }}>
            <Text strong style={{ width: 60 }}>{ticker}</Text>
            <Text type="secondary">{formatPercent(from)}</Text>
            <Text style={{ color }}>{arrow}</Text>
            <Text>{formatPercent(to)}</Text>
        </div>
    );
};

/**
 * Single rebalancing event item
 */
const RebalancingEventItem = ({ event, t }) => {
    const trades = event.trades || [];
    const buys = trades.filter(t => t.action === 'buy' || t.shares > 0);
    const sells = trades.filter(t => t.action === 'sell' || t.shares < 0);

    return (
        <div style={{ padding: '4px 0' }}>
            {/* Transaction cost */}
            {event.transaction_cost !== undefined && (
                <div style={{ marginBottom: 8 }}>
                    <Tag icon={<DollarOutlined />} color={getCostColor(event.transaction_cost)}>
                        {t('portfolio.transaction_cost', 'Cost')}: {formatCurrency(event.transaction_cost)}
                    </Tag>
                    {event.portfolio_value && (
                        <Tag color="default">
                            {t('portfolio.portfolio_value', 'Value')}: {formatCurrency(event.portfolio_value)}
                        </Tag>
                    )}
                </div>
            )}

            {/* Weight changes */}
            {event.pre_weights && event.target_weights && (
                <div style={{
                    background: 'rgba(0,0,0,0.2)',
                    borderRadius: 4,
                    padding: 8,
                    marginBottom: 8
                }}>
                    <Text type="secondary" style={{ fontSize: 11, display: 'block', marginBottom: 4 }}>
                        {t('portfolio.weight_changes', 'Weight Changes')}:
                    </Text>
                    {Object.keys(event.target_weights).map(ticker => (
                        <WeightChange
                            key={ticker}
                            ticker={ticker}
                            from={event.pre_weights[ticker] || 0}
                            to={event.target_weights[ticker] || 0}
                        />
                    ))}
                </div>
            )}

            {/* Trades summary */}
            {trades.length > 0 && (
                <div style={{ fontSize: 11 }}>
                    {buys.length > 0 && (
                        <Space size={4} wrap>
                            <Tag color="green" style={{ margin: 0 }}>
                                {t('portfolio.buy', 'BUY')}
                            </Tag>
                            {buys.map((trade, idx) => (
                                <Tooltip
                                    key={idx}
                                    title={`${Math.abs(trade.shares)} shares @ $${trade.price?.toFixed(2) || '-'}`}
                                >
                                    <Tag style={{ margin: 0 }}>{trade.ticker}</Tag>
                                </Tooltip>
                            ))}
                        </Space>
                    )}
                    {sells.length > 0 && (
                        <Space size={4} wrap style={{ marginTop: 4 }}>
                            <Tag color="red" style={{ margin: 0 }}>
                                {t('portfolio.sell', 'SELL')}
                            </Tag>
                            {sells.map((trade, idx) => (
                                <Tooltip
                                    key={idx}
                                    title={`${Math.abs(trade.shares)} shares @ $${trade.price?.toFixed(2) || '-'}`}
                                >
                                    <Tag style={{ margin: 0 }}>{trade.ticker}</Tag>
                                </Tooltip>
                            ))}
                        </Space>
                    )}
                </div>
            )}
        </div>
    );
};

/**
 * RebalancingTimeline - Shows a timeline of all rebalancing events
 */
const RebalancingTimeline = ({ rebalancingEvents, t }) => {
    if (!rebalancingEvents || rebalancingEvents.length === 0) {
        return (
            <Card
                title={
                    <Space>
                        <SyncOutlined />
                        {t('portfolio.rebalancing_history', 'Rebalancing History')}
                    </Space>
                }
            >
                <Empty description={t('portfolio.no_rebalancing', 'No rebalancing events')} />
            </Card>
        );
    }

    // Calculate total costs
    const totalCost = rebalancingEvents.reduce(
        (sum, e) => sum + (e.transaction_cost || 0),
        0
    );

    // Sort events by date
    const sortedEvents = [...rebalancingEvents].sort((a, b) =>
        a.date.localeCompare(b.date)
    );

    const timelineItems = sortedEvents.map((event, index) => ({
        color: getCostColor(event.transaction_cost),
        dot: <SwapOutlined />,
        label: event.date,
        children: <RebalancingEventItem event={event} t={t} />,
    }));

    return (
        <Card
            title={
                <Space>
                    <SyncOutlined />
                    {t('portfolio.rebalancing_history', 'Rebalancing History')}
                </Space>
            }
            extra={
                <Space>
                    <Tag color="blue">
                        {rebalancingEvents.length} {t('portfolio.events', 'events')}
                    </Tag>
                    <Tag color={getCostColor(totalCost)}>
                        {t('portfolio.total_cost', 'Total Cost')}: {formatCurrency(totalCost)}
                    </Tag>
                </Space>
            }
        >
            <div style={{ maxHeight: 400, overflow: 'auto' }}>
                <Timeline
                    mode="left"
                    items={timelineItems}
                />
            </div>
        </Card>
    );
};

export default RebalancingTimeline;
