import { useEffect, useRef } from 'react';
import { createChart } from 'lightweight-charts';
import { Empty } from 'antd';
import { useTranslation } from 'react-i18next';

/**
 * P&L Chart Component
 * Real-time visualization of profit/loss over time
 */
const PnLChart = ({ pnlHistory, currentPnl }) => {
  const { t } = useTranslation();
  const chartContainerRef = useRef(null);
  const chartRef = useRef(null);
  const lineSeriesRef = useRef(null);

  useEffect(() => {
    if (!chartContainerRef.current) return;

    // Initialize chart
    const chart = createChart(chartContainerRef.current, {
      width: chartContainerRef.current.clientWidth,
      height: 300,
      layout: {
        background: { color: 'transparent' }, // Transparent for dark theme
        textColor: '#94a3b8' // Slate 400
      },
      grid: {
        vertLines: { color: 'rgba(255, 255, 255, 0.05)' },
        horzLines: { color: 'rgba(255, 255, 255, 0.05)' }
      },
      rightPriceScale: {
        borderColor: 'rgba(255, 255, 255, 0.1)'
      },
      timeScale: {
        borderColor: 'rgba(255, 255, 255, 0.1)',
        timeVisible: true,
        secondsVisible: false
      }
    });

    const lineSeries = chart.addLineSeries({
      color: '#38bdf8', // Sky 400
      lineWidth: 2,
      crosshairMarkerVisible: true,
      crosshairMarkerRadius: 4,
      lastValueVisible: true,
      priceLineVisible: true
    });

    // Add zero line
    lineSeries.createPriceLine({
      price: 0,
      color: 'rgba(255, 255, 255, 0.3)',
      lineWidth: 1,
      lineStyle: 2, // Dashed
      axisLabelVisible: true,
      title: t('live.break_even')
    });

    chartRef.current = chart;
    lineSeriesRef.current = lineSeries;

    // Handle resize
    const handleResize = () => {
      if (chartContainerRef.current && chartRef.current) {
        chartRef.current.applyOptions({
          width: chartContainerRef.current.clientWidth
        });
      }
    };

    window.addEventListener('resize', handleResize);

    return () => {
      window.removeEventListener('resize', handleResize);
      if (chartRef.current) {
        chartRef.current.remove();
      }
    };
  }, [t]);

  useEffect(() => {
    if (!lineSeriesRef.current || !pnlHistory || pnlHistory.length === 0) return;

    // Update chart data
    const chartData = pnlHistory.map((point) => ({
      time: Math.floor(new Date(point.timestamp).getTime() / 1000),
      value: point.pnl
    }));

    // Sort by time
    chartData.sort((a, b) => a.time - b.time);

    lineSeriesRef.current.setData(chartData);

    // Update line color based on current P&L
    const color = currentPnl >= 0 ? '#4ade80' : '#f87171';
    lineSeriesRef.current.applyOptions({ color });
  }, [pnlHistory, currentPnl]);

  if (!pnlHistory || pnlHistory.length === 0) {
    return (
      <Empty description={t('live.no_pnl_data')} style={{ margin: '40px 0' }} />
    );
  }

  return (
    <div ref={chartContainerRef} style={{ width: '100%', height: 300 }} />
  );
};

export default PnLChart;
