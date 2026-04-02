import { useRef, useEffect, useState, useMemo } from 'react';
import { Card, Empty, Space, Button, Modal, Segmented } from 'antd';
import { LineChartOutlined, FullscreenOutlined } from '@ant-design/icons';
import { createChart } from 'lightweight-charts';

/**
 * Inner chart component that handles the lightweight-charts rendering
 */
const EquityChartInner = ({ data, height = 300 }) => {
    const chartContainerRef = useRef(null);
    const chartRef = useRef(null);
    const seriesRef = useRef(null);

    useEffect(() => {
        if (!chartContainerRef.current) return;

        const chart = createChart(chartContainerRef.current, {
            width: chartContainerRef.current.clientWidth,
            height: height,
            layout: {
                background: { type: 'solid', color: 'transparent' },
                textColor: '#c9d1d9'
            },
            grid: {
                vertLines: { color: 'rgba(197, 203, 206, 0.1)' },
                horzLines: { color: 'rgba(197, 203, 206, 0.1)' }
            },
            rightPriceScale: {
                borderColor: 'rgba(197, 203, 206, 0.3)',
                scaleMargins: { top: 0.1, bottom: 0.1 }
            },
            timeScale: {
                borderColor: 'rgba(197, 203, 206, 0.3)',
                timeVisible: true,
                secondsVisible: false
            },
            crosshair: {
                mode: 1,
                vertLine: {
                    width: 1,
                    color: 'rgba(224, 227, 235, 0.3)',
                    style: 0,
                },
                horzLine: {
                    visible: true,
                    labelVisible: true,
                },
            },
            localization: {
                priceFormatter: (price) => '$' + price.toLocaleString(undefined, {
                    minimumFractionDigits: 0,
                    maximumFractionDigits: 0
                }),
            },
        });

        chartRef.current = chart;

        const handleResize = () => {
            if (chartContainerRef.current) {
                chart.applyOptions({ width: chartContainerRef.current.clientWidth });
            }
        };

        window.addEventListener('resize', handleResize);

        return () => {
            window.removeEventListener('resize', handleResize);
            chart.remove();
        };
    }, [height]);

    // Update data when it changes
    useEffect(() => {
        if (!chartRef.current || !data || data.length === 0) return;

        const chart = chartRef.current;

        // Create or update area series
        if (!seriesRef.current) {
            seriesRef.current = chart.addAreaSeries({
                lineColor: '#3b82f6',
                topColor: 'rgba(59, 130, 246, 0.4)',
                bottomColor: 'rgba(59, 130, 246, 0.0)',
                lineWidth: 2,
                priceFormat: {
                    type: 'custom',
                    formatter: (price) => '$' + price.toLocaleString(undefined, {
                        minimumFractionDigits: 0,
                        maximumFractionDigits: 0
                    }),
                },
            });
        }

        // Set the data
        seriesRef.current.setData(data);

        chart.timeScale().fitContent();

    }, [data]);

    return <div ref={chartContainerRef} style={{ height }} />;
};

/**
 * EquityCurveChart - Shows portfolio equity curve over time
 */
const EquityCurveChart = ({ equityCurve, t }) => {
    const [isModalVisible, setIsModalVisible] = useState(false);
    const [timeRange, setTimeRange] = useState('ALL');

    // Transform equity curve data to chart format
    const chartData = useMemo(() => {
        if (!equityCurve || Object.keys(equityCurve).length === 0) {
            return [];
        }

        // Convert object to sorted array
        const entries = Object.entries(equityCurve)
            .map(([date, value]) => ({ time: date, value }))
            .sort((a, b) => a.time.localeCompare(b.time));

        return entries;
    }, [equityCurve]);

    // Filter data based on time range
    const filteredData = useMemo(() => {
        if (chartData.length === 0) return [];
        if (timeRange === 'ALL') return chartData;

        const endDate = new Date(chartData[chartData.length - 1].time);
        let startDate = new Date(chartData[0].time);

        switch (timeRange) {
            case '1M':
                startDate = new Date(endDate);
                startDate.setMonth(startDate.getMonth() - 1);
                break;
            case '3M':
                startDate = new Date(endDate);
                startDate.setMonth(startDate.getMonth() - 3);
                break;
            case '6M':
                startDate = new Date(endDate);
                startDate.setMonth(startDate.getMonth() - 6);
                break;
            case '1Y':
                startDate = new Date(endDate);
                startDate.setFullYear(startDate.getFullYear() - 1);
                break;
            default:
                break;
        }

        const startStr = startDate.toISOString().split('T')[0];
        return chartData.filter(d => d.time >= startStr);
    }, [chartData, timeRange]);

    if (!equityCurve || Object.keys(equityCurve).length === 0) {
        return (
            <Card
                title={
                    <Space>
                        <LineChartOutlined />
                        {t('portfolio.equity_curve', 'Equity Curve')}
                    </Space>
                }
            >
                <Empty description={t('portfolio.no_equity_data', 'No equity curve data available')} />
            </Card>
        );
    }

    const timeRangeOptions = [
        { label: '1M', value: '1M' },
        { label: '3M', value: '3M' },
        { label: '6M', value: '6M' },
        { label: '1Y', value: '1Y' },
        { label: t('common.all', 'All'), value: 'ALL' },
    ];

    return (
        <>
            <Card
                title={
                    <Space>
                        <LineChartOutlined />
                        {t('portfolio.equity_curve', 'Equity Curve')}
                    </Space>
                }
                extra={
                    <Space size="small">
                        <Segmented
                            size="small"
                            options={timeRangeOptions}
                            value={timeRange}
                            onChange={setTimeRange}
                        />
                        <Button
                            type="text"
                            icon={<FullscreenOutlined />}
                            onClick={() => setIsModalVisible(true)}
                        />
                    </Space>
                }
            >
                <EquityChartInner
                    data={filteredData}
                    height={300}
                />
            </Card>

            <Modal
                title={
                    <Space>
                        <LineChartOutlined />
                        {t('portfolio.equity_curve', 'Equity Curve')}
                    </Space>
                }
                open={isModalVisible}
                onCancel={() => setIsModalVisible(false)}
                width="90%"
                footer={null}
                style={{ top: 20 }}
                destroyOnClose
            >
                <div style={{ marginBottom: 16 }}>
                    <Segmented
                        options={timeRangeOptions}
                        value={timeRange}
                        onChange={setTimeRange}
                    />
                </div>
                <EquityChartInner
                    data={filteredData}
                    height={500}
                />
            </Modal>
        </>
    );
};

export default EquityCurveChart;
