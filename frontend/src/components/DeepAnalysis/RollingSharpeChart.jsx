import React, { useMemo, useRef, useEffect, useState } from 'react'
import { useTranslation } from 'react-i18next'
import { Card, Empty, Space, Tag, Button, Modal } from 'antd'
import { LineChartOutlined, FullscreenOutlined } from '@ant-design/icons'
import { createChart } from 'lightweight-charts'
import ChartControls from './ChartControls'

/**
 * SharpeChart - Reusable Chart Component for Rolling Sharpe Ratio
 */
const SharpeChart = ({ data, visibleSeries, colors, height = 280, t }) => {
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
                borderColor: 'rgba(197, 203, 206, 0.3)'
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

    // Update data
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
                    lineStyle: 2, // Dashed
                    title: key
                })
            }
        })

        // Set Data
        Object.keys(data).forEach(key => {
            const points = data[key].map(d => ({
                time: d.date,
                value: d.value
            }))
            if (seriesRef.current[key]) {
                seriesRef.current[key].setData(points)
            }
        })

        // Visibility
        Object.keys(visibleSeries).forEach(key => {
            if (seriesRef.current[key]) {
                seriesRef.current[key].applyOptions({
                    visible: visibleSeries[key]
                })
            }
        })

        // Add Zero Line (Only once)
        if (!seriesRef.current.zeroLine) {
            const zeroLine = chart.addLineSeries({
                color: '#6b7280',
                lineWidth: 1,
                lineStyle: 1,
                priceLineVisible: false,
                lastValueVisible: false
            })
            seriesRef.current.zeroLine = zeroLine
        }

        const strategyPoints = data.strategy
        if (strategyPoints && strategyPoints.length > 0) {
            seriesRef.current.zeroLine.setData([
                { time: strategyPoints[0].date, value: 0 },
                { time: strategyPoints[strategyPoints.length - 1].date, value: 0 }
            ])
        }

        chart.timeScale().fitContent()

    }, [data, visibleSeries, colors, t])

    return <div ref={chartContainerRef} style={{ height }} />
}

/**
 * RollingSharpeChart - Shows rolling Sharpe ratio over time with benchmark comparison.
 */
const RollingSharpeChart = ({ data }) => {
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
        if (!data) return null

        const fullStrategy = data.strategy || []
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

        const keys = ['strategy', 'SPY', '000300.SS']
        keys.forEach(key => {
            const points = data[key] || []
            // Filter points
            let filtered = points.filter(p => p.date >= startStr)

            result[key] = filtered
        })

        return result
    }, [data, timeRange])


    if (!data || !data.strategy?.length) {
        return (
            <Card
                title={
                    <Space>
                        <LineChartOutlined />
                        {t('deep_analysis.rolling_sharpe')}
                    </Space>
                }
            >
                <Empty description={t('deep_analysis.no_data')} />
            </Card>
        )
    }

    const windowDays = data.window || 60

    const seriesOptions = [
        { key: 'strategy', label: t('deep_analysis.strategy'), color: seriesColors.strategy, visible: visibleSeries.strategy },
        ...(data.SPY?.length ? [{ key: 'SPY', label: 'SPY', color: seriesColors.SPY, visible: visibleSeries.SPY }] : []),
        ...(data['000300.SS']?.length ? [{ key: '000300.SS', label: 'HS300', color: seriesColors['000300.SS'], visible: visibleSeries['000300.SS'] }] : [])
    ]

    return (
        <>
            <Card
                title={
                    <Space>
                        <LineChartOutlined />
                        {t('deep_analysis.rolling_sharpe')}
                        <Tag color="blue">{t('deep_analysis.window_days', { days: windowDays })}</Tag>
                    </Space>
                }
                extra={
                    <Space size="small">
                        <Button
                            type="text"
                            icon={<FullscreenOutlined />}
                            onClick={() => setIsModalVisible(true)}
                        />
                    </Space>
                }
            >
                <ChartControls
                    selectedRange={timeRange}
                    onRangeChange={setTimeRange}
                    series={seriesOptions}
                    onSeriesToggle={(key, val) => setVisibleSeries(prev => ({ ...prev, [key]: val }))}
                />
                <SharpeChart
                    data={filteredData}
                    visibleSeries={visibleSeries}
                    colors={seriesColors}
                    height={280}
                    t={t}
                />
            </Card>
            <Modal
                title={
                    <Space>
                        <LineChartOutlined />
                        {t('deep_analysis.rolling_sharpe')}
                        <Tag color="blue">{t('deep_analysis.window_days', { days: windowDays })}</Tag>
                    </Space>
                }
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
                    <SharpeChart
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

export default RollingSharpeChart

