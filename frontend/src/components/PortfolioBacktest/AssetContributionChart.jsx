import { useMemo, useState } from 'react';
import ReactECharts from 'echarts-for-react';
import { Card, Empty, Space, Segmented, Button, Modal } from 'antd';
import { PieChartOutlined, FullscreenOutlined } from '@ant-design/icons';

/**
 * Color palette for assets
 */
const COLORS = [
    '#3b82f6', '#22c55e', '#f59e0b', '#ef4444', '#8b5cf6',
    '#ec4899', '#14b8a6', '#f97316', '#06b6d4', '#84cc16',
];

/**
 * Get color for asset by index
 */
const getColor = (index) => COLORS[index % COLORS.length];

/**
 * AssetContributionChart - Shows asset contribution to portfolio returns/weights
 */
const AssetContributionChart = ({ assetContributions, weights, t }) => {
    const [viewMode, setViewMode] = useState('contribution');
    const [isModalVisible, setIsModalVisible] = useState(false);

    // Prepare contribution data
    const contributionData = useMemo(() => {
        if (!assetContributions || Object.keys(assetContributions).length === 0) {
            return [];
        }

        return Object.entries(assetContributions).map(([ticker, data], idx) => ({
            name: ticker,
            value: Math.abs(data.contribution_pct || data.total_return || 0),
            rawValue: data.contribution_pct || data.total_return || 0,
            weight: data.weight || (weights && weights[idx]) || 0,
            totalReturn: data.total_return || 0,
            itemStyle: { color: getColor(idx) },
        }));
    }, [assetContributions, weights]);

    // Prepare weight data
    const weightData = useMemo(() => {
        if (!weights || weights.length === 0) {
            if (!assetContributions) return [];
            return Object.entries(assetContributions).map(([ticker, data], idx) => ({
                name: ticker,
                value: data.weight || 0,
                itemStyle: { color: getColor(idx) },
            }));
        }

        const tickers = Object.keys(assetContributions || {});
        return weights.map((w, idx) => ({
            name: tickers[idx] || `Asset ${idx + 1}`,
            value: w,
            itemStyle: { color: getColor(idx) },
        }));
    }, [weights, assetContributions]);

    const chartData = viewMode === 'contribution' ? contributionData : weightData;

    const option = useMemo(() => {
        if (!chartData || chartData.length === 0) return null;

        const isContribution = viewMode === 'contribution';

        return {
            tooltip: {
                trigger: 'item',
                formatter: (params) => {
                    const data = params.data;
                    if (isContribution) {
                        const sign = data.rawValue >= 0 ? '+' : '';
                        return `<strong>${data.name}</strong><br/>
                            ${t('portfolio.contribution', 'Contribution')}: ${sign}${(data.rawValue * 100).toFixed(2)}%<br/>
                            ${t('portfolio.weight', 'Weight')}: ${(data.weight * 100).toFixed(1)}%<br/>
                            ${t('portfolio.total_return', 'Return')}: ${(data.totalReturn * 100).toFixed(2)}%`;
                    }
                    return `<strong>${data.name}</strong><br/>
                        ${t('portfolio.weight', 'Weight')}: ${(data.value * 100).toFixed(1)}%`;
                },
            },
            legend: {
                orient: 'vertical',
                right: 10,
                top: 'center',
                textStyle: { color: '#c9d1d9' },
            },
            series: [
                {
                    type: 'pie',
                    radius: ['40%', '70%'],
                    center: ['40%', '50%'],
                    avoidLabelOverlap: true,
                    itemStyle: {
                        borderRadius: 4,
                        borderColor: '#1f2937',
                        borderWidth: 2,
                    },
                    label: {
                        show: true,
                        formatter: (params) => {
                            const pct = isContribution
                                ? (params.data.rawValue * 100).toFixed(1)
                                : (params.value * 100).toFixed(1);
                            return `${params.name}\n${pct}%`;
                        },
                        color: '#c9d1d9',
                        fontSize: 11,
                    },
                    labelLine: {
                        show: true,
                        lineStyle: { color: '#6b7280' },
                    },
                    emphasis: {
                        label: { show: true, fontSize: 14, fontWeight: 'bold' },
                        itemStyle: {
                            shadowBlur: 10,
                            shadowOffsetX: 0,
                            shadowColor: 'rgba(0, 0, 0, 0.5)',
                        },
                    },
                    data: chartData,
                },
            ],
        };
    }, [chartData, viewMode, t]);

    if (!assetContributions || Object.keys(assetContributions).length === 0) {
        return (
            <Card
                title={
                    <Space>
                        <PieChartOutlined />
                        {t('portfolio.asset_contribution', 'Asset Contribution')}
                    </Space>
                }
            >
                <Empty description={t('portfolio.no_contribution_data', 'No contribution data available')} />
            </Card>
        );
    }

    const viewOptions = [
        { label: t('portfolio.contribution', 'Contribution'), value: 'contribution' },
        { label: t('portfolio.weight', 'Weight'), value: 'weight' },
    ];

    return (
        <>
            <Card
                title={
                    <Space>
                        <PieChartOutlined />
                        {t('portfolio.asset_contribution', 'Asset Contribution')}
                    </Space>
                }
                extra={
                    <Space size="small">
                        <Segmented
                            size="small"
                            options={viewOptions}
                            value={viewMode}
                            onChange={setViewMode}
                        />
                        <Button
                            type="text"
                            icon={<FullscreenOutlined />}
                            onClick={() => setIsModalVisible(true)}
                        />
                    </Space>
                }
            >
                <ReactECharts
                    option={option}
                    style={{ height: 300 }}
                    opts={{ renderer: 'canvas' }}
                />
            </Card>

            <Modal
                title={
                    <Space>
                        <PieChartOutlined />
                        {t('portfolio.asset_contribution', 'Asset Contribution')}
                    </Space>
                }
                open={isModalVisible}
                onCancel={() => setIsModalVisible(false)}
                width="80%"
                footer={null}
                style={{ top: 20 }}
                destroyOnClose
            >
                <div style={{ marginBottom: 16 }}>
                    <Segmented
                        options={viewOptions}
                        value={viewMode}
                        onChange={setViewMode}
                    />
                </div>
                <ReactECharts
                    option={option}
                    style={{ height: 500 }}
                    opts={{ renderer: 'canvas' }}
                />
            </Modal>
        </>
    );
};

export default AssetContributionChart;
