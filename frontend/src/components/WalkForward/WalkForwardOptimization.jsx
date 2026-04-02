import { useState, useEffect, useCallback } from 'react'
import { useTranslation } from 'react-i18next'
import {
    Card,
    Button,
    Table,
    Tag,
    Space,
    Modal,
    Empty,
    message,
    Tooltip
} from 'antd'
import {
    PlayCircleOutlined,
    ReloadOutlined,
    DeleteOutlined,
    EyeOutlined,
    ExclamationCircleOutlined,
    CheckCircleOutlined
} from '@ant-design/icons'
import { api } from '../../services/api'
import WalkForwardConfigModal from './WalkForwardConfigModal'
import WalkForwardDetailModal from './WalkForwardDetailModal'

const { confirm } = Modal

const WalkForwardOptimization = () => {
    const { t } = useTranslation()
    const [optimizations, setOptimizations] = useState([])
    const [loading, setLoading] = useState(false)
    const [configModalVisible, setConfigModalVisible] = useState(false)
    const [detailModalVisible, setDetailModalVisible] = useState(false)
    const [selectedOptimization, setSelectedOptimization] = useState(null)
    const [pagination, setPagination] = useState({
        current: 1,
        pageSize: 20,
        total: 0
    })
    const currentPage = pagination.current
    const pageSize = pagination.pageSize

    const loadOptimizations = useCallback(async (silent = false) => {
        if (!silent) setLoading(true)
        try {
            const response = await api.listWalkForward({
                limit: pageSize,
                offset: (currentPage - 1) * pageSize,
                sort_by: 'created_at',
                sort_order: 'desc'
            })
            setOptimizations(response.optimizations || [])
            setPagination(prev => ({ ...prev, total: response.total || 0 }))
        } catch (error) {
            if (!silent) {
                message.error(t('walkforward.loadError', { error: error.message }))
            }
        } finally {
            if (!silent) setLoading(false)
        }
    }, [currentPage, pageSize, t])

    useEffect(() => {
        loadOptimizations()
        const interval = setInterval(() => {
            loadOptimizations(true)
        }, 5000)
        return () => clearInterval(interval)
    }, [loadOptimizations])

    const handleStartOptimization = () => {
        setConfigModalVisible(true)
    }

    const handleConfigSubmit = async (values) => {
        try {
            await api.startWalkForward(values)
            message.success(t('walkforward.startSuccess'))
            setConfigModalVisible(false)
            loadOptimizations()
        } catch (error) {
            message.error(t('walkforward.startError', { error: error.message }))
        }
    }

    const handleViewDetail = async (record) => {
        try {
            const detail = await api.getWalkForward(record.optimization_id)
            setSelectedOptimization(detail)
            setDetailModalVisible(true)
        } catch (error) {
            message.error(t('walkforward.loadDetailError', { error: error.message }))
        }
    }

    const handleDelete = (record) => {
        confirm({
            title: t('walkforward.deleteConfirmTitle'),
            icon: <ExclamationCircleOutlined />,
            content: t('walkforward.deleteConfirmContent'),
            onOk: async () => {
                try {
                    await api.deleteWalkForward(record.optimization_id)
                    message.success(t('walkforward.deleteSuccess'))
                    loadOptimizations()
                } catch (error) {
                    message.error(t('walkforward.deleteError', { error: error.message }))
                }
            }
        })
    }

    const getStatusTag = (status) => {
        const statusConfig = {
            pending: { color: 'default', text: t('walkforward.status.pending') },
            running: { color: 'processing', text: t('walkforward.status.running') },
            completed: { color: 'success', text: t('walkforward.status.completed') },
            failed: { color: 'error', text: t('walkforward.status.failed') }
        }
        const config = statusConfig[status] || statusConfig.pending
        return <Tag color={config.color}>{config.text}</Tag>
    }

    const getOverfittingTag = (detected) => {
        if (detected) {
            return (
                <Tooltip title={t('walkforward.overfittingDetectedTooltip')}>
                    <Tag color="warning" icon={<ExclamationCircleOutlined />}>
                        {t('walkforward.overfittingDetected')}
                    </Tag>
                </Tooltip>
            )
        } else {
            return (
                <Tooltip title={t('walkforward.noOverfittingTooltip')}>
                    <Tag color="success" icon={<CheckCircleOutlined />}>
                        {t('walkforward.noOverfitting')}
                    </Tag>
                </Tooltip>
            )
        }
    }

    const columns = [
        {
            title: t('walkforward.table.createdAt'),
            dataIndex: 'created_at',
            key: 'created_at',
            width: 180,
            render: (text) => new Date(text).toLocaleString()
        },
        {
            title: t('walkforward.table.strategy'),
            dataIndex: 'strategy_name',
            key: 'strategy_name',
            width: 150
        },
        {
            title: t('walkforward.table.ticker'),
            dataIndex: 'ticker',
            key: 'ticker',
            width: 100
        },
        {
            title: t('walkforward.table.dateRange'),
            key: 'date_range',
            width: 200,
            render: (_, record) => `${record.start_date} ~ ${record.end_date}`
        },
        {
            title: t('walkforward.table.windows'),
            dataIndex: 'num_windows',
            key: 'num_windows',
            width: 100,
            align: 'center'
        },
        {
            title: t('walkforward.table.status'),
            dataIndex: 'status',
            key: 'status',
            width: 120,
            render: (status) => getStatusTag(status)
        },
        {
            title: t('walkforward.table.trainPerf'),
            dataIndex: 'avg_train_performance',
            key: 'avg_train_performance',
            width: 120,
            align: 'right',
            render: (val) => val == null ? '-' : val.toFixed(4)
        },
        {
            title: t('walkforward.table.testPerf'),
            dataIndex: 'avg_test_performance',
            key: 'avg_test_performance',
            width: 120,
            align: 'right',
            render: (val) => val == null ? '-' : val.toFixed(4)
        },
        {
            title: t('walkforward.table.degradation'),
            dataIndex: 'avg_degradation_pct',
            key: 'avg_degradation_pct',
            width: 120,
            align: 'right',
            render: (val) => val == null ? '-' : `${val.toFixed(2)}%`
        },
        {
            title: t('walkforward.table.overfitting'),
            dataIndex: 'overfitting_detected',
            key: 'overfitting_detected',
            width: 150,
            render: (detected, record) => record.status === 'completed' ? getOverfittingTag(detected) : '-'
        },
        {
            title: t('walkforward.table.actions'),
            key: 'actions',
            width: 150,
            fixed: 'right',
            render: (_, record) => (
                <Space size="small">
                    <Tooltip title={t('walkforward.viewDetail')}>
                        <Button
                            type="link"
                            icon={<EyeOutlined />}
                            onClick={() => handleViewDetail(record)}
                            disabled={record.status !== 'completed'}
                        />
                    </Tooltip>
                    <Tooltip title={t('walkforward.delete')}>
                        <Button
                            type="link"
                            danger
                            icon={<DeleteOutlined />}
                            onClick={() => handleDelete(record)}
                        />
                    </Tooltip>
                </Space>
            )
        }
    ]

    return (
        <div style={{ padding: '24px' }}>
            <Card
                title={t('walkforward.title')}
                extra={
                    <Space>
                        <Button icon={<ReloadOutlined />} onClick={() => loadOptimizations()}>
                            {t('walkforward.refresh')}
                        </Button>
                        <Button
                            type="primary"
                            icon={<PlayCircleOutlined />}
                            onClick={handleStartOptimization}
                        >
                            {t('walkforward.startOptimization')}
                        </Button>
                    </Space>
                }
            >
                <Table
                    columns={columns}
                    dataSource={optimizations}
                    rowKey="optimization_id"
                    loading={loading}
                    pagination={{
                        ...pagination,
                        showSizeChanger: true,
                        showQuickJumper: true,
                        showTotal: (total) => t('walkforward.totalOptimizations', { total })
                    }}
                    onChange={(newPagination) => setPagination(newPagination)}
                    scroll={{ x: 1500 }}
                    locale={{
                        emptyText: (
                            <Empty
                                description={t('walkforward.noData')}
                                image={Empty.PRESENTED_IMAGE_SIMPLE}
                            />
                        )
                    }}
                />
            </Card>

            <WalkForwardConfigModal
                visible={configModalVisible}
                onCancel={() => setConfigModalVisible(false)}
                onSubmit={handleConfigSubmit}
            />

            <WalkForwardDetailModal
                visible={detailModalVisible}
                optimization={selectedOptimization}
                onClose={() => {
                    setDetailModalVisible(false)
                    setSelectedOptimization(null)
                }}
            />
        </div>
    )
}

export default WalkForwardOptimization
