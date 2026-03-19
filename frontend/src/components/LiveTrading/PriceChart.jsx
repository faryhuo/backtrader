import { useEffect, useRef, useState } from 'react';
import { createChart, ColorType } from 'lightweight-charts';
import { useTranslation } from 'react-i18next';

/**
 * Real-time K-line (candlestick) chart using lightweight-charts
 */
const PriceChart = ({ priceHistory, currentPrice, symbol }) => {
  const { t } = useTranslation();
  const containerRef = useRef(null);
  const chartRef = useRef(null);
  const seriesRef = useRef(null);
  const [hasData, setHasData] = useState(false);

  useEffect(() => {
    if (!containerRef.current || chartRef.current) return;

    // Create chart
    const chart = createChart(containerRef.current, {
      layout: {
        background: { type: ColorType.Solid, color: 'transparent' },
        textColor: '#d1d5db',
      },
      grid: {
        vertLines: { color: '#374151' },
        horzLines: { color: '#374151' },
      },
      width: containerRef.current.clientWidth,
      height: 280,
      timeScale: {
        timeVisible: true,
        secondsVisible: false,
      },
      rightPriceScale: {
        borderColor: '#4b5563',
      },
    });

    // Add candlestick series (K-line)
    const candlestickSeries = chart.addCandlestickSeries({
      upColor: '#22c55e',
      downColor: '#ef4444',
      borderUpColor: '#22c55e',
      borderDownColor: '#ef4444',
      wickUpColor: '#22c55e',
      wickDownColor: '#ef4444',
    });

    chartRef.current = chart;
    seriesRef.current = candlestickSeries;

    // Handle resize
    const handleResize = () => {
      try {
        if (containerRef.current && chartRef.current) {
          chartRef.current.applyOptions({
            width: containerRef.current.clientWidth,
          });
        }
      } catch (_e) {
        // Ignore resize errors
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

  // Convert timestamp to lightweight-charts time format (seconds)
  const toChartTime = (ts) => {
    if (!ts) return Math.floor(Date.now() / 1000);
    // If it's already in seconds
    if (ts < 1e12) return ts;
    // Convert milliseconds to seconds
    return Math.floor(ts / 1000);
  };

  // Convert price to number
  const toPrice = (p) => {
    const n = Number.parseFloat(p);
    return Number.isNaN(n) ? 0 : n;
  };

  // Update chart with historical data
  useEffect(() => {
    if (!seriesRef.current) return;

    if (!priceHistory || priceHistory.length === 0) {
      setHasData(false);
      return;
    }

    // Convert price history to candle data
    const candleData = priceHistory.map((item) => ({
      time: toChartTime(item.time),
      open: toPrice(item.open),
      high: toPrice(item.high),
      low: toPrice(item.low),
      close: toPrice(item.close),
    })).filter(c => c.open > 0 && c.high >= c.open && c.low <= c.open && c.close > 0);

    if (candleData.length > 0) {
      seriesRef.current.setData(candleData);
      setHasData(true);

      // Fit content to view
      try {
        chartRef.current?.timeScale().fitContent();
      } catch (_e) {
        // Ignore
      }
    }
  }, [priceHistory]);

  // Update latest candle in real-time
  useEffect(() => {
    if (!seriesRef.current || !currentPrice) return;

    const price = toPrice(currentPrice);
    if (price <= 0) return;

    const now = Math.floor(Date.now() / 1000);
    const lastCandle = priceHistory && priceHistory.length > 0
      ? priceHistory[priceHistory.length - 1]
      : null;

    // Determine candle time (aligned to minute)
    const candleTime = lastCandle && toChartTime(lastCandle.time) >= now - 60
      ? toChartTime(lastCandle.time)
      : now - (now % 60);

    if (lastCandle && toChartTime(lastCandle.time) >= now - 60) {
      // Update existing candle
      const lastOpen = toPrice(lastCandle.open);
      const lastHigh = toPrice(lastCandle.high);
      const lastLow = toPrice(lastCandle.low);

      seriesRef.current.update({
        time: candleTime,
        open: lastOpen,
        high: Math.max(lastHigh, price),
        low: Math.min(lastLow, price),
        close: price,
      });
    } else {
      // Create new candle
      seriesRef.current.update({
        time: candleTime,
        open: price,
        high: price,
        low: price,
        close: price,
      });
      setHasData(true);
    }
  }, [currentPrice, priceHistory]);

  return (
    <div style={{ position: 'relative', width: '100%', height: '280px' }}>
      <div ref={containerRef} style={{ width: '100%', height: '280px' }} />
      {!hasData && (!priceHistory || priceHistory.length === 0) && (
        <div
          style={{
            position: 'absolute',
            inset: 0,
            display: 'flex',
            alignItems: 'center',
            justifyContent: 'center',
            color: '#9ca3af',
            background: 'rgba(31, 41, 55, 0.5)',
            borderRadius: '8px',
            pointerEvents: 'none',
          }}
        >
          <div style={{ textAlign: 'center' }}>
            <div style={{ fontSize: '24px', marginBottom: '8px' }}>$</div>
            <div>{t('live.waiting_for_price_data', 'Waiting for price data...')}</div>
            {symbol && <div style={{ fontSize: '12px', marginTop: '4px' }}>{symbol}</div>}
          </div>
        </div>
      )}
    </div>
  );
};

export default PriceChart;
