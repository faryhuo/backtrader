import React from 'react'
import { useTranslation } from 'react-i18next'
import { Card, Table, Progress, Tag, Space, Typography } from 'antd'
import { BarChartOutlined } from '@ant-design/icons'

const { Text } = Typography

/**
 * ParameterSensitivityTable - Displays parameter sensitivity ranking
 * 
 * Shows which parameters have the most impact on performance
 */
const ParameterSensitivityTable = ({ sensitivityRanking }) => {
    const { t } = useTranslation()

    if (!sensitivityRanking || sensitivityRanking.length === 0) {
        return null
    }

    const columns = [
        {
            title: t('walkforward.analysis.rank', 'Rank'),
            dataIndex: 'rank',
            key: 'rank',
            width: 80,
            render: (_, __, index) => (
                <Tag color={index === 0 ? 'gold' : index === 1 ? 'silver' : 'default'}>
                    #{index + 1}
                </Tag>
            )
        },
        {
            title: t('walkforward.analysis.parameter', 'Parameter'),
            dataIndex: 'param',
            key: 'param',
            render: (param) => <Text code>{param}</Text>
        },
        {
            title: t('walkforward.analysis.sensitivityScore', 'Sensitivity Score'),
            dataIndex: 'score',
            key: 'score',
            width: 300,
            render: (score) => (
                <Space>
                    <Progress
                        percent={score}
                        size="small"
                        style={{ width: 150 }}
                        strokeColor={{
                            '0%': '#108ee9',
                            '100%': score > 70 ? '#ff4d4f' : score > 40 ? '#faad14' : '#52c41a'
                        }}
                        showInfo={false}
                    />
                    <Text>{score.toFixed(1)}%</Text>
                </Space>
            )
        },
        {
            title: t('walkforward.analysis.impact', 'Impact Level'),
            key: 'impact',
            width: 120,
            render: (_, record) => {
                const score = record.score
                if (score > 70) {
                    return <Tag color="red">{t('walkforward.analysis.highImpact', 'High')}</Tag>
                } else if (score > 40) {
                    return <Tag color="orange">{t('walkforward.analysis.mediumImpact', 'Medium')}</Tag>
                } else {
                    return <Tag color="green">{t('walkforward.analysis.lowImpact', 'Low')}</Tag>
                }
            }
        }
    ]

    return (
        <Card
            title={
                <Space>
                    <BarChartOutlined />
                    {t('walkforward.analysis.sensitivityRanking', 'Parameter Sensitivity Ranking')}
                </Space>
            }
            style={{ marginBottom: 24 }}
        >
            <Table
                columns={columns}
                dataSource={sensitivityRanking.map((item, index) => ({
                    ...item,
                    key: item.param || index
                }))}
                pagination={false}
                size="middle"
            />
            <div style={{ marginTop: 12 }}>
                <Text type="secondary">
                    {t('walkforward.analysis.sensitivityHint',
                        'Higher sensitivity means varying this parameter has a larger impact on strategy performance. Focus optimization efforts on high-sensitivity parameters.'
                    )}
                </Text>
            </div>
        </Card>
    )
}

export default ParameterSensitivityTable
