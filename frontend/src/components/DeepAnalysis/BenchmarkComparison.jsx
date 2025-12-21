import React, { useMemo, useRef, useEffect, useState } from 'react'
import { useTranslation } from 'react-i18next'
import { Card, Empty, Space, Row, Col, Table, Typography, Tag, Button, Modal } from 'antd'
import { SwapOutlined, FullscreenOutlined } from '@ant-design/icons'
import { createChart } from 'lightweight-charts'
import ChartControls from './ChartControls'

const { Text } = Typography

/**
 * BenchmarkChart - Reusable Chart Component for Benchmark Comparison
 */
const BenchmarkChart = ({ data, visibleSeries, colors, height = 300, t }) => {
    const chartContainerRef = useRef(null)
    const chartRef = useRef(null)
    const seriesRef = useRef({})

    useEffect(() => {
        if (!chartContainerRef.current) return

        // Create chart
        const chart = createChart(chartContainerRef.current, {
            width: chartContainerRef.current.clientWidth,
            height: height,
            layout: {
                background: { type: 'solid', color: 'transparent' },
                textColor: '#c9d1d9'
            },
            grid: {
                vertLines: { color: 'rgba(197, 203, 206, 0.1)' },
                horzLines: { color: 'rgba(197, 203, 206, 0.1)' }
            },
            rightPriceScale: {
                borderColor: 'rgba(197, 203, 206, 0.3)',
                scaleMargins: {
                    top: 0.1,
                    bottom: 0.1,
                },
            },
            timeScale: {
                borderColor: 'rgba(197, 203, 206, 0.3)',
                timeVisible: true,
                secondsVisible: false
            },
            crosshair: {
                mode: 1,
                vertLine: {
                    width: 1,
                    color: 'rgba(224, 227, 235, 0.1)',
                    style: 0,
                },
                horzLine: {
                    visible: false,
                    labelVisible: false,
                },
            }
        })

        chartRef.current = chart
        seriesRef.current = {}

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
    }, [height])

    // Update data and visibility
    useEffect(() => {
        if (!chartRef.current || !data) return

        const chart = chartRef.current

        // Strategy Series
        if (!seriesRef.current.strategy) {
            seriesRef.current.strategy = chart.addLineSeries({
                color: colors.strategy,
                lineWidth: 2,
                title: t('deep_analysis.strategy')
            })
        }

        // Benchmark Series
        ['SPY', '000300.SS'].forEach(key => {
            if (!seriesRef.current[key]) {
                seriesRef.current[key] = chart.addLineSeries({
                    color: colors[key],
                    lineWidth: 1,
                    lineStyle: 2,
                    title: key
                })
            }
        })

        // Set Data
        Object.keys(data).forEach(key => {
            const series = seriesRef.current[key]
            if (series) {
                const points = data[key].map(d => ({
                    time: d.date,
                    value: d.value * 100
                }))
                series.setData(points)
            }
        })

        // Update Visibility
        Object.keys(visibleSeries).forEach(key => {
            if (seriesRef.current[key]) {
                seriesRef.current[key].applyOptions({
                    visible: visibleSeries[key]
                })
            }
        })

        chart.timeScale().fitContent()

    }, [data, visibleSeries, colors, t])

    return <div ref={chartContainerRef} style={{ height }} />
}

/**
 * BenchmarkComparison - Shows cumulative returns chart and comparison metrics table.
 */
const BenchmarkComparison = ({ data }) => {
    const { t } = useTranslation()
    const [timeRange, setTimeRange] = useState('ALL')
    const [isModalVisible, setIsModalVisible] = useState(false)
    const [visibleSeries, setVisibleSeries] = useState({
        strategy: true,
        SPY: true,
        '000300.SS': true
    })

    const seriesColors = useMemo(() => ({
        strategy: '#3b82f6',
        SPY: '#f59e0b',
        '000300.SS': '#ef4444'
    }), [])

    // Filter data based on time range
    const filteredData = useMemo(() => {
        if (!data?.cumulative_returns) return null

        const fullStrategy = data.cumulative_returns.strategy || []
        if (fullStrategy.length === 0) return null

        const endDate = new Date(fullStrategy[fullStrategy.length - 1].date)
        let startDate = new Date(fullStrategy[0].date)

        if (timeRange !== 'ALL') {
            const now = new Date(endDate)
            switch (timeRange) {
                case '1M': now.setMonth(now.getMonth() - 1); break
                case '3M': now.setMonth(now.getMonth() - 3); break
                case '6M': now.setMonth(now.getMonth() - 6); break
                case '1Y': now.setFullYear(now.getFullYear() - 1); break
                case 'YTD': now.setMonth(0, 1); break
                default: break
            }
            if (now > startDate) startDate = now
        }

        const startStr = startDate.toISOString().split('T')[0]
        const result = {}

        Object.keys(data.cumulative_returns).forEach(key => {
            const points = data.cumulative_returns[key] || []
            // Filter points
            let filtered = points.filter(p => p.date >= startStr)

            // Rebase to 0 at start
            if (filtered.length > 0) {
                const baseVal = filtered[0].value
                filtered = filtered.map(p => ({
                    date: p.date,
                    value: p.value - baseVal
                }))
            }
            result[key] = filtered
        })

        return result

    }, [data, timeRange])

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

    const seriesOptions = [
        { key: 'strategy', label: t('deep_analysis.strategy'), color: seriesColors.strategy, visible: visibleSeries.strategy },
        ...(data.cumulative_returns?.SPY?.length ? [{ key: 'SPY', label: 'SPY', color: seriesColors.SPY, visible: visibleSeries.SPY }] : []),
        ...(data.cumulative_returns?.['000300.SS']?.length ? [{ key: '000300.SS', label: 'HS300', color: seriesColors['000300.SS'], visible: visibleSeries['000300.SS'] }] : [])
    ]

    return (
        <>
            <Card
                title={
                    <Space>
                        <SwapOutlined />
                        {t('deep_analysis.benchmark_comparison')}
                    </Space>
                }
                extra={
                    <Button
                        type="text"
                        icon={<FullscreenOutlined />}
                        onClick={() => setIsModalVisible(true)}
                    />
                }
            >
                <ChartControls
                    selectedRange={timeRange}
                    onRangeChange={setTimeRange}
                    series={seriesOptions}
                    onSeriesToggle={(key, val) => setVisibleSeries(prev => ({ ...prev, [key]: val }))}
                />

                <Row gutter={24}>
                    <Col xs={24} lg={14}>
                        <BenchmarkChart
                            data={filteredData}
                            visibleSeries={visibleSeries}
                            colors={seriesColors}
                            height={300}
                            t={t}
                        />
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

            <Modal
                title={t('deep_analysis.benchmark_comparison')}
                open={isModalVisible}
                onCancel={() => setIsModalVisible(false)}
                width="90%"
                footer={null}
                style={{ top: 20 }}
                destroyOnClose
            >
                <ChartControls
                    selectedRange={timeRange}
                    onRangeChange={setTimeRange}
                    series={seriesOptions}
                    onSeriesToggle={(key, val) => setVisibleSeries(prev => ({ ...prev, [key]: val }))}
                />
                <div style={{ marginTop: 16 }}>
                    <BenchmarkChart
                        data={filteredData}
                        visibleSeries={visibleSeries}
                        colors={seriesColors}
                        height={600}
                        t={t}
                    />
                </div>
            </Modal>
        </>
    )
}

export default BenchmarkComparison

