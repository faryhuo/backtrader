import { useEffect, useMemo, useRef, useState } from 'react';
import { createChart } from 'lightweight-charts';
import { Empty } from 'antd';
import { useTranslation } from 'react-i18next';

function formatMoney(value) {
  if (value === null || value === undefined || Number.isNaN(Number(value))) {
    return '-';
  }
  return `$${Number(value).toLocaleString(undefined, {
    minimumFractionDigits: 2,
    maximumFractionDigits: 2,
  })}`;
}

function getPnlTone(value) {
  if (value > 0) return 'positive';
  if (value < 0) return 'negative';
  return 'neutral';
}

/**
 * Performance chart: portfolio value curve with session P&L tooltip.
 */
const PnLChart = ({ pnlHistory, currentPnl, portfolioValue, totalFeesDisplay }) => {
  const { t } = useTranslation();
  const chartContainerRef = useRef(null);
  const chartRef = useRef(null);
  const areaSeriesRef = useRef(null);
  const dataPointsRef = useRef([]);
  const [hoverPoint, setHoverPoint] = useState(null);

  const latestPoint = useMemo(() => {
    if (!pnlHistory || pnlHistory.length === 0) return null;
    return pnlHistory[pnlHistory.length - 1];
  }, [pnlHistory]);

  useEffect(() => {
    if (!chartContainerRef.current) return undefined;

    const chart = createChart(chartContainerRef.current, {
      width: chartContainerRef.current.clientWidth,
      height: 300,
      layout: {
        background: { color: 'transparent' },
        textColor: '#94a3b8',
      },
      grid: {
        vertLines: { color: 'rgba(255, 255, 255, 0.05)' },
        horzLines: { color: 'rgba(255, 255, 255, 0.05)' },
      },
      rightPriceScale: {
        borderColor: 'rgba(255, 255, 255, 0.1)',
      },
      timeScale: {
        borderColor: 'rgba(255, 255, 255, 0.1)',
        timeVisible: true,
        secondsVisible: false,
      },
      crosshair: {
        vertLine: {
          color: 'rgba(56, 189, 248, 0.25)',
          width: 1,
        },
        horzLine: {
          color: 'rgba(255, 255, 255, 0.12)',
          width: 1,
        },
      },
    });

    const areaSeries = chart.addAreaSeries({
      lineColor: '#38bdf8',
      topColor: 'rgba(56, 189, 248, 0.28)',
      bottomColor: 'rgba(56, 189, 248, 0.02)',
      lineWidth: 2,
      crosshairMarkerVisible: true,
      crosshairMarkerRadius: 4,
      lastValueVisible: true,
      priceLineVisible: true,
    });

    chart.subscribeCrosshairMove((param) => {
      if (!param?.time) {
        setHoverPoint(null);
        return;
      }

      const matched = dataPointsRef.current.find((item) => item.time === param.time);
      setHoverPoint(matched || null);
    });

    chartRef.current = chart;
    areaSeriesRef.current = areaSeries;

    const handleResize = () => {
      if (chartContainerRef.current && chartRef.current) {
        chartRef.current.applyOptions({
          width: chartContainerRef.current.clientWidth,
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
  }, []);

  useEffect(() => {
    if (!areaSeriesRef.current || !pnlHistory || pnlHistory.length === 0) return;

    const sortedPoints = [...pnlHistory]
      .map((point) => ({
        ...point,
        time: Math.floor(new Date(point.timestamp).getTime() / 1000),
        value: Number(point.portfolioValue ?? 0),
        pnl: Number(point.pnl ?? 0),
      }))
      .filter((point) => Number.isFinite(point.time) && Number.isFinite(point.value))
      .sort((a, b) => a.time - b.time);

    dataPointsRef.current = sortedPoints;
    areaSeriesRef.current.setData(sortedPoints.map(({ time, value }) => ({ time, value })));

    const positive = (currentPnl ?? 0) >= 0;
    areaSeriesRef.current.applyOptions({
      lineColor: positive ? '#4ade80' : '#f87171',
      topColor: positive ? 'rgba(74, 222, 128, 0.26)' : 'rgba(248, 113, 113, 0.24)',
      bottomColor: positive ? 'rgba(74, 222, 128, 0.02)' : 'rgba(248, 113, 113, 0.02)',
    });

    if (chartRef.current) {
      chartRef.current.timeScale().fitContent();
    }
  }, [pnlHistory, currentPnl]);

  if (!pnlHistory || pnlHistory.length === 0) {
    return (
      <Empty description={t('live.no_pnl_data')} style={{ margin: '40px 0' }} />
    );
  }

  const displayPoint = hoverPoint || latestPoint;
  const displayTimestamp = displayPoint?.timestamp
    ? new Date(displayPoint.timestamp).toLocaleString()
    : '-';
  const displayPortfolioValue = displayPoint?.portfolioValue ?? portfolioValue;
  const displayPnl = displayPoint?.pnl ?? currentPnl;
  const pnlTone = getPnlTone(displayPnl ?? 0);
  const pnlLabel = pnlTone === 'positive'
    ? t('live.session_profit', 'Session Profit')
    : pnlTone === 'negative'
      ? t('live.session_loss', 'Session Loss')
      : t('live.break_even', 'Break Even');

  return (
    <div style={{ position: 'relative' }}>
      <div
        style={{
          display: 'grid',
          gridTemplateColumns: 'repeat(3, minmax(0, 1fr))',
          gap: 12,
          marginBottom: 12,
        }}
      >
        <div>
          <div style={{ fontSize: 11, textTransform: 'uppercase', color: 'rgba(148,163,184,0.72)' }}>
            {t('live.portfolio_value', 'Portfolio Value')}
          </div>
          <div style={{ fontSize: 18, fontWeight: 700, color: '#e2e8f0' }}>
            {formatMoney(displayPortfolioValue)}
          </div>
        </div>
        <div>
          <div style={{ fontSize: 11, textTransform: 'uppercase', color: 'rgba(148,163,184,0.72)' }}>
            {pnlLabel}
          </div>
          <div
            style={{
              fontSize: 18,
              fontWeight: 700,
              color: pnlTone === 'positive' ? '#4ade80' : pnlTone === 'negative' ? '#f87171' : '#e2e8f0',
            }}
          >
            {formatMoney(displayPnl)}
          </div>
        </div>
        <div>
          <div style={{ fontSize: 11, textTransform: 'uppercase', color: 'rgba(148,163,184,0.72)' }}>
            {t('live.total_fees', 'Total Fees')}
          </div>
          <div style={{ fontSize: 14, fontWeight: 600, color: '#cbd5e1' }}>
            {totalFeesDisplay || t('live.total_fees_empty', 'No fees yet')}
          </div>
        </div>
        <div>
          <div style={{ fontSize: 11, textTransform: 'uppercase', color: 'rgba(148,163,184,0.72)' }}>
            {t('live.orders.time', 'Time')}
          </div>
          <div style={{ fontSize: 14, fontWeight: 600, color: '#cbd5e1' }}>
            {displayTimestamp}
          </div>
        </div>
      </div>

      <div ref={chartContainerRef} style={{ width: '100%', height: 300 }} />
    </div>
  );
};

export default PnLChart;
