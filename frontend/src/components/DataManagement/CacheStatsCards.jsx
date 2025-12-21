/**
 * Cache Statistics Cards Component
 * Displays overview statistics for the data cache
 */
import { Row, Col, Card, Statistic, Spin } from 'antd';
import {
    DatabaseOutlined,
    FireOutlined,
    LineChartOutlined,
    ClockCircleOutlined
} from '@ant-design/icons';
import { useTranslation } from 'react-i18next';

function CacheStatsCards({ stats, statsLoading, warmupResult }) {
    const { t } = useTranslation();

    return (
        <Spin spinning={statsLoading}>
            <Row gutter={[16, 16]} className="stats-row">
                <Col xs={24} sm={12} lg={6}>
                    <Card className="stat-card stat-card-tickers">
                        <Statistic
                            title={t('datamanagement.stats.total_tickers')}
                            value={stats?.total_tickers || 0}
                            prefix={<DatabaseOutlined />}
                        />
                    </Card>
                </Col>
                <Col xs={24} sm={12} lg={6}>
                    <Card className="stat-card stat-card-records">
                        <Statistic
                            title={t('datamanagement.stats.total_records')}
                            value={stats?.total_records || 0}
                            prefix={<LineChartOutlined />}
                        />
                    </Card>
                </Col>
                <Col xs={24} sm={12} lg={6}>
                    <Card className="stat-card stat-card-rate">
                        <Statistic
                            title={t('datamanagement.stats.cache_hit_rate')}
                            value={warmupResult?.cache_hit_rate
                                ? (warmupResult.cache_hit_rate * 100).toFixed(1)
                                : 'N/A'}
                            suffix={warmupResult?.cache_hit_rate ? '%' : ''}
                            prefix={<FireOutlined />}
                        />
                    </Card>
                </Col>
                <Col xs={24} sm={12} lg={6}>
                    <Card className="stat-card stat-card-updated">
                        <Statistic
                            title={t('datamanagement.stats.date_range')}
                            value={stats?.date_range
                                ? `${stats.date_range.start} ~ ${stats.date_range.end}`
                                : 'N/A'}
                            prefix={<ClockCircleOutlined />}
                            valueStyle={{ fontSize: '14px' }}
                        />
                    </Card>
                </Col>
            </Row>
        </Spin>
    );
}

export default CacheStatsCards;
