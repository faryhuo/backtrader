import { useMemo } from 'react'
import { useTranslation } from 'react-i18next'
import ReactECharts from 'echarts-for-react'
import { Card, Empty, Space, Statistic, Row, Col, Typography } from 'antd'
import { WarningOutlined } from '@ant-design/icons'

const { Text } = Typography

/**
 * ConsecutiveLossStats - Shows statistics about consecutive losing periods.
 */
const ConsecutiveLossStats = ({ data }) => {
    const { t } = useTranslation()

    const streakDistOption = useMemo(() => {
        if (!data || !data.streaks_distribution) {
            return null
        }

        const { streaks_distribution } = data

        // Sort by streak length
        const entries = Object.entries(streaks_distribution)
            .map(([len, count]) => ({ len: parseInt(len), count }))
            .sort((a, b) => a.len - b.len)

        if (entries.length === 0) return null

        return {
            tooltip: {
                trigger: 'axis',
                axisPointer: { type: 'shadow' },
                formatter: (params) => {
                    const d = params[0]
                    return `${d.name} ${t('deep_analysis.days')}<br/>${t('deep_analysis.occurrences')}: ${d.value}`
                }
            },
            grid: {
                left: '15%',
                right: '10%',
                bottom: '15%',
                top: '10%'
            },
            xAxis: {
                type: 'category',
                data: entries.map(e => e.len.toString()),
                name: t('deep_analysis.streak_length'),
                nameLocation: 'center',
                nameGap: 25
            },
            yAxis: {
                type: 'value',
                name: t('deep_analysis.occurrences'),
                nameLocation: 'center',
                nameGap: 30
            },
            series: [{
                name: t('deep_analysis.consecutive_loss'),
                type: 'bar',
                data: entries.map(e => e.count),
                itemStyle: {
                    color: '#f97316'
                }
            }]
        }
    }, [data, t])

    if (!data) {
        return (
            <Card
                title={
                    <Space>
                        <WarningOutlined />
                        {t('deep_analysis.consecutive_loss')}
                    </Space>
                }
            >
                <Empty description={t('deep_analysis.no_data')} />
            </Card>
        )
    }

    const {
        max_streak = 0,
        max_streak_period,
        max_streak_loss = 0,
        streaks_distribution
    } = data

    const hasStreaks = streaks_distribution && Object.keys(streaks_distribution).length > 0

    return (
        <Card
            title={
                <Space>
                    <WarningOutlined />
                    {t('deep_analysis.consecutive_loss')}
                </Space>
            }
        >
            <Row gutter={[16, 16]}>
                <Col span={12}>
                    <Statistic
                        title={t('deep_analysis.max_streak')}
                        value={max_streak}
                        suffix={t('deep_analysis.days')}
                        valueStyle={{ color: '#ef4444', fontSize: 28 }}
                    />
                </Col>
                <Col span={12}>
                    <Statistic
                        title={t('deep_analysis.max_streak_loss')}
                        value={(max_streak_loss * 100).toFixed(2)}
                        suffix="%"
                        valueStyle={{ color: '#ef4444', fontSize: 28 }}
                    />
                </Col>
            </Row>

            {max_streak_period && (
                <div style={{ marginTop: 12, marginBottom: 12 }}>
                    <Text type="secondary">
                        {t('deep_analysis.period')}: {max_streak_period.start} ~ {max_streak_period.end}
                    </Text>
                </div>
            )}

            {hasStreaks && streakDistOption && (
                <ReactECharts
                    option={streakDistOption}
                    style={{ height: 150 }}
                    opts={{ renderer: 'svg' }}
                />
            )}
        </Card>
    )
}

export default ConsecutiveLossStats
