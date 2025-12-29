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
 * Shows: ticker | from% → to% | (+/-diff%)
 */
const WeightChange = ({ ticker, from, to }) => {
    const diff = to - from;
    const color = diff > 0 ? '#52c41a' : diff < 0 ? '#ff4d4f' : '#8c8c8c';
    const diffSign = diff > 0 ? '+' : '';

    return (
        <div style={{ display: 'flex', alignItems: 'center', gap: 8, fontSize: 12 }}>
            <Text strong style={{ width: 60 }}>{ticker}</Text>
            <Text type="secondary">{formatPercent(from)}</Text>
            <Text type="secondary">→</Text>
            <Text>{formatPercent(to)}</Text>
            <Text style={{ color, marginLeft: 4 }}>
                ({diffSign}{formatPercent(diff)})
            </Text>
        </div>
    );
};

/**
 * Single rebalancing event item with detailed trade information
 */
const RebalancingEventItem = ({ event, t }) => {
    const trades = event.trades || [];
    const buys = trades.filter(t => t.action === 'buy' || t.shares > 0);
    const sells = trades.filter(t => t.action === 'sell' || t.shares < 0);

    // Format trade value
    const formatTradeValue = (trade) => {
        if (trade.value) return formatCurrency(trade.value);
        if (trade.shares && trade.price) return formatCurrency(Math.abs(trade.shares) * trade.price);
        return '-';
    };

    return (
        <div style={{ padding: '4px 0' }}>
            {/* Transaction cost and portfolio value */}
            <div style={{ marginBottom: 8, display: 'flex', flexWrap: 'wrap', gap: 4 }}>
                {event.transaction_cost !== undefined && (
                    <Tag icon={<DollarOutlined />} color={getCostColor(event.transaction_cost)}>
                        {t('portfolio.transaction_cost', '费用')}: {formatCurrency(event.transaction_cost)}
                    </Tag>
                )}
                {event.portfolio_value && (
                    <Tag color="default">
                        {t('portfolio.portfolio_value', '价值')}: {formatCurrency(event.portfolio_value)}
                    </Tag>
                )}
                {event.pre_rebalance_value && event.post_rebalance_value && (
                    <Tag color="default">
                        {formatCurrency(event.pre_rebalance_value)} → {formatCurrency(event.post_rebalance_value)}
                    </Tag>
                )}
            </div>

            {/* Weight changes table */}
            {event.pre_weights && event.target_weights && (
                <div style={{
                    background: 'rgba(0,0,0,0.2)',
                    borderRadius: 4,
                    padding: 8,
                    marginBottom: 8
                }}>
                    <Text type="secondary" style={{ fontSize: 11, display: 'block', marginBottom: 6 }}>
                        {t('portfolio.weight_changes', '权重变化')}:
                    </Text>
                    <div style={{
                        display: 'grid',
                        gridTemplateColumns: '70px 80px 20px 80px 80px',
                        gap: '4px 8px',
                        fontSize: 12,
                        alignItems: 'center'
                    }}>
                        {/* Header */}
                        <Text type="secondary" style={{ fontSize: 10 }}>{t('portfolio.ticker', '标的')}</Text>
                        <Text type="secondary" style={{ fontSize: 10 }}>{t('portfolio.before', '调仓前')}</Text>
                        <Text type="secondary" style={{ fontSize: 10 }}></Text>
                        <Text type="secondary" style={{ fontSize: 10 }}>{t('portfolio.after', '目标')}</Text>
                        <Text type="secondary" style={{ fontSize: 10 }}>{t('portfolio.change', '变化')}</Text>

                        {/* Data rows */}
                        {Object.keys(event.target_weights).map(ticker => {
                            const from = event.pre_weights[ticker] || 0;
                            const to = event.target_weights[ticker] || 0;
                            const diff = to - from;
                            const color = diff > 0 ? '#52c41a' : diff < 0 ? '#ff4d4f' : '#8c8c8c';
                            const diffSign = diff > 0 ? '+' : '';

                            return (
                                <React.Fragment key={ticker}>
                                    <Text strong>{ticker}</Text>
                                    <Text type="secondary">{formatPercent(from)}</Text>
                                    <Text type="secondary">→</Text>
                                    <Text>{formatPercent(to)}</Text>
                                    <Text style={{ color }}>({diffSign}{formatPercent(diff)})</Text>
                                </React.Fragment>
                            );
                        })}
                    </div>
                </div>
            )}

            {/* Detailed trades */}
            {trades.length > 0 && (
                <div style={{
                    background: 'rgba(0,0,0,0.15)',
                    borderRadius: 4,
                    padding: 8,
                    fontSize: 11
                }}>
                    <Text type="secondary" style={{ fontSize: 10, display: 'block', marginBottom: 6 }}>
                        {t('portfolio.trades', '交易明细')}:
                    </Text>

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
                                        {t('portfolio.buy', '买入')}
                                    </Tag>
                                    <Text strong style={{ minWidth: 50 }}>{trade.ticker}</Text>
                                    <Text>{Math.abs(trade.shares)} {t('portfolio.shares', '股')}</Text>
                                    <Text type="secondary">@</Text>
                                    <Text>${trade.price?.toFixed(2) || '-'}</Text>
                                    <Text type="secondary">=</Text>
                                    <Text style={{ color: '#52c41a' }}>{formatTradeValue(trade)}</Text>
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
                                        {t('portfolio.sell', '卖出')}
                                    </Tag>
                                    <Text strong style={{ minWidth: 50 }}>{trade.ticker}</Text>
                                    <Text>{Math.abs(trade.shares)} {t('portfolio.shares', '股')}</Text>
                                    <Text type="secondary">@</Text>
                                    <Text>${trade.price?.toFixed(2) || '-'}</Text>
                                    <Text type="secondary">=</Text>
                                    <Text style={{ color: '#ff4d4f' }}>{formatTradeValue(trade)}</Text>
                                </div>
                            ))}
                        </div>
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
