import React from 'react'
import { useTranslation } from 'react-i18next'
import { Card, Progress, Tag, Space, Typography, Tooltip, Row, Col } from 'antd'
import {
    CheckCircleOutlined,
    WarningOutlined,
    CloseCircleOutlined,
    InfoCircleOutlined
} from '@ant-design/icons'

const { Text, Title } = Typography

/**
 * OverfittingScoreCard - Displays a visual gauge/score card showing overfitting risk
 * 
 * Score interpretation:
 * - 0-30: Low risk (green) - Strategy is robust
 * - 31-60: Medium risk (yellow) - Some overfitting concerns
 * - 61-100: High risk (red) - Significant overfitting detected
 */
const OverfittingScoreCard = ({ overfittingScore }) => {
    const { t } = useTranslation()

    if (!overfittingScore) {
        return null
    }

    const { score, level, factors } = overfittingScore

    // Determine color and icon based on level
    const getLevelConfig = () => {
        switch (level) {
            case 'low':
                return {
                    color: '#52c41a',
                    icon: <CheckCircleOutlined />,
                    tagColor: 'success',
                    gradient: 'linear-gradient(135deg, #52c41a 0%, #73d13d 100%)'
                }
            case 'medium':
                return {
                    color: '#faad14',
                    icon: <WarningOutlined />,
                    tagColor: 'warning',
                    gradient: 'linear-gradient(135deg, #faad14 0%, #ffc53d 100%)'
                }
            case 'high':
                return {
                    color: '#ff4d4f',
                    icon: <CloseCircleOutlined />,
                    tagColor: 'error',
                    gradient: 'linear-gradient(135deg, #ff4d4f 0%, #ff7875 100%)'
                }
            default:
                return {
                    color: '#1890ff',
                    icon: <InfoCircleOutlined />,
                    tagColor: 'processing',
                    gradient: 'linear-gradient(135deg, #1890ff 0%, #40a9ff 100%)'
                }
        }
    }

    const config = getLevelConfig()

    // Factor name translations
    const getFactorName = (factorName) => {
        const factorMap = {
            high_degradation: t('walkforward.analysis.factorHighDegradation', 'High performance degradation'),
            moderate_degradation: t('walkforward.analysis.factorModerateDegradation', 'Moderate performance degradation'),
            mild_degradation: t('walkforward.analysis.factorMildDegradation', 'Mild performance degradation'),
            slight_degradation: t('walkforward.analysis.factorSlightDegradation', 'Slight performance degradation'),
            low_consistency: t('walkforward.analysis.factorLowConsistency', 'Low consistency across windows'),
            poor_consistency: t('walkforward.analysis.factorPoorConsistency', 'Poor consistency across windows'),
            moderate_consistency: t('walkforward.analysis.factorModerateConsistency', 'Moderate consistency issues'),
            negative_correlation: t('walkforward.analysis.factorNegativeCorrelation', 'Negative train/test correlation'),
            weak_correlation: t('walkforward.analysis.factorWeakCorrelation', 'Weak train/test correlation'),
            low_correlation: t('walkforward.analysis.factorLowCorrelation', 'Low train/test correlation'),
            high_volatility: t('walkforward.analysis.factorHighVolatility', 'High degradation volatility'),
            moderate_volatility: t('walkforward.analysis.factorModerateVolatility', 'Moderate degradation volatility'),
        }
        return factorMap[factorName] || factorName
    }

    return (
        <Card
            title={
                <Space>
                    {config.icon}
                    <span>{t('walkforward.analysis.overfittingScore', 'Overfitting Score')}</span>
                </Space>
            }
            style={{ marginBottom: 24 }}
            extra={
                <Tag color={config.tagColor} style={{ fontSize: 14, padding: '4px 12px' }}>
                    {level === 'low' && t('walkforward.analysis.lowRisk', 'Low Risk')}
                    {level === 'medium' && t('walkforward.analysis.mediumRisk', 'Medium Risk')}
                    {level === 'high' && t('walkforward.analysis.highRisk', 'High Risk')}
                </Tag>
            }
        >
            <Row gutter={[24, 16]}>
                <Col xs={24} md={8}>
                    <div style={{ textAlign: 'center' }}>
                        <Progress
                            type="dashboard"
                            percent={score}
                            strokeColor={config.color}
                            format={(percent) => (
                                <div>
                                    <Title level={2} style={{ margin: 0, color: config.color }}>
                                        {percent}
                                    </Title>
                                    <Text type="secondary">{t('walkforward.analysis.outOf100', '/ 100')}</Text>
                                </div>
                            )}
                            size={180}
                        />
                        <div style={{ marginTop: 12 }}>
                            <Text type="secondary">
                                {t('walkforward.analysis.lowerIsBetter', 'Lower score = Lower overfitting risk')}
                            </Text>
                        </div>
                    </div>
                </Col>
                <Col xs={24} md={16}>
                    <Title level={5}>{t('walkforward.analysis.contributingFactors', 'Contributing Factors')}</Title>
                    {factors && factors.length > 0 ? (
                        <Space direction="vertical" style={{ width: '100%' }}>
                            {factors.map((factor, index) => (
                                <div
                                    key={index}
                                    style={{
                                        display: 'flex',
                                        justifyContent: 'space-between',
                                        alignItems: 'center',
                                        padding: '8px 12px',
                                        background: '#fafafa',
                                        borderRadius: 4,
                                        borderLeft: `3px solid ${config.color}`
                                    }}
                                >
                                    <Text>{getFactorName(factor.name)}</Text>
                                    <Space>
                                        <Tooltip title={t('walkforward.analysis.impactScore', 'Impact score')}>
                                            <Tag color={config.tagColor}>+{factor.impact}</Tag>
                                        </Tooltip>
                                        <Text type="secondary">
                                            ({factor.value?.toFixed?.(2) ?? factor.value})
                                        </Text>
                                    </Space>
                                </div>
                            ))}
                        </Space>
                    ) : (
                        <Text type="secondary">
                            {t('walkforward.analysis.noFactors', 'No significant overfitting factors detected')}
                        </Text>
                    )}
                </Col>
            </Row>
        </Card>
    )
}

export default OverfittingScoreCard
