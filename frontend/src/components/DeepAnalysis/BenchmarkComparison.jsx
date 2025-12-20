import React, { useMemo, useRef, useEffect } from 'react'
import { useTranslation } from 'react-i18next'
import { Card, Empty, Space, Row, Col, Table, Typography, Tag } from 'antd'
import { SwapOutlined } from '@ant-design/icons'
import { createChart } from 'lightweight-charts'

const { Text } = Typography

/**
 * BenchmarkComparison - Shows cumulative returns chart and comparison metrics table.
 */
const BenchmarkComparison = ({ data }) => {
    const { t } = useTranslation()
    const chartContainerRef = useRef(null)
    const chartRef = useRef(null)

    const seriesColors = useMemo(() => ({
        strategy: '#3b82f6',
        SPY: '#f59e0b',
        '000300.SS': '#ef4444'
    }), [])

    useEffect(() => {
        if (!chartContainerRef.current || !data?.cumulative_returns?.strategy?.length) {
            return
        }

        // Create chart
        const chart = createChart(chartContainerRef.current, {
            width: chartContainerRef.current.clientWidth,
            height: 300,
            layout: {
                background: { type: 'solid', color: 'transparent' },
                textColor: '#c9d1d9'
            },
            grid: {
                vertLines: { color: 'rgba(197, 203, 206, 0.1)' },
                horzLines: { color: 'rgba(197, 203, 206, 0.1)' }
            },
            rightPriceScale: {
                borderColor: 'rgba(197, 203, 206, 0.3)'
            },
            timeScale: {
                borderColor: 'rgba(197, 203, 206, 0.3)',
                timeVisible: true,
                secondsVisible: false
            },
            crosshair: {
                mode: 1
            }
        })

        chartRef.current = chart
        const { cumulative_returns } = data

        // Add lines for each series
        Object.entries(cumulative_returns).forEach(([key, points]) => {
            if (!points || points.length === 0) return

            const seriesData = points.map(d => ({
                time: d.date,
                value: d.value * 100 // Convert to percentage
            }))

            const series = chart.addLineSeries({
                color: seriesColors[key] || '#888',
                lineWidth: key === 'strategy' ? 2 : 1,
                lineStyle: key === 'strategy' ? 0 : 2,
                title: key === 'strategy' ? t('deep_analysis.strategy') : key
            })
            series.setData(seriesData)
        })

        // Add zero line
        const strategyData = cumulative_returns.strategy
        if (strategyData?.length) {
            const zeroLine = chart.addLineSeries({
                color: '#6b7280',
                lineWidth: 1,
                lineStyle: 1,
                priceLineVisible: false,
                lastValueVisible: false
            })
            zeroLine.setData([
                { time: strategyData[0].date, value: 0 },
                { time: strategyData[strategyData.length - 1].date, value: 0 }
            ])
        }

        chart.timeScale().fitContent()

        // Handle resize
        const handleResize = () => {
            if (chartContainerRef.current) {
                chart.applyOptions({ width: chartContainerRef.current.clientWidth })
            }
        }

        window.addEventListener('resize', handleResize)

        return () => {
            window.removeEventListener('resize', handleResize)
            chart.remove()
        }
    }, [data, seriesColors, t])

    // Build comparison table data
    const tableData = useMemo(() => {
        if (!data) return []

        const benchmarks = Object.keys(data.correlation || {})
        return benchmarks.map(ticker => ({
            key: ticker,
            ticker,
            correlation: data.correlation?.[ticker],
            beta: data.beta?.[ticker],
            alpha: data.alpha?.[ticker],
            information_ratio: data.information_ratio?.[ticker],
            tracking_error: data.tracking_error?.[ticker]
        }))
    }, [data])

    const columns = useMemo(() => [
        {
            title: t('deep_analysis.benchmark'),
            dataIndex: 'ticker',
            key: 'ticker',
            render: (val) => (
                <Tag color={seriesColors[val] || 'default'}>{val}</Tag>
            )
        },
        {
            title: t('deep_analysis.correlation'),
            dataIndex: 'correlation',
            key: 'correlation',
            render: (val) => val?.toFixed(4) ?? 'N/A'
        },
        {
            title: t('deep_analysis.beta'),
            dataIndex: 'beta',
            key: 'beta',
            render: (val) => val?.toFixed(4) ?? 'N/A'
        },
        {
            title: t('deep_analysis.alpha'),
            dataIndex: 'alpha',
            key: 'alpha',
            render: (val) => val !== undefined ? (
                <Text type={val >= 0 ? 'success' : 'danger'}>
                    {(val * 100).toFixed(2)}%
                </Text>
            ) : 'N/A'
        },
        {
            title: t('deep_analysis.information_ratio'),
            dataIndex: 'information_ratio',
            key: 'information_ratio',
            render: (val) => val?.toFixed(4) ?? 'N/A'
        },
        {
            title: t('deep_analysis.tracking_error'),
            dataIndex: 'tracking_error',
            key: 'tracking_error',
            render: (val) => val !== undefined ? `${(val * 100).toFixed(2)}%` : 'N/A'
        }
    ], [t, seriesColors])

    if (!data || !data.cumulative_returns?.strategy?.length) {
        return (
            <Card
                title={
                    <Space>
                        <SwapOutlined />
                        {t('deep_analysis.benchmark_comparison')}
                    </Space>
                }
            >
                <Empty description={t('deep_analysis.no_data')} />
            </Card>
        )
    }

    return (
        <Card
            title={
                <Space>
                    <SwapOutlined />
                    {t('deep_analysis.benchmark_comparison')}
                </Space>
            }
            extra={
                <Space size="small">
                    <Tag color="#3b82f6">{t('deep_analysis.strategy')}</Tag>
                    {data.cumulative_returns?.SPY?.length > 0 && <Tag color="#f59e0b">SPY</Tag>}
                    {data.cumulative_returns?.['000300.SS']?.length > 0 && <Tag color="#ef4444">HS300</Tag>}
                </Space>
            }
        >
            <Row gutter={24}>
                <Col xs={24} lg={14}>
                    <Text strong style={{ marginBottom: 8, display: 'block' }}>
                        {t('deep_analysis.cumulative_returns')}
                    </Text>
                    <div ref={chartContainerRef} style={{ height: 300 }} />
                </Col>
                <Col xs={24} lg={10}>
                    <Text strong style={{ marginBottom: 8, display: 'block' }}>
                        {t('deep_analysis.benchmark_metrics')}
                    </Text>
                    <Table
                        dataSource={tableData}
                        columns={columns}
                        size="small"
                        pagination={false}
                    />
                    <div style={{ marginTop: 12 }}>
                        <Text type="secondary" style={{ fontSize: 11 }}>
                            {t('deep_analysis.alpha_note', 'Alpha is annualized. Positive alpha indicates outperformance vs benchmark.')}
                        </Text>
                    </div>
                </Col>
            </Row>
        </Card>
    )
}

export default BenchmarkComparison
