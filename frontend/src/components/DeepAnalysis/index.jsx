import { useState, useEffect, useCallback } from 'react'
import { useTranslation } from 'react-i18next'
import { Spin, Alert, Row, Col, Divider } from 'antd'
import { api } from '../../services/api'
import MonthlyReturnsHeatmap from './MonthlyReturnsHeatmap'
import RollingSharpeChart from './RollingSharpeChart'
import ReturnsDistribution from './ReturnsDistribution'
import DrawdownDistribution from './DrawdownDistribution'
import ConsecutiveLossStats from './ConsecutiveLossStats'
import BenchmarkComparison from './BenchmarkComparison'

/**
 * DeepAnalysis - Main container for deep backtest analysis visualizations.
 *
 * Props:
 *   backtest: Backtest object with backtest_id and other details
 */
const DeepAnalysis = ({ backtest }) => {
    const { t } = useTranslation()
    const [loading, setLoading] = useState(false)
    const [error, setError] = useState(null)
    const [analysisData, setAnalysisData] = useState(null)

    const loadDeepAnalysis = useCallback(async () => {
        setLoading(true)
        setError(null)

        try {
            const data = await api.getDeepAnalysis(backtest.backtest_id)
            if (data.status === 'ok') {
                setAnalysisData(data)
            } else {
                setError(data.detail || t('deep_analysis.error'))
            }
        } catch (err) {
            console.error('Failed to load deep analysis:', err)
            setError(err.message || t('deep_analysis.error'))
        } finally {
            setLoading(false)
        }
    }, [backtest?.backtest_id, t])

    useEffect(() => {
        if (backtest?.backtest_id) {
            loadDeepAnalysis()
        }
    }, [backtest?.backtest_id, loadDeepAnalysis])

    if (loading) {
        return (
            <div style={{ textAlign: 'center', padding: '60px 0' }}>
                <Spin size="large" />
                <div style={{ marginTop: 16, color: '#888' }}>
                    {t('deep_analysis.loading')}
                </div>
            </div>
        )
    }

    if (error) {
        return (
            <Alert
                type="warning"
                showIcon
                message={t('deep_analysis.error')}
                description={error}
                style={{ margin: 20 }}
            />
        )
    }

    if (!analysisData) {
        return (
            <Alert
                type="info"
                showIcon
                message={t('deep_analysis.no_data')}
                style={{ margin: 20 }}
            />
        )
    }

    return (
        <div style={{ padding: '20px' }}>
            {/* Row 1: Monthly Returns Heatmap + Consecutive Loss Stats */}
            <Row gutter={[24, 24]}>
                <Col xs={24} lg={16}>
                    <MonthlyReturnsHeatmap data={analysisData.monthly_returns} />
                </Col>
                <Col xs={24} lg={8}>
                    <ConsecutiveLossStats data={analysisData.consecutive_losses} />
                </Col>
            </Row>

            <Divider />

            {/* Row 2: Rolling Sharpe + Returns Distribution */}
            <Row gutter={[24, 24]}>
                <Col xs={24} lg={12}>
                    <RollingSharpeChart data={analysisData.rolling_sharpe} />
                </Col>
                <Col xs={24} lg={12}>
                    <ReturnsDistribution data={analysisData.returns_distribution} />
                </Col>
            </Row>

            <Divider />

            {/* Row 3: Drawdown Distribution */}
            <Row gutter={[24, 24]}>
                <Col span={24}>
                    <DrawdownDistribution data={analysisData.drawdown_distribution} />
                </Col>
            </Row>

            <Divider />

            {/* Row 4: Benchmark Comparison */}
            <Row gutter={[24, 24]}>
                <Col span={24}>
                    <BenchmarkComparison data={analysisData.benchmark_comparison} />
                </Col>
            </Row>
        </div>
    )
}

export default DeepAnalysis
