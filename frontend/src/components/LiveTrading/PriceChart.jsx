import { memo, useEffect, useMemo, useRef, useState } from 'react';
import { createChart, ColorType } from 'lightweight-charts';
import { useTranslation } from 'react-i18next';

function getTimeframeSeconds(timeframe) {
  const normalized = String(timeframe || '1m').trim().toLowerCase();
  const match = normalized.match(/^(\d+)([smhdw])$/);
  if (!match) {
    return 60;
  }

  const value = Number.parseInt(match[1], 10);
  const unit = match[2];
  const multiplierMap = {
    s: 1,
    m: 60,
    h: 3600,
    d: 86400,
    w: 604800,
  };

  return Math.max(value * (multiplierMap[unit] || 60), 1);
}

function toChartTime(ts) {
  if (!ts) return Math.floor(Date.now() / 1000);
  return ts < 1e12 ? Math.floor(ts) : Math.floor(ts / 1000);
}

function toPrice(value) {
  const parsed = Number.parseFloat(value);
  return Number.isNaN(parsed) ? 0 : parsed;
}

function normalizeHistory(priceHistory) {
  const merged = new Map();

  (priceHistory || []).forEach((item) => {
    const time = toChartTime(item?.time);
    const open = toPrice(item?.open);
    const high = toPrice(item?.high);
    const low = toPrice(item?.low);
    const close = toPrice(item?.close);

    if (!Number.isFinite(time) || open <= 0 || high <= 0 || low <= 0 || close <= 0) {
      return;
    }

    merged.set(time, {
      time,
      open,
      high: Math.max(high, open, close),
      low: Math.min(low, open, close),
      close,
      volume: Math.max(toPrice(item?.volume), 0),
    });
  });

  return [...merged.values()].sort((left, right) => left.time - right.time);
}

function getHistorySignature(history) {
  if (!history || history.length === 0) {
    return 'empty';
  }

  const first = history[0];
  const last = history[history.length - 1];
  return [
    history.length,
    first.time,
    first.open,
    last.time,
    last.open,
    last.high,
    last.low,
    last.close,
    last.volume,
  ].join('|');
}

function calculateMovingAverageSeries(data, period) {
  return data
    .map((item, index) => {
      if (index < period - 1) {
        return null;
      }

      const slice = data.slice(index - period + 1, index + 1);
      const avg = slice.reduce((sum, entry) => sum + toPrice(entry.close), 0) / period;

      return {
        time: item.time,
        value: avg,
      };
    })
    .filter(Boolean);
}

function PriceChart({ priceHistory, currentPrice, symbol, timeframe, ticker, openPrice, prevTicker }) {
  const { t } = useTranslation();
  const containerRef = useRef(null);
  const chartRef = useRef(null);
  const seriesRef = useRef(null);
  const volumeSeriesRef = useRef(null);
  const ma5SeriesRef = useRef(null);
  const ma10SeriesRef = useRef(null);
  const priceHistoryRef = useRef([]);
  const lastHistorySignatureRef = useRef('empty');
  const lastRealtimeBarRef = useRef(null);
  const lastSymbolRef = useRef(null);
  const hasAutoFittedRef = useRef(false);
  const [hasData, setHasData] = useState(false);
  const [hoverData, setHoverData] = useState(null);

  const normalizedHistory = useMemo(() => normalizeHistory(priceHistory), [priceHistory]);
  const historySignature = useMemo(() => getHistorySignature(normalizedHistory), [normalizedHistory]);

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
      bars: normalizedHistory.length,
    };
  }, [ticker, currentPrice, openPrice, prevTicker, normalizedHistory.length]);

  const latestBar = (() => {
    if (normalizedHistory.length === 0) return null;
    const lastIndex = normalizedHistory.length - 1;
    const current = normalizedHistory[lastIndex];
    const previous = lastIndex > 0 ? normalizedHistory[lastIndex - 1] : null;
    const realtimeBar = lastRealtimeBarRef.current;
    const source = realtimeBar && realtimeBar.time >= current.time ? realtimeBar : current;

    return {
      ...source,
      previousClose: previous ? Number(previous.close ?? 0) : Number(source?.open ?? 0),
    };
  })();

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
    priceHistoryRef.current = normalizedHistory;
  }, [normalizedHistory]);

  useEffect(() => {
    if (!containerRef.current || chartRef.current) return;

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
      priceFormat: { type: 'volume' },
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
        ? history.findIndex((item) => item.time === time)
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

    const handleResize = () => {
      try {
        if (containerRef.current && chartRef.current) {
          chartRef.current.applyOptions({
            width: containerRef.current.clientWidth,
          });
        }
      } catch (_error) {
        // Ignore resize errors.
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

  useEffect(() => {
    if (!seriesRef.current || !volumeSeriesRef.current || !ma5SeriesRef.current || !ma10SeriesRef.current) return;

    if (lastSymbolRef.current !== (symbol || null)) {
      lastSymbolRef.current = symbol || null;
      lastHistorySignatureRef.current = 'empty';
      lastRealtimeBarRef.current = null;
      hasAutoFittedRef.current = false;
    }

    if (normalizedHistory.length === 0) {
      setHasData(false);
      return;
    }

    if (lastHistorySignatureRef.current === historySignature) {
      setHasData(true);
      return;
    }

    const enrichedHistory = normalizedHistory.map((item, index) => ({
      ...item,
      previousClose: index > 0 ? toPrice(normalizedHistory[index - 1]?.close) : toPrice(item.open),
    }));

    const candleData = enrichedHistory.map((item) => ({
      time: item.time,
      open: item.open,
      high: item.high,
      low: item.low,
      close: item.close,
    }));

    const volumeData = enrichedHistory
      .map((item) => ({
        time: item.time,
        value: item.volume,
        color: item.close >= item.open ? 'rgba(34, 197, 94, 0.55)' : 'rgba(239, 68, 68, 0.55)',
      }))
      .filter((item) => item.value > 0);

    seriesRef.current.setData(candleData);
    volumeSeriesRef.current.setData(volumeData);
    ma5SeriesRef.current.setData(calculateMovingAverageSeries(enrichedHistory, 5));
    ma10SeriesRef.current.setData(calculateMovingAverageSeries(enrichedHistory, 10));
    lastHistorySignatureRef.current = historySignature;
    lastRealtimeBarRef.current = candleData[candleData.length - 1] || null;
    setHasData(candleData.length > 0);

    if (!hasAutoFittedRef.current) {
      try {
        chartRef.current?.timeScale().fitContent();
        hasAutoFittedRef.current = true;
      } catch (_error) {
        // Ignore fit errors.
      }
    }
  }, [historySignature, normalizedHistory, symbol]);

  useEffect(() => {
    if (!seriesRef.current) return;

    const price = toPrice(currentPrice);
    if (price <= 0) return;

    const history = priceHistoryRef.current;
    const lastBar = history.length > 0 ? history[history.length - 1] : null;
    const referenceTime = ticker?.timestamp ? toChartTime(ticker.timestamp) : Math.floor(Date.now() / 1000);
    const timeframeSeconds = getTimeframeSeconds(timeframe);
    const alignedTime = referenceTime - (referenceTime % timeframeSeconds);
    const candleTime = lastBar && alignedTime <= lastBar.time + timeframeSeconds - 1
      ? lastBar.time
      : alignedTime;
    const baseOpen = lastBar?.open ?? lastRealtimeBarRef.current?.open ?? price;
    const baseHigh = lastBar?.high ?? lastRealtimeBarRef.current?.high ?? price;
    const baseLow = lastBar?.low ?? lastRealtimeBarRef.current?.low ?? price;
    const volume = lastBar?.volume ?? lastRealtimeBarRef.current?.volume ?? 0;

    const nextBar = {
      time: candleTime,
      open: baseOpen,
      high: Math.max(baseHigh, price),
      low: Math.min(baseLow, price),
      close: price,
      volume,
    };

    lastRealtimeBarRef.current = nextBar;
    seriesRef.current.update(nextBar);
    setHasData(true);
  }, [currentPrice, ticker?.timestamp, timeframe]);

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
        {!hasData && normalizedHistory.length === 0 && (
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
}

function arePropsEqual(previousProps, nextProps) {
  return previousProps.symbol === nextProps.symbol
    && previousProps.timeframe === nextProps.timeframe
    && previousProps.currentPrice === nextProps.currentPrice
    && previousProps.openPrice === nextProps.openPrice
    && previousProps.priceHistory === nextProps.priceHistory
    && previousProps.ticker === nextProps.ticker
    && previousProps.prevTicker === nextProps.prevTicker;
}

export default memo(PriceChart, arePropsEqual);
