import React, { useMemo } from 'react'
import { useTranslation } from 'react-i18next'
import ReactECharts from 'echarts-for-react'
import 'echarts-gl'
import { Card, Empty, Typography, Space } from 'antd'
import { AreaChartOutlined } from '@ant-design/icons'

const { Text } = Typography

/**
 * Parameter3DSurface - 3D surface plot for visualizing the performance landscape
 * 
 * X/Y axes: Two parameters
 * Z-axis: Performance metric
 * Rotatable/zoomable view with color gradient overlay
 */
const Parameter3DSurface = ({ surfaceData, metricName = 'sharpe_ratio' }) => {
    const { t } = useTranslation()

    const option = useMemo(() => {
        if (!surfaceData || !surfaceData.x_values || !surfaceData.y_values || !surfaceData.matrix) {
            return null
        }

        // Only show 3D surface for 2-parameter grids
        if (surfaceData.type === 'line') {
            return null
        }

        const { x_values, y_values, matrix, min_value, max_value, x_param, y_param } = surfaceData

        // Convert to 3D surface data format
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
                formatter: (params) => {
                    if (!params.data) return ''
                    const [xIdx, yIdx, value] = params.data
                    return `${x_param}: ${x_values[xIdx]}<br/>${y_param}: ${y_values[yIdx]}<br/>${metricName}: ${value?.toFixed?.(4) ?? value}`
                }
            },
            visualMap: {
                show: true,
                dimension: 2,
                min: min_value,
                max: max_value,
                inRange: {
                    color: ['#313695', '#4575b4', '#74add1', '#abd9e9', '#e0f3f8', '#ffffbf', '#fee090', '#fdae61', '#f46d43', '#d73027', '#a50026']
                },
                right: 10,
                top: 'center',
                text: [t('walkforward.analysis.high', 'High'), t('walkforward.analysis.low', 'Low')],
                textStyle: { color: '#333' }
            },
            xAxis3D: {
                type: 'category',
                data: x_values,
                name: x_param,
                nameTextStyle: { fontSize: 12 }
            },
            yAxis3D: {
                type: 'category',
                data: y_values,
                name: y_param,
                nameTextStyle: { fontSize: 12 }
            },
            zAxis3D: {
                type: 'value',
                name: metricName,
                nameTextStyle: { fontSize: 12 }
            },
            grid3D: {
                viewControl: {
                    projection: 'perspective',
                    autoRotate: false,
                    distance: 200,
                    alpha: 25,
                    beta: 40
                },
                light: {
                    main: {
                        intensity: 1.2,
                        shadow: true
                    },
                    ambient: {
                        intensity: 0.3
                    }
                },
                boxWidth: 100,
                boxHeight: 60,
                boxDepth: 100
            },
            series: [{
                type: 'surface',
                wireframe: {
                    show: true,
                    lineStyle: {
                        opacity: 0.3,
                        width: 1
                    }
                },
                shading: 'realistic',
                realisticMaterial: {
                    roughness: 0.5,
                    metalness: 0
                },
                data: data.map(([x, y, z]) => [x, y, z]),
                itemStyle: {
                    opacity: 0.9
                },
                emphasis: {
                    itemStyle: {
                        opacity: 1
                    }
                }
            }]
        }
    }, [surfaceData, metricName, t])

    // Check for insufficient data - need at least 2 values on both axes for 3D surface
    const hasInsufficientData = useMemo(() => {
        if (!surfaceData) return true
        if (surfaceData.type === 'line') return true
        return (
            !surfaceData.x_values?.length ||
            !surfaceData.y_values?.length ||
            surfaceData.x_values.length < 2 ||
            surfaceData.y_values.length < 2
        )
    }, [surfaceData])

    // Don't show for single parameter (line chart case) or insufficient data
    if (!surfaceData || surfaceData.type === 'line') {
        return null
    }

    if (hasInsufficientData || !option) {
        return (
            <Card title={
                <Space>
                    <AreaChartOutlined />
                    {t('walkforward.analysis.surface3d', '3D Surface')}
                </Space>
            }>
                <Empty
                    description={
                        <Space direction="vertical" align="center">
                            <Text type="secondary">
                                {t('walkforward.analysis.no3dData', 'Insufficient parameter data for 3D surface')}
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


    return (
        <Card
            title={
                <Space>
                    <AreaChartOutlined />
                    {t('walkforward.analysis.surface3d', '3D Surface')}
                </Space>
            }
            style={{ marginBottom: 24 }}
        >
            <ReactECharts
                option={option}
                style={{ height: 500 }}
                opts={{ renderer: 'canvas' }}
            />
            <div style={{ textAlign: 'center', marginTop: 12 }}>
                <Text type="secondary">
                    {t('walkforward.analysis.surface3dHint', 'Drag to rotate, scroll to zoom. Peaks represent optimal parameter combinations.')}
                </Text>
            </div>
        </Card>
    )
}

export default Parameter3DSurface
