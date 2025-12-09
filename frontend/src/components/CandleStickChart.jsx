import { createChart } from 'lightweight-charts';
import React, { useEffect, useRef } from 'react';
import PropTypes from 'prop-types';

function CandleStickChart({ data }) {
    const chartContainerRef = useRef();
    const chartRef = useRef(null);
    const seriesRef = useRef(null);

    // 1. Initialize Chart
    useEffect(() => {
        if (!chartContainerRef.current) return;

        const chart = createChart(chartContainerRef.current, {
            width: chartContainerRef.current.clientWidth,
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
            },
            rightPriceScale: {
                borderColor: '#30363d',
            },
        });

        const candleSeries = chart.addCandlestickSeries({
            upColor: '#2ea043',
            downColor: '#f85149',
            borderVisible: false,
            wickUpColor: '#2ea043',
            wickDownColor: '#f85149',
        });

        chartRef.current = chart;
        seriesRef.current = candleSeries;

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
        };
    }, []);

    // 2. Update Data
    useEffect(() => {
        if (seriesRef.current && data && data.length > 0) {
            // Ensure unique and sorted data
            const uniqueData = [...new Map(data.map(item => [item.time, item])).values()];
            uniqueData.sort((a, b) => (new Date(a.time) - new Date(b.time)));
            
            seriesRef.current.setData(uniqueData);
            
            if (chartRef.current) {
                chartRef.current.timeScale().fitContent();
            }
        }
    }, [data]);

    return (
        <div 
            ref={chartContainerRef} 
            style={{ width: '100%', height: '500px', border: '1px solid var(--border-color)', borderRadius: '8px', overflow: 'hidden' }}
        />
    );
}

CandleStickChart.propTypes = {
    data: PropTypes.arrayOf(PropTypes.shape({
        time: PropTypes.string.isRequired,
        open: PropTypes.number.isRequired,
        high: PropTypes.number.isRequired,
        low: PropTypes.number.isRequired,
        close: PropTypes.number.isRequired,
    })).isRequired,
};

export default CandleStickChart;
