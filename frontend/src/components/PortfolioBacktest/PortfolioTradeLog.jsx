import React from 'react';
import { Table, Tag, Card, Empty } from 'antd';
import { UnorderedListOutlined } from '@ant-design/icons';

/**
 * PortfolioTradeLog - Displays all trades from portfolio backtest
 * Uses all_trades if available, otherwise extracts from rebalancing events
 */
function PortfolioTradeLog({ allTrades, rebalancingEvents, t }) {
    // Use all_trades directly if available, otherwise extract from rebalancing events
    let trades = [];

    if (allTrades && allTrades.length > 0) {
        // Use the all_trades directly from backend
        trades = allTrades.map((trade, index) => ({
            key: index + 1,
            trade_num: index + 1,
            date: trade.date,
            ticker: trade.ticker,
            action: trade.action,
            shares: trade.shares,
            price: trade.price,
            value: trade.value,
            trigger: trade.trigger,
        }));
    } else if (rebalancingEvents && rebalancingEvents.length > 0) {
        // Fallback: Extract from rebalancing events
        let tradeNum = 1;
        rebalancingEvents.forEach((event) => {
            const eventTrades = event.trades || [];
            const prices = event.prices || {};
            const orders = event.orders || {};

            if (eventTrades.length > 0) {
                eventTrades.forEach((trade) => {
                    trades.push({
                        key: tradeNum,
                        trade_num: tradeNum++,
                        date: event.date,
                        ticker: trade.ticker,
                        action: trade.action || (trade.shares > 0 ? 'buy' : 'sell'),
                        shares: Math.abs(trade.shares),
                        price: trade.price,
                        value: Math.abs(trade.shares) * (trade.price || 0),
                        trigger: 'rebalance',
                    });
                });
            } else if (Object.keys(orders).length > 0) {
                Object.entries(orders).forEach(([ticker, shares]) => {
                    if (shares !== 0) {
                        const price = prices[ticker] || 0;
                        trades.push({
                            key: tradeNum,
                            trade_num: tradeNum++,
                            date: event.date,
                            ticker,
                            action: shares > 0 ? 'buy' : 'sell',
                            shares: Math.abs(shares),
                            price,
                            value: Math.abs(shares) * price,
                            trigger: 'rebalance',
                        });
                    }
                });
            }
        });
    }

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
            render: (action) => (
                <Tag color={action === 'buy' ? 'green' : 'red'}>
                    {action === 'buy' ? t('portfolio.buy', 'Buy') : t('portfolio.sell', 'Sell')}
                </Tag>
            ),
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
            render: (value, record) => (
                <span style={{ color: record.action === 'buy' ? '#52c41a' : '#ff4d4f' }}>
                    ${value.toLocaleString(undefined, { minimumFractionDigits: 2, maximumFractionDigits: 2 })}
                </span>
            ),
        },
        {
            title: t('portfolio.trigger', 'Trigger'),
            dataIndex: 'trigger',
            key: 'trigger',
            width: 100,
            render: (trigger) => (
                <Tag color={trigger === 'initial_position' ? 'blue' : 'purple'}>
                    {trigger === 'initial_position'
                        ? t('portfolio.initial_position', 'Initial')
                        : t('portfolio.rebalance_trigger', 'Rebalance')}
                </Tag>
            ),
        },
    ];

    if (trades.length === 0) {
        return (
            <Card>
                <Empty description={t('portfolio.no_trades', 'No trades executed')} />
            </Card>
        );
    }

    return (
        <Card
            title={
                <span>
                    <UnorderedListOutlined style={{ marginRight: 8 }} />
                    {t('portfolio.trade_log', 'Trade Log')} ({trades.length})
                </span>
            }
        >
            <Table
                dataSource={trades}
                columns={columns}
                size="small"
                pagination={{ pageSize: 20, showSizeChanger: true }}
                scroll={{ y: 400 }}
            />
        </Card>
    );
}

export default PortfolioTradeLog;
