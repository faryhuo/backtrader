import { useMemo } from 'react'
import { useTranslation } from 'react-i18next'
import ReactECharts from 'echarts-for-react'
import { Card, Empty, Typography, Tag, Space } from 'antd'
import { HeatMapOutlined } from '@ant-design/icons'

const { Text } = Typography

/**
 * ParameterHeatmap - 2D heatmap showing parameter space with color-coded performance
 * 
 * X-axis: Parameter 1 values
 * Y-axis: Parameter 2 values
 * Color intensity: Performance metric value
 */
const ParameterHeatmap = ({ heatmapData, metricName = 'sharpe_ratio' }) => {
    const { t } = useTranslation()

    // Check if we have meaningful data (more than 1 point for heatmap)
    const hasInsufficientData = useMemo(() => {
        if (!heatmapData) return true
        if (heatmapData.type === 'line') {
            return !heatmapData.data_points || heatmapData.data_points.length < 2
        }
        // For 2D heatmap, need at least 2 values on one axis
        return (
            !heatmapData.x_values ||
            !heatmapData.y_values ||
            (heatmapData.x_values.length < 2 && heatmapData.y_values.length < 2)
        )
    }, [heatmapData])

    const option = useMemo(() => {
        if (!heatmapData || !heatmapData.x_values || !heatmapData.y_values || !heatmapData.matrix) {
            return null
        }

        // Handle 1D case (line chart)
        if (heatmapData.type === 'line') {
            const dataPoints = heatmapData.data_points || []
            return {
                tooltip: {
                    trigger: 'axis',
                    formatter: (params) => {
                        const data = params[0]
                        return `${heatmapData.param_name}: ${data.name}<br/>${metricName}: ${data.value.toFixed(4)}`
                    }
                },
                xAxis: {
                    type: 'category',
                    name: heatmapData.param_name,
                    data: dataPoints.map(d => String(d.param_value)),
                    axisLabel: { rotate: 45 }
                },
                yAxis: {
                    type: 'value',
                    name: metricName
                },
                series: [{
                    type: 'line',
                    data: dataPoints.map(d => d.metric_value),
                    smooth: true,
                    areaStyle: {
                        opacity: 0.3
                    },
                    lineStyle: {
                        width: 3
                    },
                    markPoint: {
                        data: [
                            { type: 'max', name: 'Max' },
                            { type: 'min', name: 'Min' }
                        ]
                    }
                }],
                grid: {
                    left: '10%',
                    right: '10%',
                    bottom: '15%',
                    top: '10%'
                }
            }
        }

        // 2D Heatmap case
        const { x_values, y_values, matrix, min_value, max_value, optimal, x_param, y_param } = heatmapData

        // Convert matrix to ECharts format: [x_index, y_index, value]
        const data = []
        matrix.forEach((row, yIndex) => {
            row.forEach((value, xIndex) => {
                if (value !== null) {
                    data.push([xIndex, yIndex, value])
                }
            })
        })

        return {
            tooltip: {
                position: 'top',
                formatter: (params) => {
                    const [xIdx, yIdx, value] = params.data
                    return `${x_param}: ${x_values[xIdx]}<br/>${y_param}: ${y_values[yIdx]}<br/>${metricName}: ${value?.toFixed?.(4) ?? value}`
                }
            },
            grid: {
                left: '15%',
                right: '15%',
                bottom: '20%',
                top: '10%'
            },
            xAxis: {
                type: 'category',
                data: x_values,
                name: x_param,
                nameLocation: 'center',
                nameGap: 35,
                splitArea: { show: true },
                axisLabel: { rotate: 45 }
            },
            yAxis: {
                type: 'category',
                data: y_values,
                name: y_param,
                nameLocation: 'center',
                nameGap: 50,
                splitArea: { show: true }
            },
            visualMap: {
                min: min_value,
                max: max_value,
                calculable: true,
                orient: 'vertical',
                right: '5%',
                top: 'center',
                inRange: {
                    color: ['#313695', '#4575b4', '#74add1', '#abd9e9', '#e0f3f8', '#ffffbf', '#fee090', '#fdae61', '#f46d43', '#d73027', '#a50026']
                },
                text: [t('walkforward.analysis.high', 'High'), t('walkforward.analysis.low', 'Low')],
                textStyle: { color: '#333' }
            },
            series: [{
                name: metricName,
                type: 'heatmap',
                data: data,
                label: {
                    show: data.length <= 25,
                    formatter: (params) => params.data[2]?.toFixed?.(2) ?? ''
                },
                emphasis: {
                    itemStyle: {
                        shadowBlur: 10,
                        shadowColor: 'rgba(0, 0, 0, 0.5)'
                    }
                },
                markPoint: optimal ? {
                    data: [{
                        coord: [
                            x_values.indexOf(String(optimal.param1)),
                            y_values.indexOf(String(optimal.param2))
                        ],
                        symbol: 'pin',
                        symbolSize: 40,
                        itemStyle: { color: '#52c41a' },
                        label: {
                            show: true,
                            formatter: '★',
                            fontSize: 16,
                            color: '#fff'
                        }
                    }]
                } : undefined
            }]
        }
    }, [heatmapData, metricName, t])

    // Show empty state if no data or insufficient data for visualization
    if (!heatmapData || (!heatmapData.x_values?.length && !heatmapData.data_points?.length) || hasInsufficientData) {
        return (
            <Card title={
                <Space>
                    <HeatMapOutlined />
                    {t('walkforward.analysis.parameterHeatmap', 'Parameter Heatmap')}
                </Space>
            }>
                <Empty
                    description={
                        <Space direction="vertical" align="center">
                            <Text type="secondary">
                                {t('walkforward.analysis.noHeatmapData', 'Insufficient parameter data for heatmap')}
                            </Text>
                            <Text type="secondary" style={{ fontSize: 12 }}>
                                {t('walkforward.analysis.rerunOptimization', 'Re-run optimization to generate full parameter analysis data')}
                            </Text>
                        </Space>
                    }
                />
            </Card>
        )
    }

    const isLineChart = heatmapData.type === 'line'


    return (
        <Card
            title={
                <Space>
                    <HeatMapOutlined />
                    {isLineChart
                        ? t('walkforward.analysis.parameterSensitivity', 'Parameter Sensitivity')
                        : t('walkforward.analysis.parameterHeatmap', 'Parameter Heatmap')}
                </Space>
            }
            extra={
                heatmapData.optimal && (
                    <Tag color="green">
                        {t('walkforward.analysis.optimal', 'Optimal')}:
                        {heatmapData.optimal.param1_name}={heatmapData.optimal.param1},
                        {heatmapData.optimal.param2_name}={heatmapData.optimal.param2}
                    </Tag>
                )
            }
            style={{ marginBottom: 24 }}
        >
            <ReactECharts
                option={option}
                style={{ height: 400 }}
                opts={{ renderer: 'svg' }}
            />
            {!isLineChart && (
                <div style={{ textAlign: 'center', marginTop: 12 }}>
                    <Text type="secondary">
                        {t('walkforward.analysis.heatmapHint', 'Darker colors indicate higher metric values. ★ marks the optimal combination.')}
                    </Text>
                </div>
            )}
        </Card>
    )
}

export default ParameterHeatmap
