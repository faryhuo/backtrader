import { useState, useEffect } from 'react'
import { Table, Input, Select, DatePicker, Button, Space, Tag, message, Popconfirm, Segmented } from 'antd'
import { DeleteOutlined, EyeOutlined, ReloadOutlined, FilterOutlined, FundOutlined, PieChartOutlined } from '@ant-design/icons'
import dayjs from 'dayjs'
import { useTranslation } from 'react-i18next'
import { api } from '../services/api'
import BacktestDetailModal from '../components/BacktestHistory/BacktestDetailModal'
import PortfolioDetailModal from '../components/BacktestHistory/PortfolioDetailModal'
import '../index.css'

const { RangePicker } = DatePicker

function BacktestHistory() {
    const { t } = useTranslation()

    // Record type toggle
    const [recordType, setRecordType] = useState('strategy') // 'strategy' or 'portfolio'

    // State
    const [backtests, setBacktests] = useState([])
    const [portfolios, setPortfolios] = useState([])
    const [_total, setTotal] = useState(0)
    const [loading, setLoading] = useState(false)
    const [selectedBacktest, setSelectedBacktest] = useState(null)
    const [selectedPortfolio, setSelectedPortfolio] = useState(null)
    const [detailModalVisible, setDetailModalVisible] = useState(false)
    const [portfolioModalVisible, setPortfolioModalVisible] = useState(false)

    // Filters
    const [ticker, setTicker] = useState(null)
    const [strategyName, setStrategyName] = useState(null)
    const [dateRange, setDateRange] = useState(null)
    const [strategies, setStrategies] = useState([])

    // Pagination & Sorting
    const [pagination, setPagination] = useState({
        current: 1,
        pageSize: 20,
        total: 0
    })
    const [sortField, setSortField] = useState('created_at')
    const [sortOrder, setSortOrder] = useState('desc')

    useEffect(() => {
        fetchStrategies()
    }, [])

    useEffect(() => {
        if (recordType === 'strategy') {
            fetchBacktests()
        } else {
            fetchPortfolios()
        }
    }, [recordType])

    const fetchStrategies = async () => {
        try {
            const names = await api.getStrategies()
            setStrategies(names)
        } catch (err) {
            console.error('Failed to fetch strategies:', err)
        }
    }

    const fetchBacktests = async (params = {}) => {
        setLoading(true)
        try {
            const queryParams = {
                ticker: params.ticker !== undefined ? params.ticker : ticker,
                strategy_name: params.strategyName !== undefined ? params.strategyName : strategyName,
                start_date: params.dateRange?.[0] || dateRange?.[0],
                end_date: params.dateRange?.[1] || dateRange?.[1],
                sort_by: params.sortField || sortField,
                sort_order: params.sortOrder || sortOrder,
                limit: params.pageSize || pagination.pageSize,
                offset: ((params.current || pagination.current) - 1) * (params.pageSize || pagination.pageSize)
            }

            const result = await api.getBacktestHistory(queryParams)
            setBacktests(result.backtests || [])
            setTotal(result.total || 0)
            setPagination({
                ...pagination,
                total: result.total || 0,
                current: params.current || pagination.current,
                pageSize: params.pageSize || pagination.pageSize
            })
        } catch (err) {
            message.error(t('history.fetch_error'))
            console.error(err)
        } finally {
            setLoading(false)
        }
    }

    const fetchPortfolios = async (params = {}) => {
        setLoading(true)
        try {
            const queryParams = {
                sort_by: params.sortField || sortField,
                sort_order: params.sortOrder || sortOrder,
                limit: params.pageSize || pagination.pageSize,
                offset: ((params.current || pagination.current) - 1) * (params.pageSize || pagination.pageSize)
            }

            const result = await api.getPortfolioHistory(queryParams)
            setPortfolios(result.results || [])
            setTotal(result.count || 0)
            setPagination({
                ...pagination,
                total: result.count || 0,
                current: params.current || pagination.current,
                pageSize: params.pageSize || pagination.pageSize
            })
        } catch (err) {
            message.error(t('history.fetch_error'))
            console.error(err)
        } finally {
            setLoading(false)
        }
    }

    const handleTableChange = (newPagination, filters, sorter) => {
        const sortFieldMap = {
            'created_at': 'created_at',
            'total_return': 'total_return',
            'sharpe_ratio': 'sharpe_ratio',
            'weighted_sharpe': 'weighted_sharpe'
        }

        const newSortField = sorter.field ? sortFieldMap[sorter.field] : 'created_at'
        const newSortOrder = sorter.order === 'ascend' ? 'asc' : 'desc'

        setSortField(newSortField)
        setSortOrder(newSortOrder)

        const fetchFn = recordType === 'strategy' ? fetchBacktests : fetchPortfolios
        fetchFn({
            current: newPagination.current,
            pageSize: newPagination.pageSize,
            sortField: newSortField,
            sortOrder: newSortOrder
        })
    }

    const handleFilter = () => {
        setPagination({ ...pagination, current: 1 })
        fetchBacktests({ current: 1 })
    }

    const handleReset = () => {
        setTicker(null)
        setStrategyName(null)
        setDateRange(null)
        setPagination({ ...pagination, current: 1 })
        const fetchFn = recordType === 'strategy' ? fetchBacktests : fetchPortfolios
        fetchFn({
            current: 1,
            ticker: null,
            strategyName: null,
            dateRange: null
        })
    }

    const handleViewDetail = async (record) => {
        try {
            const detail = await api.getBacktestDetail(record.backtest_id)
            setSelectedBacktest(detail)
            setDetailModalVisible(true)
        } catch (err) {
            message.error(t('history.detail_error'))
            console.error(err)
        }
    }

    const handleViewPortfolioDetail = async (record) => {
        try {
            const detail = await api.getPortfolioDetail(record.portfolio_id)
            setSelectedPortfolio(detail)
            setPortfolioModalVisible(true)
        } catch (err) {
            message.error(t('history.portfolio_detail_error'))
            console.error(err)
        }
    }

    const handleAnalysisUpdate = (backtestId, analysis) => {
        // Update the selected backtest with new AI analysis
        setSelectedBacktest(prev => ({
            ...prev,
            ai_analysis: analysis
        }))
    }

    const handleDelete = async (backtestId) => {
        try {
            await api.deleteBacktest(backtestId)
            message.success(t('history.delete_success'))
            fetchBacktests()
        } catch (err) {
            message.error(t('history.delete_error'))
            console.error(err)
        }
    }

    const handleDeletePortfolio = async (portfolioId) => {
        try {
            await api.deletePortfolio(portfolioId)
            message.success(t('history.portfolio_delete_success'))
            fetchPortfolios()
        } catch (err) {
            message.error(t('history.portfolio_delete_error'))
            console.error(err)
        }
    }

    const handleRecordTypeChange = (value) => {
        setRecordType(value)
        setPagination({ ...pagination, current: 1 })
    }

    // Strategy backtest columns
    const strategyColumns = [
        {
            title: t('history.date'),
            dataIndex: 'created_at',
            key: 'created_at',
            width: 160,
            sorter: true,
            defaultSortOrder: 'descend',
            render: (date) => date ? dayjs(date).format('YYYY-MM-DD HH:mm') : 'N/A'
        },
        {
            title: t('history.ticker'),
            dataIndex: 'ticker',
            key: 'ticker',
            width: 100,
            render: (ticker) => <Tag color="blue">{ticker}</Tag>
        },
        {
            title: t('history.strategy'),
            dataIndex: 'strategy_name',
            key: 'strategy_name',
            width: 150,
            ellipsis: true
        },
        {
            title: t('history.period'),
            key: 'period',
            width: 200,
            render: (_, record) => `${record.start_date} ~ ${record.end_date}`
        },
        {
            title: t('history.return'),
            dataIndex: 'total_return',
            key: 'total_return',
            width: 120,
            sorter: true,
            render: (value) => {
                if (value === null || value === undefined) return 'N/A'
                const color = value >= 0 ? 'green' : 'red'
                return <Tag color={color}>{value.toFixed(2)}%</Tag>
            }
        },
        {
            title: t('history.sharpe'),
            dataIndex: 'sharpe_ratio',
            key: 'sharpe_ratio',
            width: 120,
            sorter: true,
            render: (value) => value !== null && value !== undefined ? value.toFixed(2) : 'N/A'
        },
        {
            title: t('history.drawdown'),
            dataIndex: 'max_drawdown',
            key: 'max_drawdown',
            width: 120,
            render: (value) => value !== null && value !== undefined ? `${value.toFixed(2)}%` : 'N/A'
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
            )
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
                        onClick={() => handleViewDetail(record)}
                    >
                        {t('common.view')}
                    </Button>
                    <Popconfirm
                        title={t('history.delete_confirm')}
                        onConfirm={() => handleDelete(record.backtest_id)}
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
            )
        }
    ]

    // Portfolio columns
    const portfolioColumns = [
        {
            title: t('history.date'),
            dataIndex: 'created_at',
            key: 'created_at',
            width: 160,
            sorter: true,
            defaultSortOrder: 'descend',
            render: (date) => date ? dayjs(date).format('YYYY-MM-DD HH:mm') : 'N/A'
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
            )
        },
        {
            title: t('history.num_assets'),
            dataIndex: 'num_assets',
            key: 'num_assets',
            width: 80,
            render: (value, record) => value || record.tickers?.length || 0
        },
        {
            title: t('history.period'),
            key: 'period',
            width: 200,
            render: (_, record) => `${record.start_date} ~ ${record.end_date}`
        },
        {
            title: t('history.return'),
            dataIndex: 'total_return',
            key: 'total_return',
            width: 120,
            sorter: true,
            render: (value) => {
                if (value === null || value === undefined) return 'N/A'
                const color = value >= 0 ? 'green' : 'red'
                return <Tag color={color}>{value.toFixed(2)}%</Tag>
            }
        },
        {
            title: t('history.weighted_sharpe'),
            dataIndex: 'weighted_sharpe',
            key: 'weighted_sharpe',
            width: 120,
            sorter: true,
            render: (value) => value !== null && value !== undefined ? value.toFixed(2) : 'N/A'
        },
        {
            title: t('history.drawdown'),
            dataIndex: 'max_drawdown',
            key: 'max_drawdown',
            width: 120,
            render: (value) => value !== null && value !== undefined ? `${value.toFixed(2)}%` : 'N/A'
        },
        {
            title: t('history.strategy'),
            dataIndex: 'strategy_name',
            key: 'strategy_name',
            width: 150,
            ellipsis: true,
            render: (value) => value || 'Default'
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
                        onClick={() => handleViewPortfolioDetail(record)}
                    >
                        {t('common.view')}
                    </Button>
                    <Popconfirm
                        title={t('history.delete_confirm')}
                        onConfirm={() => handleDeletePortfolio(record.portfolio_id)}
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
            )
        }
    ]

    const columns = recordType === 'strategy' ? strategyColumns : portfolioColumns
    const dataSource = recordType === 'strategy' ? backtests : portfolios
    const rowKey = recordType === 'strategy' ? 'backtest_id' : 'portfolio_id'
    const emptyText = recordType === 'strategy' ? t('history.no_history') : t('history.no_portfolio_history')

    return (
        <div className="page-container">
            <div className="page-header">
                <h1>{t('history.title')}</h1>
                <p>{t('history.subtitle')}</p>
            </div>

            {/* Record Type Toggle */}
            <div className="card" style={{ marginBottom: '1rem', padding: '1rem' }}>
                <Space wrap style={{ width: '100%', justifyContent: 'space-between' }}>
                    <Segmented
                        options={[
                            {
                                label: (
                                    <Space>
                                        <FundOutlined />
                                        {t('history.type_strategy')}
                                    </Space>
                                ),
                                value: 'strategy'
                            },
                            {
                                label: (
                                    <Space>
                                        <PieChartOutlined />
                                        {t('history.type_portfolio')}
                                    </Space>
                                ),
                                value: 'portfolio'
                            }
                        ]}
                        value={recordType}
                        onChange={handleRecordTypeChange}
                    />

                    {/* Filters - only show for strategy */}
                    {recordType === 'strategy' && (
                        <Space wrap>
                            <Input
                                placeholder={t('history.filter_ticker')}
                                value={ticker}
                                onChange={(e) => setTicker(e.target.value || null)}
                                style={{ width: 120 }}
                                allowClear
                            />
                            <Select
                                placeholder={t('history.filter_strategy')}
                                value={strategyName}
                                onChange={setStrategyName}
                                style={{ width: 200 }}
                                allowClear
                            >
                                {strategies.map(name => (
                                    <Select.Option key={name} value={name}>{name}</Select.Option>
                                ))}
                            </Select>
                            <RangePicker
                                value={dateRange ? [dayjs(dateRange[0]), dayjs(dateRange[1])] : null}
                                onChange={(dates) => setDateRange(dates ? [dates[0].format('YYYY-MM-DD'), dates[1].format('YYYY-MM-DD')] : null)}
                                placeholder={[t('history.start_date'), t('history.end_date')]}
                            />
                            <Button
                                type="primary"
                                icon={<FilterOutlined />}
                                onClick={handleFilter}
                            >
                                {t('common.filter')}
                            </Button>
                        </Space>
                    )}

                    <Button
                        icon={<ReloadOutlined />}
                        onClick={handleReset}
                    >
                        {t('common.reset')}
                    </Button>
                </Space>
            </div>

            {/* Table */}
            <div className="card">
                <Table
                    columns={columns}
                    dataSource={dataSource}
                    rowKey={rowKey}
                    loading={loading}
                    pagination={pagination}
                    onChange={handleTableChange}
                    scroll={{ x: 'max-content' }}
                    locale={{
                        emptyText: emptyText
                    }}
                />
            </div>

            {/* Strategy Detail Modal */}
            {selectedBacktest && (
                <BacktestDetailModal
                    visible={detailModalVisible}
                    backtest={selectedBacktest}
                    onClose={() => {
                        setDetailModalVisible(false)
                        setSelectedBacktest(null)
                    }}
                    onAnalysisUpdate={handleAnalysisUpdate}
                />
            )}

            {/* Portfolio Detail Modal */}
            {selectedPortfolio && (
                <PortfolioDetailModal
                    visible={portfolioModalVisible}
                    portfolio={selectedPortfolio}
                    onClose={() => {
                        setPortfolioModalVisible(false)
                        setSelectedPortfolio(null)
                    }}
                />
            )}
        </div>
    )
}

export default BacktestHistory
