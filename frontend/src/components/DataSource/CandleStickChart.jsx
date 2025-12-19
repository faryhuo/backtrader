import { createChart } from 'lightweight-charts';
import React, { useEffect, useRef, useState } from 'react';
import PropTypes from 'prop-types';

function CandleStickChart({ data, chartType = 'candlestick', indicators = {} }) {
    const chartContainerRef = useRef();
    const chartRef = useRef(null);
    const seriesRef = useRef(null);
    const volumeSeriesRef = useRef(null);
    const indicatorSeriesRef = useRef({});
    const [chartReady, setChartReady] = useState(false);

    // Chart configuration
    const chartConfig = {
        width: chartContainerRef.current?.clientWidth || 800,
        height: 500,
        layout: {
            background: { type: 'solid', color: '#0d1117' },
            textColor: '#c9d1d9',
        },
        grid: {
            vertLines: { color: '#30363d' },
            horzLines: { color: '#30363d' },
        },
        timeScale: {
            borderColor: '#30363d',
            timeVisible: true,
        },
        rightPriceScale: {
            borderColor: '#30363d',
        },
    };

    // 1. Initialize Chart
    useEffect(() => {
        if (!chartContainerRef.current) return;

        const chart = createChart(chartContainerRef.current, chartConfig);

        chartRef.current = chart;
        setChartReady(true);

        const handleResize = () => {
            if (chartContainerRef.current) {
                chart.applyOptions({ width: chartContainerRef.current.clientWidth });
            }
        };

        window.addEventListener('resize', handleResize);

        return () => {
            window.removeEventListener('resize', handleResize);
            chart.remove();
            chartRef.current = null;
            seriesRef.current = null;
            volumeSeriesRef.current = null;
            indicatorSeriesRef.current = {};
            setChartReady(false);
        };
    }, []);

    // 2. Update Chart Type, Series, and Data together
    useEffect(() => {
        if (!chartRef.current || !chartReady) return;

        // Remove old series
        if (seriesRef.current) {
            chartRef.current.removeSeries(seriesRef.current);
            seriesRef.current = null;
        }

        // Create new series based on chart type
        let newSeries;
        switch (chartType) {
            case 'line':
                newSeries = chartRef.current.addLineSeries({
                    color: '#0ea5e9',
                    lineWidth: 2,
                });
                break;
            case 'area':
                newSeries = chartRef.current.addAreaSeries({
                    topColor: 'rgba(14, 165, 233, 0.56)',
                    bottomColor: 'rgba(14, 165, 233, 0.04)',
                    lineColor: '#0ea5e9',
                    lineWidth: 2,
                });
                break;
            case 'candlestick':
            default:
                newSeries = chartRef.current.addCandlestickSeries({
                    upColor: '#22c55e',
                    downColor: '#ef4444',
                    borderVisible: false,
                    wickUpColor: '#22c55e',
                    wickDownColor: '#ef4444',
                });
                break;
        }

        seriesRef.current = newSeries;

        // Set data immediately after creating series
        if (data && data.length > 0) {
            // Ensure unique and sorted data
            const uniqueData = [...new Map(data.map(item => [item.time, item])).values()];
            uniqueData.sort((a, b) => (new Date(a.time) - new Date(b.time)));

            // Set data based on chart type
            if (chartType === 'line' || chartType === 'area') {
                // For line/area charts, use close prices
                const lineData = uniqueData.map(item => ({
                    time: item.time,
                    value: item.close
                }));
                newSeries.setData(lineData);
            } else {
                // For candlestick charts, use OHLC data
                newSeries.setData(uniqueData);
            }

            if (chartRef.current) {
                chartRef.current.timeScale().fitContent();
            }
        }
    }, [chartType, chartReady, data]);

    // 4. Add Volume Indicator
    useEffect(() => {
        if (!chartRef.current || !chartReady || !indicators.volume || !data) return;

        // Remove old volume series if exists
        if (volumeSeriesRef.current) {
            chartRef.current.removeSeries(volumeSeriesRef.current);
        }

        // Add histogram for volume
        const volumeSeries = chartRef.current.addHistogramSeries({
            color: '#26a69a',
            priceFormat: {
                type: 'volume',
            },
            priceScaleId: 'volume',
        });

        chartRef.current.priceScale('volume').applyOptions({
            scaleMargins: {
                top: 0.8,
                bottom: 0,
            },
        });

        // Prepare volume data
        const volumeData = data
            .filter(item => item.volume !== undefined)
            .map(item => ({
                time: item.time,
                value: item.volume,
                color: item.close >= item.open ? '#22c55e80' : '#ef444480'
            }));

        volumeSeries.setData(volumeData);
        volumeSeriesRef.current = volumeSeries;

        return () => {
            if (volumeSeriesRef.current && chartRef.current) {
                try {
                    chartRef.current.removeSeries(volumeSeriesRef.current);
                } catch (e) {
                    // Series might already be removed
                }
                volumeSeriesRef.current = null;
            }
        };
    }, [indicators.volume, data, chartReady]);

    // 5. Add Moving Average Indicators
    useEffect(() => {
        if (!chartRef.current || !chartReady || !data || data.length === 0) return;

        // Remove old MA lines
        Object.values(indicatorSeriesRef.current).forEach(series => {
            try {
                chartRef.current.removeSeries(series);
            } catch (e) {
                // Series might already be removed
            }
        });
        indicatorSeriesRef.current = {};

        // Calculate and add MA lines
        const maConfig = {
            ma5: { period: 5, color: '#f59e0b', enabled: indicators.ma5 },
            ma10: { period: 10, color: '#8b5cf6', enabled: indicators.ma10 },
            ma20: { period: 20, color: '#ec4899', enabled: indicators.ma20 },
            ma50: { period: 50, color: '#06b6d4', enabled: indicators.ma50 },
        };

        Object.entries(maConfig).forEach(([key, config]) => {
            if (!config.enabled) return;

            const maData = calculateMA(data, config.period);
            if (maData.length > 0) {
                const maSeries = chartRef.current.addLineSeries({
                    color: config.color,
                    lineWidth: 1,
                    crosshairMarkerVisible: false,
                    priceLineVisible: false,
                });
                maSeries.setData(maData);
                indicatorSeriesRef.current[key] = maSeries;
            }
        });

        return () => {
            Object.values(indicatorSeriesRef.current).forEach(series => {
                try {
                    if (chartRef.current) {
                        chartRef.current.removeSeries(series);
                    }
                } catch (e) {
                    // Series might already be removed
                }
            });
            indicatorSeriesRef.current = {};
        };
    }, [indicators.ma5, indicators.ma10, indicators.ma20, indicators.ma50, data, chartReady]);

    return (
        <div
            ref={chartContainerRef}
            style={{
                width: '100%',
                height: '500px',
                border: '1px solid var(--border-color)',
                borderRadius: '8px',
                overflow: 'hidden'
            }}
        />
    );
}

// Helper function to calculate Moving Average
function calculateMA(data, period) {
    if (!data || data.length < period) return [];

    const maData = [];
    for (let i = period - 1; i < data.length; i++) {
        let sum = 0;
        for (let j = 0; j < period; j++) {
            sum += data[i - j].close;
        }
        maData.push({
            time: data[i].time,
            value: sum / period
        });
    }
    return maData;
}

CandleStickChart.propTypes = {
    data: PropTypes.arrayOf(PropTypes.shape({
        time: PropTypes.string.isRequired,
        open: PropTypes.number.isRequired,
        high: PropTypes.number.isRequired,
        low: PropTypes.number.isRequired,
        close: PropTypes.number.isRequired,
        volume: PropTypes.number,
    })).isRequired,
    chartType: PropTypes.oneOf(['candlestick', 'line', 'area']),
    indicators: PropTypes.shape({
        volume: PropTypes.bool,
        ma5: PropTypes.bool,
        ma10: PropTypes.bool,
        ma20: PropTypes.bool,
        ma50: PropTypes.bool,
    })
};

export default CandleStickChart;
