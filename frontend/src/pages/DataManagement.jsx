/**
 * Data Management Page - Cache statistics, warmup, cleanup, and resampling
 */
import { useState, useEffect, useCallback } from 'react';
import { useTranslation } from 'react-i18next';
import { Row, Col, message, Typography } from 'antd';
import { DatabaseOutlined } from '@ant-design/icons';
import { api } from '../services/api';
import {
    CacheStatsCards,
    WarmupCard,
    ResampleCard,
    CleanupCard,
    CachedDataTable
} from '../components/DataManagement';
import './DataManagement.css';

const { Title, Paragraph } = Typography;

function DataManagement() {
    const { t } = useTranslation();

    // Cache stats state
    const [stats, setStats] = useState(null);
    const [statsLoading, setStatsLoading] = useState(false);

    // Warmup state
    const [warmupLoading, setWarmupLoading] = useState(false);
    const [warmupResult, setWarmupResult] = useState(null);

    // Resample state
    const [resampleLoading, setResampleLoading] = useState(false);
    const [resampleResult, setResampleResult] = useState(null);
    const [timeframes, setTimeframes] = useState([]);

    // Cleanup state
    const [cleanupLoading, setCleanupLoading] = useState(false);

    // Load cache stats
    const loadStats = useCallback(async () => {
        setStatsLoading(true);
        try {
            const data = await api.getCacheStats();
            setStats(data);
        } catch (error) {
            console.error('Failed to load cache stats:', error);
            message.error(t('datamanagement.stats.loading'));
        } finally {
            setStatsLoading(false);
        }
    }, [t]);

    // Load supported timeframes
    const loadTimeframes = useCallback(async () => {
        try {
            const data = await api.getSupportedTimeframes();
            setTimeframes(data.timeframes || []);
        } catch (error) {
            console.error('Failed to load timeframes:', error);
        }
    }, []);

    // Initial load
    useEffect(() => {
        loadStats();
        loadTimeframes();
    }, [loadStats, loadTimeframes]);

    // Handle warmup
    const handleWarmup = async (params) => {
        setWarmupLoading(true);
        setWarmupResult(null);
        try {
            const result = await api.warmupCache(params);
            setWarmupResult(result);
            message.success(t('datamanagement.warmup.success'));
            loadStats();
        } catch (error) {
            console.error('Warmup failed:', error);
            message.error(t('datamanagement.warmup.failed'));
        } finally {
            setWarmupLoading(false);
        }
    };

    // Handle resample
    const handleResample = async (params) => {
        setResampleLoading(true);
        setResampleResult(null);
        try {
            const result = await api.resampleData(params);
            setResampleResult(result);
            message.success(t('datamanagement.resample.success'));
        } catch (error) {
            console.error('Resample failed:', error);
            message.error(t('datamanagement.resample.failed'));
        } finally {
            setResampleLoading(false);
        }
    };

    // Handle cleanup
    const handleCleanup = async (params) => {
        setCleanupLoading(true);
        try {
            const result = await api.cleanupCache(params);
            message.success(t('datamanagement.cleanup.success', { count: result.deleted_records }));
            loadStats();
        } catch (error) {
            console.error('Cleanup failed:', error);
            message.error(t('datamanagement.cleanup.failed'));
        } finally {
            setCleanupLoading(false);
        }
    };

    // Handle delete ticker cache
    const handleDeleteTicker = async (ticker) => {
        try {
            await api.deleteTickerCache(ticker);
            message.success(t('datamanagement.cached_data.delete_success', { ticker }));
            loadStats();
        } catch (error) {
            console.error('Delete failed:', error);
            message.error(error.message);
        }
    };

    return (
        <div className="data-management-page">
            <div className="page-header">
                <Title level={2}>
                    <DatabaseOutlined /> {t('datamanagement.title')}
                </Title>
                <Paragraph type="secondary">{t('datamanagement.description')}</Paragraph>
            </div>

            {/* Stats Cards */}
            <CacheStatsCards
                stats={stats}
                statsLoading={statsLoading}
                warmupResult={warmupResult}
            />

            <Row gutter={[16, 16]} className="main-content">
                {/* Left Column - Warmup & Resample */}
                <Col xs={24} lg={12}>
                    <WarmupCard
                        onWarmup={handleWarmup}
                        loading={warmupLoading}
                        result={warmupResult}
                    />
                    <ResampleCard
                        onResample={handleResample}
                        loading={resampleLoading}
                        result={resampleResult}
                        timeframes={timeframes}
                    />
                </Col>

                {/* Right Column - Cleanup & Cached Data */}
                <Col xs={24} lg={12}>
                    <CleanupCard
                        onCleanup={handleCleanup}
                        loading={cleanupLoading}
                    />
                    <CachedDataTable
                        tickers={stats?.tickers}
                        loading={statsLoading}
                        onRefresh={loadStats}
                        onDelete={handleDeleteTicker}
                    />
                </Col>
            </Row>
        </div>
    );
}

export default DataManagement;
