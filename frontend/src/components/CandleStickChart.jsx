import { createChart } from 'lightweight-charts';
import React, { useEffect, useRef } from 'react';
import PropTypes from 'prop-types';

function CandleStickChart({ data }) {
    const chartContainerRef = useRef();
    const chartRef = useRef(null);

    useEffect(() => {
        if (!chartContainerRef.current) return;

        const chart = createChart(chartContainerRef.current, {
            width: chartContainerRef.current.clientWidth,
            height: 500,
            layout: {
                background: { color: '#0d1117' },
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

        candleSeries.setData(data);

        chart.timeScale().fitContent();

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
