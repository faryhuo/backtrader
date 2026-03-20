import { useCallback, useEffect, useMemo, useRef, useState } from 'react';
import { createChart, ColorType } from 'lightweight-charts';
import { useTranslation } from 'react-i18next';

/**
 * Real-time K-line (candlestick) chart using lightweight-charts
 */
const PriceChart = ({ priceHistory, currentPrice, symbol, ticker, openPrice, prevTicker }) => {
  const { t } = useTranslation();
  const containerRef = useRef(null);
  const chartRef = useRef(null);
  const seriesRef = useRef(null);
  const volumeSeriesRef = useRef(null);
  const ma5SeriesRef = useRef(null);
  const ma10SeriesRef = useRef(null);
  const priceHistoryRef = useRef([]);
  const [hasData, setHasData] = useState(false);
  const [hoverData, setHoverData] = useState(null);

  const formatPrice = (value, fallback = '--') => {
    const number = Number(value);
    if (!Number.isFinite(number) || number <= 0) return fallback;
    return number.toLocaleString(undefined, {
      minimumFractionDigits: 2,
      maximumFractionDigits: 8,
    });
  };

  const formatCompact = (value, fallback = '--') => {
    const number = Number(value);
    if (!Number.isFinite(number) || number < 0) return fallback;
    return new Intl.NumberFormat(undefined, {
      notation: 'compact',
      maximumFractionDigits: 2,
    }).format(number);
  };

  const chartSummary = useMemo(() => {
    const lastPrice = Number(ticker?.last ?? currentPrice ?? 0);
    const referenceOpen = Number(openPrice ?? 0);
    const previousPrice = Number(prevTicker?.last ?? 0);
    const change = referenceOpen > 0
      ? lastPrice - referenceOpen
      : previousPrice > 0
        ? lastPrice - previousPrice
        : 0;
    const changePercent = referenceOpen > 0
      ? (change / referenceOpen) * 100
      : previousPrice > 0
        ? (change / previousPrice) * 100
        : 0;
    const trendTone = change > 0 ? '#4ade80' : change < 0 ? '#f87171' : '#e2e8f0';
    const lastTimestamp = ticker?.timestamp
      ? new Date(ticker.timestamp < 1e12 ? ticker.timestamp * 1000 : ticker.timestamp)
      : null;

    return {
      lastPrice,
      change,
      changePercent,
      trendTone,
      high: Number(ticker?.high ?? 0),
      low: Number(ticker?.low ?? 0),
      bid: Number(ticker?.bid ?? 0),
      ask: Number(ticker?.ask ?? 0),
      volume: Number(ticker?.volume ?? 0),
      updatedAt: lastTimestamp && !Number.isNaN(lastTimestamp.getTime())
        ? lastTimestamp.toLocaleTimeString()
        : '--',
      bars: Array.isArray(priceHistory) ? priceHistory.length : 0,
    };
  }, [ticker, currentPrice, openPrice, prevTicker, priceHistory]);

  const latestBar = useMemo(() => {
    if (!priceHistory || priceHistory.length === 0) return null;
    const lastIndex = priceHistory.length - 1;
    const current = priceHistory[lastIndex];
    const previous = lastIndex > 0 ? priceHistory[lastIndex - 1] : null;
    return {
      ...current,
      previousClose: previous ? Number(previous.close ?? 0) : Number(current?.open ?? 0),
    };
  }, [priceHistory]);

  const indicatorSummary = useMemo(() => {
    const source = hoverData || latestBar;
    if (!source) return null;

    const open = Number(source.open ?? 0);
    const high = Number(source.high ?? 0);
    const low = Number(source.low ?? 0);
    const close = Number(source.close ?? 0);
    const volume = Number(source.volume ?? 0);
    const prevClose = Number(source.previousClose ?? open);
    const change = close - prevClose;
    const changePercent = prevClose > 0 ? (change / prevClose) * 100 : 0;

    return {
      open,
      high,
      low,
      close,
      volume,
      change,
      changePercent,
      ma5: source.ma5 ?? null,
      ma10: source.ma10 ?? null,
    };
  }, [hoverData, latestBar]);

  useEffect(() => {
    priceHistoryRef.current = Array.isArray(priceHistory) ? priceHistory : [];
  }, [priceHistory]);

  const toChartTime = (ts) => {
    if (!ts) return Math.floor(Date.now() / 1000);
    if (ts < 1e12) return ts;
    return Math.floor(ts / 1000);
  };

  const toPrice = (p) => {
    const n = Number.parseFloat(p);
    return Number.isNaN(n) ? 0 : n;
  };

  const calculateMovingAverageSeries = useCallback((data, period) => (
    data.map((item, index) => {
      if (index < period - 1) {
        return null;
      }

      const slice = data.slice(index - period + 1, index + 1);
      const avg = slice.reduce((sum, entry) => sum + toPrice(entry.close), 0) / period;

      return {
        time: toChartTime(item.time),
        value: avg,
      };
    }).filter(Boolean)
  ), []);

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
      height: 340,
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
      priceScaleId: 'right',
      priceLineVisible: true,
    });

    const volumeSeries = chart.addHistogramSeries({
      priceScaleId: 'volume',
      priceFormat: {
        type: 'volume',
      },
      lastValueVisible: false,
      priceLineVisible: false,
    });

    const ma5Series = chart.addLineSeries({
      color: '#fbbf24',
      lineWidth: 2,
      priceLineVisible: false,
      lastValueVisible: false,
      crosshairMarkerVisible: false,
    });

    const ma10Series = chart.addLineSeries({
      color: '#38bdf8',
      lineWidth: 2,
      priceLineVisible: false,
      lastValueVisible: false,
      crosshairMarkerVisible: false,
    });

    chart.priceScale('right').applyOptions({
      borderColor: '#4b5563',
      scaleMargins: {
        top: 0.08,
        bottom: 0.3,
      },
    });

    chart.priceScale('volume').applyOptions({
      borderColor: '#4b5563',
      scaleMargins: {
        top: 0.78,
        bottom: 0,
      },
    });

    chartRef.current = chart;
    seriesRef.current = candlestickSeries;
    volumeSeriesRef.current = volumeSeries;
    ma5SeriesRef.current = ma5Series;
    ma10SeriesRef.current = ma10Series;

    const onCrosshairMove = (param) => {
      if (!param?.time || !param.seriesData) {
        setHoverData(null);
        return;
      }

      const candle = param.seriesData.get(candlestickSeries);
      if (!candle) {
        setHoverData(null);
        return;
      }

      const time = Number(candle.time);
      const history = priceHistoryRef.current;
      const index = Array.isArray(history)
        ? history.findIndex((item) => toChartTime(item.time) === time)
        : -1;
      const previousClose = index > 0 ? toPrice(history[index - 1]?.close) : toPrice(candle.open);

      setHoverData({
        time,
        open: candle.open,
        high: candle.high,
        low: candle.low,
        close: candle.close,
        volume: param.seriesData.get(volumeSeries)?.value ?? 0,
        ma5: param.seriesData.get(ma5Series)?.value ?? null,
        ma10: param.seriesData.get(ma10Series)?.value ?? null,
        previousClose,
      });
    };

    chart.subscribeCrosshairMove(onCrosshairMove);

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
      chart.unsubscribeCrosshairMove(onCrosshairMove);
      chart.remove();
      chartRef.current = null;
      seriesRef.current = null;
      volumeSeriesRef.current = null;
      ma5SeriesRef.current = null;
      ma10SeriesRef.current = null;
    };
  }, []);

  // Update chart with historical data
  useEffect(() => {
    if (!seriesRef.current || !volumeSeriesRef.current || !ma5SeriesRef.current || !ma10SeriesRef.current) return;

    if (!priceHistory || priceHistory.length === 0) {
      setHasData(false);
      return;
    }

    const enrichedHistory = priceHistory.map((item, index) => ({
      ...item,
      previousClose: index > 0 ? toPrice(priceHistory[index - 1]?.close) : toPrice(item.open),
    }));

    const candleData = enrichedHistory.map((item) => ({
      time: toChartTime(item.time),
      open: toPrice(item.open),
      high: toPrice(item.high),
      low: toPrice(item.low),
      close: toPrice(item.close),
    })).filter(c => c.open > 0 && c.high >= c.open && c.low <= c.open && c.close > 0);

    const volumeData = enrichedHistory.map((item) => {
      const open = toPrice(item.open);
      const close = toPrice(item.close);
      return {
        time: toChartTime(item.time),
        value: toPrice(item.volume),
        color: close >= open ? 'rgba(34, 197, 94, 0.55)' : 'rgba(239, 68, 68, 0.55)',
      };
    }).filter((item) => item.value > 0);

    if (candleData.length > 0) {
      seriesRef.current.setData(candleData);
      volumeSeriesRef.current.setData(volumeData);
      ma5SeriesRef.current.setData(calculateMovingAverageSeries(enrichedHistory, 5));
      ma10SeriesRef.current.setData(calculateMovingAverageSeries(enrichedHistory, 10));
      setHasData(true);

      // Fit content to view
      try {
        chartRef.current?.timeScale().fitContent();
      } catch (_e) {
        // Ignore
      }
    }
  }, [calculateMovingAverageSeries, priceHistory]);

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
    <div style={{ display: 'grid', gap: '14px' }}>
      <div
        style={{
          display: 'flex',
          flexWrap: 'wrap',
          alignItems: 'center',
          gap: '14px',
          padding: '10px 12px',
          borderRadius: '12px',
          background: 'rgba(7, 13, 24, 0.5)',
          border: '1px solid rgba(148, 163, 184, 0.12)',
          fontSize: '12px',
          fontVariantNumeric: 'tabular-nums',
        }}
      >
        <span style={{ color: '#94a3b8' }}>{symbol || 'MARKET'}</span>
        <span style={{ color: '#f8fafc' }}>O {formatPrice(indicatorSummary?.open)}</span>
        <span style={{ color: '#4ade80' }}>H {formatPrice(indicatorSummary?.high)}</span>
        <span style={{ color: '#f87171' }}>L {formatPrice(indicatorSummary?.low)}</span>
        <span style={{ color: '#f8fafc' }}>C {formatPrice(indicatorSummary?.close)}</span>
        <span style={{ color: (indicatorSummary?.change ?? 0) >= 0 ? '#4ade80' : '#f87171' }}>
          CHG {(indicatorSummary?.change ?? 0) > 0 ? '+' : ''}{formatPrice(indicatorSummary?.change, '0.00')}
          {' '}
          ({(indicatorSummary?.change ?? 0) > 0 ? '+' : ''}{(indicatorSummary?.changePercent ?? 0).toFixed(2)}%)
        </span>
        <span style={{ color: '#cbd5e1' }}>VOL {formatCompact(indicatorSummary?.volume)}</span>
        <span style={{ color: '#fbbf24' }}>MA5 {formatPrice(indicatorSummary?.ma5)}</span>
        <span style={{ color: '#38bdf8' }}>MA10 {formatPrice(indicatorSummary?.ma10)}</span>
      </div>

      <div
        style={{
          display: 'grid',
          gridTemplateColumns: 'repeat(auto-fit, minmax(180px, 1fr))',
          gap: '10px',
        }}
      >
        <div
          style={{
            padding: '12px 14px',
            borderRadius: '14px',
            background: 'rgba(7, 13, 24, 0.46)',
            border: '1px solid rgba(148, 163, 184, 0.12)',
          }}
        >
          <div style={{ color: '#8ea0bb', fontSize: '11px', textTransform: 'uppercase', letterSpacing: '0.08em' }}>
            {t('live.price_card.last_price', 'Last Price')}
          </div>
          <div style={{ marginTop: '8px', fontSize: '26px', fontWeight: 700, color: '#f8fafc' }}>
            {formatPrice(chartSummary.lastPrice)}
          </div>
          <div style={{ marginTop: '6px', fontSize: '13px', fontWeight: 600, color: chartSummary.trendTone }}>
            {chartSummary.change > 0 ? '+' : ''}{formatPrice(chartSummary.change, '0.00')}
            {' '}
            ({chartSummary.change > 0 ? '+' : ''}{chartSummary.changePercent.toFixed(2)}%)
          </div>
        </div>

        <div
          style={{
            padding: '12px 14px',
            borderRadius: '14px',
            background: 'rgba(7, 13, 24, 0.46)',
            border: '1px solid rgba(148, 163, 184, 0.12)',
            display: 'grid',
            gap: '10px',
          }}
        >
          <div style={{ display: 'flex', justifyContent: 'space-between', gap: '12px' }}>
            <div>
              <div style={{ color: '#8ea0bb', fontSize: '11px', textTransform: 'uppercase', letterSpacing: '0.08em' }}>
                {t('live.price_card.day_high', 'Day High')}
              </div>
              <div style={{ marginTop: '6px', fontWeight: 700, color: '#4ade80' }}>
                {formatPrice(chartSummary.high)}
              </div>
            </div>
            <div>
              <div style={{ color: '#8ea0bb', fontSize: '11px', textTransform: 'uppercase', letterSpacing: '0.08em' }}>
                {t('live.price_card.day_low', 'Day Low')}
              </div>
              <div style={{ marginTop: '6px', fontWeight: 700, color: '#f87171' }}>
                {formatPrice(chartSummary.low)}
              </div>
            </div>
          </div>
          <div style={{ color: '#8ea0bb', fontSize: '12px' }}>
            {t('live.price_card.candles', 'Loaded Bars')}: {chartSummary.bars}
          </div>
        </div>

        <div
          style={{
            padding: '12px 14px',
            borderRadius: '14px',
            background: 'rgba(7, 13, 24, 0.46)',
            border: '1px solid rgba(148, 163, 184, 0.12)',
            display: 'grid',
            gap: '10px',
          }}
        >
          <div style={{ display: 'flex', justifyContent: 'space-between', gap: '12px' }}>
            <div>
              <div style={{ color: '#8ea0bb', fontSize: '11px', textTransform: 'uppercase', letterSpacing: '0.08em' }}>
                {t('live.price_card.bid', 'Bid')}
              </div>
              <div style={{ marginTop: '6px', fontWeight: 700, color: '#4ade80' }}>
                {formatPrice(chartSummary.bid)}
              </div>
            </div>
            <div>
              <div style={{ color: '#8ea0bb', fontSize: '11px', textTransform: 'uppercase', letterSpacing: '0.08em' }}>
                {t('live.price_card.ask', 'Ask')}
              </div>
              <div style={{ marginTop: '6px', fontWeight: 700, color: '#f87171' }}>
                {formatPrice(chartSummary.ask)}
              </div>
            </div>
          </div>
          <div style={{ color: '#8ea0bb', fontSize: '12px' }}>
            {t('live.price_card.volume', 'Volume')}: {formatCompact(chartSummary.volume)}
          </div>
          <div style={{ color: '#8ea0bb', fontSize: '12px' }}>
            {t('live.price_card.updated', 'Updated')}: {chartSummary.updatedAt}
          </div>
        </div>
      </div>

      <div
        style={{
          display: 'flex',
          justifyContent: 'space-between',
          alignItems: 'center',
          gap: '12px',
          padding: '0 4px',
          color: '#8ea0bb',
          fontSize: '12px',
        }}
      >
        <span>{t('live.price_card.volume_panel', 'Volume')}</span>
        <div style={{ display: 'flex', gap: '12px' }}>
          <span style={{ color: '#fbbf24' }}>MA5</span>
          <span style={{ color: '#38bdf8' }}>MA10</span>
        </div>
      </div>

      <div style={{ position: 'relative', width: '100%', height: '340px' }}>
        <div ref={containerRef} style={{ width: '100%', height: '340px' }} />
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
    </div>
  );
};

export default PriceChart;
