import { useMemo, useState } from 'react'
import { useTranslation } from 'react-i18next'
import ReactECharts from 'echarts-for-react'
import { Card, Empty, Space, Typography, Button, Modal } from 'antd'
import { HeatMapOutlined, FullscreenOutlined } from '@ant-design/icons'

const { Text } = Typography

/**
 * MonthlyReturnsHeatmap - Shows monthly returns as a color-coded heatmap.
 *
 * X-axis: Months (Jan-Dec)
 * Y-axis: Years
 * Color: Green for positive, Red for negative returns
 */
const MonthlyReturnsHeatmap = ({ data }) => {
    const { t } = useTranslation()
    const [isModalVisible, setIsModalVisible] = useState(false)

    const option = useMemo(() => {
        if (!data || !data.years || !data.months || !data.matrix) {
            return null
        }

        const { years, months, matrix } = data

        // Convert matrix to ECharts format: [month_index, year_index, value]
        const chartData = []
        let minVal = 0
        let maxVal = 0

        matrix.forEach((yearData, yearIdx) => {
            yearData.forEach((value, monthIdx) => {
                if (value !== null && value !== undefined) {
                    chartData.push([monthIdx, yearIdx, value])
                    minVal = Math.min(minVal, value)
                    maxVal = Math.max(maxVal, value)
                }
            })
        })

        // Ensure symmetric color scale around 0
        const absMax = Math.max(Math.abs(minVal), Math.abs(maxVal), 0.05)

        return {
            tooltip: {
                position: 'top',
                formatter: (params) => {
                    const [monthIdx, yearIdx, value] = params.data
                    const pct = (value * 100).toFixed(2)
                    return `${years[yearIdx]} ${months[monthIdx]}<br/>${t('deep_analysis.monthly_return')}: ${pct}%`
                }
            },
            grid: {
                left: '12%',
                right: '15%',
                bottom: '15%',
                top: '8%'
            },
            xAxis: {
                type: 'category',
                data: months,
                splitArea: { show: true },
                axisLabel: { fontSize: 11 }
            },
            yAxis: {
                type: 'category',
                data: years.map(String),
                splitArea: { show: true }
            },
            visualMap: {
                min: -absMax,
                max: absMax,
                calculable: true,
                orient: 'vertical',
                right: '3%',
                top: 'center',
                inRange: {
                    color: ['#d73027', '#f46d43', '#fdae61', '#fee08b', '#ffffbf', '#d9ef8b', '#a6d96a', '#66bd63', '#1a9850']
                },
                text: [`+${(absMax * 100).toFixed(0)}%`, `-${(absMax * 100).toFixed(0)}%`],
                textStyle: { color: '#c9d1d9', fontSize: 11 }
            },
            series: [{
                name: t('deep_analysis.monthly_returns'),
                type: 'heatmap',
                data: chartData,
                label: {
                    show: chartData.length <= 60,
                    formatter: (params) => {
                        const val = params.data[2]
                        return val !== null ? `${(val * 100).toFixed(1)}%` : ''
                    },
                    fontSize: 10
                },
                emphasis: {
                    itemStyle: {
                        shadowBlur: 10,
                        shadowColor: 'rgba(0, 0, 0, 0.5)'
                    }
                }
            }]
        }
    }, [data, t])

    if (!data || !data.years?.length) {
        return (
            <Card
                title={
                    <Space>
                        <HeatMapOutlined />
                        {t('deep_analysis.monthly_returns')}
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
                    <HeatMapOutlined />
                    {t('deep_analysis.monthly_returns')}
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
            <ReactECharts
                option={option}
                style={{ height: 300 }}
                opts={{ renderer: 'svg' }}
            />
            <div style={{ textAlign: 'center', marginTop: 8 }}>
                <Text type="secondary" style={{ fontSize: 12 }}>
                    {t('deep_analysis.monthly_returns_hint', 'Green indicates positive returns, red indicates negative returns')}
                </Text>
            </div>
            <Modal
                title={t('deep_analysis.monthly_returns')}
                open={isModalVisible}
                onCancel={() => setIsModalVisible(false)}
                width="90%"
                footer={null}
                centered
            >
                <ReactECharts
                    option={option}
                    style={{ height: 600 }}
                    opts={{ renderer: 'svg' }}
                />
            </Modal>
        </Card>
    )
}

export default MonthlyReturnsHeatmap
