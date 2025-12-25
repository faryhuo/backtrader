import { Tag, Space, Button, Popconfirm } from 'antd';
import { DeleteOutlined, EyeOutlined } from '@ant-design/icons';
import dayjs from 'dayjs';

/**
 * Generate column definitions for strategy backtest history table.
 *
 * @param {Object} options - Column configuration
 * @param {function} options.t - Translation function
 * @param {function} options.onView - View detail handler
 * @param {function} options.onDelete - Delete handler
 * @returns {Array} Column definitions
 */
export function getStrategyBacktestColumns({ t, onView, onDelete }) {
    return [
        {
            title: t('history.date'),
            dataIndex: 'created_at',
            key: 'created_at',
            width: 160,
            sorter: true,
            defaultSortOrder: 'descend',
            render: (date) => date ? dayjs(date).format('YYYY-MM-DD HH:mm') : 'N/A',
        },
        {
            title: t('history.ticker'),
            dataIndex: 'ticker',
            key: 'ticker',
            width: 100,
            render: (ticker) => <Tag color="blue">{ticker}</Tag>,
        },
        {
            title: t('history.strategy'),
            dataIndex: 'strategy_name',
            key: 'strategy_name',
            width: 150,
            ellipsis: true,
        },
        {
            title: t('history.period'),
            key: 'period',
            width: 200,
            render: (_, record) => `${record.start_date} ~ ${record.end_date}`,
        },
        {
            title: t('history.return'),
            dataIndex: 'total_return',
            key: 'total_return',
            width: 120,
            sorter: true,
            render: (value) => {
                if (value === null || value === undefined) return 'N/A';
                const color = value >= 0 ? 'green' : 'red';
                return <Tag color={color}>{value.toFixed(2)}%</Tag>;
            },
        },
        {
            title: t('history.sharpe'),
            dataIndex: 'sharpe_ratio',
            key: 'sharpe_ratio',
            width: 120,
            sorter: true,
            render: (value) => value !== null && value !== undefined ? value.toFixed(2) : 'N/A',
        },
        {
            title: t('history.drawdown'),
            dataIndex: 'max_drawdown',
            key: 'max_drawdown',
            width: 120,
            render: (value) => value !== null && value !== undefined ? `${value.toFixed(2)}%` : 'N/A',
        },
        {
            title: t('history.trades'),
            dataIndex: 'total_trades',
            key: 'total_trades',
            width: 120,
            render: (total, record) => (
                <span>
                    {total} ({record.winning_trades}W/{record.losing_trades}L)
                </span>
            ),
        },
        {
            title: t('history.actions'),
            key: 'actions',
            fixed: 'right',
            width: 120,
            render: (_, record) => (
                <Space size="small">
                    <Button
                        type="link"
                        size="small"
                        icon={<EyeOutlined />}
                        onClick={() => onView(record)}
                    >
                        {t('common.view')}
                    </Button>
                    <Popconfirm
                        title={t('history.delete_confirm')}
                        onConfirm={() => onDelete(record.backtest_id)}
                        okText={t('common.yes')}
                        cancelText={t('common.no')}
                    >
                        <Button
                            type="link"
                            danger
                            size="small"
                            icon={<DeleteOutlined />}
                        />
                    </Popconfirm>
                </Space>
            ),
        },
    ];
}

/**
 * Generate column definitions for portfolio backtest history table.
 *
 * @param {Object} options - Column configuration
 * @param {function} options.t - Translation function
 * @param {function} options.onView - View detail handler
 * @param {function} options.onDelete - Delete handler
 * @returns {Array} Column definitions
 */
export function getPortfolioBacktestColumns({ t, onView, onDelete }) {
    return [
        {
            title: t('history.date'),
            dataIndex: 'created_at',
            key: 'created_at',
            width: 160,
            sorter: true,
            defaultSortOrder: 'descend',
            render: (date) => date ? dayjs(date).format('YYYY-MM-DD HH:mm') : 'N/A',
        },
        {
            title: t('history.tickers'),
            dataIndex: 'tickers',
            key: 'tickers',
            width: 200,
            render: (tickers) => (
                <Space size={[0, 4]} wrap>
                    {tickers?.slice(0, 3).map(ticker => (
                        <Tag key={ticker} color="blue">{ticker}</Tag>
                    ))}
                    {tickers?.length > 3 && <Tag>+{tickers.length - 3}</Tag>}
                </Space>
            ),
        },
        {
            title: t('history.num_assets'),
            dataIndex: 'num_assets',
            key: 'num_assets',
            width: 80,
            render: (value, record) => value || record.tickers?.length || 0,
        },
        {
            title: t('history.period'),
            key: 'period',
            width: 200,
            render: (_, record) => `${record.start_date} ~ ${record.end_date}`,
        },
        {
            title: t('history.return'),
            dataIndex: 'total_return',
            key: 'total_return',
            width: 120,
            sorter: true,
            render: (value) => {
                if (value === null || value === undefined) return 'N/A';
                const color = value >= 0 ? 'green' : 'red';
                return <Tag color={color}>{value.toFixed(2)}%</Tag>;
            },
        },
        {
            title: t('history.weighted_sharpe'),
            dataIndex: 'weighted_sharpe',
            key: 'weighted_sharpe',
            width: 120,
            sorter: true,
            render: (value) => value !== null && value !== undefined ? value.toFixed(2) : 'N/A',
        },
        {
            title: t('history.drawdown'),
            dataIndex: 'max_drawdown',
            key: 'max_drawdown',
            width: 120,
            render: (value) => value !== null && value !== undefined ? `${value.toFixed(2)}%` : 'N/A',
        },
        {
            title: t('history.strategy'),
            dataIndex: 'strategy_name',
            key: 'strategy_name',
            width: 150,
            ellipsis: true,
            render: (value) => value || 'Default',
        },
        {
            title: t('history.actions'),
            key: 'actions',
            fixed: 'right',
            width: 120,
            render: (_, record) => (
                <Space size="small">
                    <Button
                        type="link"
                        size="small"
                        icon={<EyeOutlined />}
                        onClick={() => onView(record)}
                    >
                        {t('common.view')}
                    </Button>
                    <Popconfirm
                        title={t('history.delete_confirm')}
                        onConfirm={() => onDelete(record.portfolio_id)}
                        okText={t('common.yes')}
                        cancelText={t('common.no')}
                    >
                        <Button
                            type="link"
                            danger
                            size="small"
                            icon={<DeleteOutlined />}
                        />
                    </Popconfirm>
                </Space>
            ),
        },
    ];
}

/**
 * Generate column definitions for individual asset results table (PortfolioBacktest).
 *
 * @param {Object} options - Column configuration
 * @param {function} options.t - Translation function
 * @returns {Array} Column definitions
 */
export function getIndividualResultsColumns({ t }) {
    return [
        {
            title: t('portfolio.table.ticker', 'Ticker'),
            dataIndex: 'ticker',
            render: ticker => <Tag color="blue">{ticker}</Tag>,
        },
        {
            title: t('portfolio.table.weight', 'Weight'),
            dataIndex: 'weight',
            render: w => `${(w * 100).toFixed(0)}%`,
        },
        {
            title: t('portfolio.table.status', 'Status'),
            dataIndex: 'success',
            render: s => s
                ? <span style={{ color: '#52c41a' }}>✓</span>
                : <span style={{ color: '#ff4d4f' }}>✗</span>,
        },
        {
            title: t('portfolio.table.initial', 'Initial'),
            dataIndex: 'initial_cash',
            render: v => v ? `$${v.toLocaleString()}` : '-',
        },
        {
            title: t('portfolio.table.final', 'Final'),
            dataIndex: 'final_value',
            render: v => v ? `$${v.toLocaleString()}` : '-',
        },
        {
            title: t('portfolio.table.return', 'Return'),
            dataIndex: 'return',
            render: r => r != null
                ? <span className={r >= 0 ? 'positive' : 'negative'}>{r.toFixed(2)}%</span>
                : '-',
        },
        {
            title: t('portfolio.table.sharpe', 'Sharpe'),
            dataIndex: 'sharpe',
            render: s => s?.toFixed(4) || '-',
        },
    ];
}
