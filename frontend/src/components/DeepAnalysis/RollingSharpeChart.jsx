import React, { useMemo, useRef, useEffect } from 'react'
import { useTranslation } from 'react-i18next'
import { Card, Empty, Space, Tag } from 'antd'
import { LineChartOutlined } from '@ant-design/icons'
import { createChart } from 'lightweight-charts'

/**
 * RollingSharpeChart - Shows rolling Sharpe ratio over time with benchmark comparison.
 */
const RollingSharpeChart = ({ data }) => {
    const { t } = useTranslation()
    const chartContainerRef = useRef(null)
    const chartRef = useRef(null)

    const seriesColors = useMemo(() => ({
        strategy: '#3b82f6',
        SPY: '#f59e0b',
        '000300.SS': '#ef4444'
    }), [])

    useEffect(() => {
        if (!chartContainerRef.current || !data || !data.strategy?.length) {
            return
        }

        // Create chart
        const chart = createChart(chartContainerRef.current, {
            width: chartContainerRef.current.clientWidth,
            height: 280,
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

        // Add strategy line
        const strategyData = data.strategy.map(d => ({
            time: d.date,
            value: d.value
        }))

        const strategySeries = chart.addLineSeries({
            color: seriesColors.strategy,
            lineWidth: 2,
            title: t('deep_analysis.strategy')
        })
        strategySeries.setData(strategyData)

        // Add benchmark lines
        Object.keys(data).forEach(key => {
            if (key === 'strategy' || key === 'window') return
            if (!data[key] || !data[key].length) return

            const benchData = data[key].map(d => ({
                time: d.date,
                value: d.value
            }))

            const series = chart.addLineSeries({
                color: seriesColors[key] || '#888',
                lineWidth: 1,
                lineStyle: 2, // Dashed
                title: key
            })
            series.setData(benchData)
        })

        // Add zero line
        const zeroLine = chart.addLineSeries({
            color: '#6b7280',
            lineWidth: 1,
            lineStyle: 1,
            priceLineVisible: false,
            lastValueVisible: false
        })

        if (strategyData.length > 0) {
            zeroLine.setData([
                { time: strategyData[0].time, value: 0 },
                { time: strategyData[strategyData.length - 1].time, value: 0 }
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

    return (
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
                    <Tag color="#3b82f6">{t('deep_analysis.strategy')}</Tag>
                    {data.SPY?.length > 0 && <Tag color="#f59e0b">SPY</Tag>}
                    {data['000300.SS']?.length > 0 && <Tag color="#ef4444">HS300</Tag>}
                </Space>
            }
        >
            <div ref={chartContainerRef} style={{ height: 280 }} />
        </Card>
    )
}

export default RollingSharpeChart
