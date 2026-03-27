import { useState } from 'react';
import PropTypes from 'prop-types';
import { InfoCircleOutlined } from '@ant-design/icons';
import { Alert, Empty, Image, Segmented, Space, Tooltip, Typography } from 'antd';
import ReactECharts from 'echarts-for-react';


const UP_COLOR = '#22c55e';
const DOWN_COLOR = '#ef4444';
const OVERLAY_COLORS = ['#38bdf8', '#f59e0b', '#a78bfa', '#f97316', '#14b8a6', '#f472b6'];
const SUBPLOT_COLORS = ['#60a5fa', '#facc15', '#c084fc', '#34d399', '#fb7185', '#22d3ee'];
const AXIS_TEXT_COLOR = '#cbd5e1';
const AXIS_MUTED_COLOR = '#94a3b8';
const PANE_LABEL_BG = 'rgba(15, 23, 42, 0.88)';
const PANE_LABEL_BORDER = 'rgba(148, 163, 184, 0.3)';
const { Text } = Typography;


function StrategyPlot({ result, t }) {
    const [renderMode, setRenderMode] = useState('ui');
    const chartData = result?.chart_data || result?.metrics?.chart_data || null;
    const hasUiChart = Boolean(chartData?.ohlcv?.length);
    const hasImageChart = Boolean(result?.plot_url);
    const effectiveRenderMode = resolveRenderMode(renderMode, hasUiChart, hasImageChart);
    const chartSummary = buildChartSummary(chartData, t);
    const availabilityNotice = buildAvailabilityNotice({
        hasUiChart,
        hasImageChart,
        t,
    });

    if (hasUiChart || hasImageChart) {
        return (
            <div className="card plot-card">
                <div className="strategy-chart-toolbar">
                    <Space size="middle" wrap>
                        <Text type="secondary">
                            {t?.('history.render_mode', 'Render Mode')}
                        </Text>
                        <Segmented
                            size="small"
                            value={effectiveRenderMode}
                            onChange={setRenderMode}
                            options={[
                                {
                                    label: hasUiChart
                                        ? t?.('history.render_mode_ui', 'UI Chart')
                                        : t?.('history.render_mode_ui_unavailable', 'UI Chart unavailable'),
                                    value: 'ui',
                                    disabled: !hasUiChart,
                                },
                                {
                                    label: hasImageChart
                                        ? t?.('history.render_mode_image', 'Backtrader Image')
                                        : t?.('history.render_mode_image_unavailable', 'Backtrader Image unavailable'),
                                    value: 'image',
                                    disabled: !hasImageChart,
                                },
                            ]}
                        />
                        {hasUiChart && (
                            <>
                                <Tooltip
                                    placement="bottomLeft"
                                    title={buildChartLegendHelp(t)}
                                    overlayClassName="strategy-chart-help-tooltip"
                                >
                                    <InfoCircleOutlined className="strategy-chart-help-icon" />
                                </Tooltip>
                                <Text type="secondary" className="strategy-chart-summary">
                                    {chartSummary}
                                </Text>
                            </>
                        )}
                    </Space>
                </div>

                {availabilityNotice && (
                    <Alert
                        style={{ marginBottom: 16 }}
                        type={availabilityNotice.type}
                        showIcon
                        message={availabilityNotice.title}
                        description={availabilityNotice.description}
                    />
                )}

                <div className="plot-container dark-mode strategy-chart-container">
                    {(effectiveRenderMode === 'ui' && hasUiChart) ? (
                        <ReactECharts
                            option={buildChartOption(chartData, t)}
                            style={{ width: '100%', height: buildChartHeight(chartData) }}
                            notMerge
                            lazyUpdate
                        />
                    ) : (
                        <Image
                            src={result.plot_url}
                            alt={t?.('history.strategy_plot_alt', 'Strategy Plot')}
                            style={{ maxWidth: '100%' }}
                        />
                    )}
                </div>
            </div>
        );
    }

    return (
        <div className="card plot-card">
            <Alert
                style={{ marginBottom: 16 }}
                type="warning"
                showIcon
                message={t?.('history.chart_all_unavailable_title', 'No chart output is available')}
                description={t?.(
                    'history.chart_all_unavailable_desc',
                    'This run did not return structured UI chart data or a Backtrader image. Check the task error details or rerun the strategy.'
                )}
            />
            <div className="plot-container dark-mode strategy-chart-empty">
                <Empty description={t?.('history.chart_data_unavailable', 'Chart data is not available.')} />
            </div>
        </div>
    );
}


function resolveRenderMode(renderMode, hasUiChart, hasImageChart) {
    if (renderMode === 'image' && hasImageChart) {
        return 'image';
    }
    if (renderMode === 'ui' && hasUiChart) {
        return 'ui';
    }
    if (hasUiChart) {
        return 'ui';
    }
    if (hasImageChart) {
        return 'image';
    }
    return 'ui';
}


function buildAvailabilityNotice({ hasUiChart, hasImageChart, t }) {
    if (hasUiChart && hasImageChart) {
        return null;
    }

    if (hasImageChart && !hasUiChart) {
        return {
            type: 'info',
            title: t?.('history.chart_ui_unavailable_title', 'UI chart is unavailable for this run'),
            description: t?.(
                'history.chart_ui_unavailable_desc',
                'The backend returned a Backtrader image, but it did not return structured chart data for browser rendering.'
            ),
        };
    }

    if (hasUiChart && !hasImageChart) {
        return {
            type: 'warning',
            title: t?.('history.chart_image_unavailable_title', 'Backtrader image is unavailable for this run'),
            description: t?.(
                'history.chart_image_unavailable_desc',
                'The UI chart was rendered from structured data, but the server did not generate a Backtrader image.'
            ),
        };
    }

    return null;
}


function buildChartSummary(chartData, t) {
    if (!chartData) {
        return '';
    }

    const candleCount = chartData.ohlcv?.length || 0;
    const indicatorCount = chartData.indicators?.length || 0;
    const signalCount = chartData.markers?.length || 0;
    const equityCount = chartData.equity_curve?.length || 0;

    return t?.('history.chart_summary', {
        candles: candleCount,
        indicators: indicatorCount,
        signals: signalCount,
        equityPoints: equityCount,
        defaultValue: '{{candles}} candles | {{indicators}} indicators | {{signals}} signals | {{equityPoints}} equity points',
    }) || '';
}


function buildChartLegendHelp(t) {
    return (
        <div className="strategy-chart-help-content">
            <div className="strategy-chart-help-title">
                {t?.('history.chart_panels_title', 'Chart Panels')}
            </div>
            <div>
                <strong>{t?.('history.price_chart', 'Price')}:</strong>{' '}
                {t?.('history.chart_panel_price_desc', 'Candlesticks, overlay indicators, and buy/sell markers on the main price pane.')}
            </div>
            <div>
                <strong>{t?.('history.volume', 'Volume')}:</strong>{' '}
                {t?.('history.chart_panel_volume_desc', 'Trading volume bars for each candle.')}
            </div>
            <div>
                <strong>Broker:</strong>{' '}
                {t?.('history.chart_panel_broker_desc', 'Broker observer lines showing available cash and total portfolio value over time.')}
            </div>
            <div>
                <strong>Trades:</strong>{' '}
                {t?.('history.chart_panel_trades_desc', 'Trade observer bars showing profit and loss from closed trades.')}
            </div>
            <div>
                <strong>{t?.('history.equity_curve', 'Equity Curve')}:</strong>{' '}
                {t?.('history.chart_panel_equity_desc', 'Overall account equity trend across the backtest.')}
            </div>
        </div>
    );
}


function buildChartHeight(chartData) {
    const subplotCount = (chartData.indicators || []).filter(indicator => indicator.subplot).length;
    const hasEquity = (chartData.equity_curve || []).length > 0;
    return 560 + (subplotCount * 190) + (hasEquity ? 190 : 0);
}


function buildChartOption(chartData, t) {
    const ohlcv = chartData.ohlcv || [];
    const equityCurve = chartData.equity_curve || [];
    const indicators = chartData.indicators || [];
    const overlayIndicators = indicators.filter(indicator => !indicator.subplot);
    const subplotIndicators = indicators.filter(indicator => indicator.subplot);
    const categories = ohlcv.map(item => item.time);
    const hasEquity = equityCurve.length > 0;

    const panes = [
        { key: 'price', weight: 4.4 },
        { key: 'volume', weight: 1.5 },
        ...subplotIndicators.map((indicator) => ({ key: indicator.id, weight: 1.8, indicator })),
        ...(hasEquity ? [{ key: 'equity', weight: 1.8 }] : []),
    ];

    const layout = buildPaneLayout(panes);
    const grids = layout.map((pane) => ({
        left: 88,
        right: 24,
        top: `${pane.top + 1.6}%`,
        height: `${pane.height}%`,
        containLabel: true,
    }));

    const xAxis = layout.map((pane, index) => ({
        type: 'category',
        gridIndex: index,
        data: pane.key === 'equity' ? equityCurve.map(item => item.time) : categories,
        boundaryGap: pane.key !== 'equity',
        axisLine: { lineStyle: { color: '#475569' } },
        axisLabel: {
            color: AXIS_MUTED_COLOR,
            hideOverlap: true,
            margin: 10,
            show: index === layout.length - 1,
        },
        splitLine: { show: false },
        min: 'dataMin',
        max: 'dataMax',
    }));

    const yAxis = layout.map((pane) => ({
        gridIndex: pane.gridIndex,
        scale: true,
        splitNumber: pane.key === 'price' ? 4 : 3,
        nameLocation: 'end',
        nameGap: 18,
        axisLine: { lineStyle: { color: '#475569' } },
        axisLabel: {
            color: AXIS_MUTED_COLOR,
            margin: 12,
        },
        splitLine: { lineStyle: { color: 'rgba(148, 163, 184, 0.12)' } },
        name: resolvePaneName(pane, t),
        nameTextStyle: {
            color: AXIS_TEXT_COLOR,
            fontSize: 12,
            fontWeight: 700,
            align: 'left',
            verticalAlign: 'bottom',
            backgroundColor: PANE_LABEL_BG,
            borderColor: PANE_LABEL_BORDER,
            borderWidth: 1,
            borderRadius: 6,
            padding: [4, 8, 4, 8],
        },
        ...(pane.key === 'volume' ? { axisLabel: { color: AXIS_MUTED_COLOR, margin: 12, formatter: formatCompactNumber } } : {}),
        ...(pane.key === 'equity' ? { axisLabel: { color: AXIS_MUTED_COLOR, margin: 12, formatter: value => `$${formatCompactNumber(value)}` } } : {}),
    }));

    const dataZoomAxisIndex = layout.map((_, index) => index);
    const series = [];
    const legendItems = [];

    series.push({
        name: t?.('history.tab_chart', 'Chart'),
        type: 'candlestick',
        xAxisIndex: 0,
        yAxisIndex: 0,
        itemStyle: {
            color: UP_COLOR,
            color0: DOWN_COLOR,
            borderColor: UP_COLOR,
            borderColor0: DOWN_COLOR,
        },
        data: ohlcv.map(item => [item.open, item.close, item.low, item.high]),
        tooltip: {
            formatter: (params) => buildCandlestickTooltip(params, t),
        },
    });
    legendItems.push(t?.('history.tab_chart', 'Chart'));

    series.push({
        name: t?.('history.volume', 'Volume'),
        type: 'bar',
        xAxisIndex: 1,
        yAxisIndex: 1,
        barWidth: '70%',
        data: ohlcv.map(item => ({
            value: item.volume,
            itemStyle: {
                color: item.close >= item.open ? `${UP_COLOR}99` : `${DOWN_COLOR}99`,
            },
        })),
    });
    legendItems.push(t?.('history.volume', 'Volume'));

    overlayIndicators.forEach((indicator, indicatorIndex) => {
        indicator.lines.forEach((line, lineIndex) => {
            const seriesName = resolveSeriesName(indicator, line, t);
            series.push({
                name: seriesName,
                type: 'line',
                xAxisIndex: 0,
                yAxisIndex: 0,
                showSymbol: false,
                smooth: false,
                lineStyle: {
                    width: 1.5,
                    color: OVERLAY_COLORS[(indicatorIndex + lineIndex) % OVERLAY_COLORS.length],
                },
                data: line.data.map(item => [item.time, item.value]),
            });
            legendItems.push(seriesName);
        });
    });

    const tradeMarkers = chartData.markers || [];
    const buyMarkers = tradeMarkers.filter(marker => marker.side === 'buy');
    const sellMarkers = tradeMarkers.filter(marker => marker.side === 'sell');

    if (buyMarkers.length) {
        series.push({
            name: t?.('history.buy_markers', 'Buy'),
            type: 'scatter',
            xAxisIndex: 0,
            yAxisIndex: 0,
            symbol: 'triangle',
            symbolSize: 14,
            itemStyle: { color: UP_COLOR },
            label: {
                show: true,
                formatter: 'B',
                position: 'top',
                color: UP_COLOR,
                fontWeight: 700,
                fontSize: 11,
            },
            data: buyMarkers.map(marker => ({
                value: [marker.time, marker.value],
                label: marker.label,
                size: marker.size,
            })),
            tooltip: {
                formatter: (params) => buildMarkerTooltip(params, t),
            },
        });
        legendItems.push(t?.('history.buy_markers', 'Buy'));
    }

    if (sellMarkers.length) {
        series.push({
            name: t?.('history.sell_markers', 'Sell'),
            type: 'scatter',
            xAxisIndex: 0,
            yAxisIndex: 0,
            symbol: 'triangle',
            symbolRotate: 180,
            symbolSize: 14,
            itemStyle: { color: DOWN_COLOR },
            label: {
                show: true,
                formatter: 'S',
                position: 'bottom',
                color: DOWN_COLOR,
                fontWeight: 700,
                fontSize: 11,
            },
            data: sellMarkers.map(marker => ({
                value: [marker.time, marker.value],
                label: marker.label,
                pnl: marker.pnl,
                size: marker.size,
            })),
            tooltip: {
                formatter: (params) => buildMarkerTooltip(params, t),
            },
        });
        legendItems.push(t?.('history.sell_markers', 'Sell'));
    }

    subplotIndicators.forEach((indicator, subplotIndex) => {
        const paneIndex = subplotIndex + 2;
        indicator.lines.forEach((line, lineIndex) => {
            const seriesName = resolveSeriesName(indicator, line, t);
            series.push({
                name: seriesName,
                type: line.series_type || 'line',
                xAxisIndex: paneIndex,
                yAxisIndex: paneIndex,
                showSymbol: false,
                lineStyle: {
                    width: 1.5,
                    color: SUBPLOT_COLORS[(subplotIndex + lineIndex) % SUBPLOT_COLORS.length],
                },
                itemStyle: {
                    color: SUBPLOT_COLORS[(subplotIndex + lineIndex) % SUBPLOT_COLORS.length],
                },
                data: line.data.map(item => [item.time, item.value]),
            });
            legendItems.push(seriesName);
        });
    });

    if (hasEquity) {
        const equityPaneIndex = layout.length - 1;
        series.push({
            name: t?.('history.equity_curve', 'Equity Curve'),
            type: 'line',
            xAxisIndex: equityPaneIndex,
            yAxisIndex: equityPaneIndex,
            showSymbol: false,
            lineStyle: {
                width: 2,
                color: '#38bdf8',
            },
            areaStyle: {
                color: 'rgba(56, 189, 248, 0.18)',
            },
            data: equityCurve.map(item => [item.time, item.value]),
        });
        legendItems.push(t?.('history.equity_curve', 'Equity Curve'));
    }

    return {
        animation: false,
        backgroundColor: 'transparent',
        legend: {
            top: 8,
            textStyle: { color: '#cbd5e1' },
            data: legendItems,
        },
        grid: grids,
        xAxis,
        yAxis,
        axisPointer: {
            link: xAxis.map((_, index) => ({ xAxisIndex: index })),
        },
        dataZoom: [
            {
                type: 'inside',
                xAxisIndex: dataZoomAxisIndex,
                start: 0,
                end: 100,
            },
            {
                type: 'slider',
                xAxisIndex: dataZoomAxisIndex,
                bottom: 8,
                height: 22,
                borderColor: 'rgba(148, 163, 184, 0.24)',
                fillerColor: 'rgba(56, 189, 248, 0.18)',
                handleStyle: { color: '#38bdf8' },
                textStyle: { color: '#94a3b8' },
            },
        ],
        tooltip: {
            trigger: 'axis',
            backgroundColor: 'rgba(15, 23, 42, 0.92)',
            borderColor: 'rgba(148, 163, 184, 0.24)',
            textStyle: { color: '#e2e8f0' },
        },
        series,
    };
}


function buildPaneLayout(panes) {
    const topPadding = 9;
    const bottomPadding = 8;
    const gap = 3;
    const totalGap = gap * Math.max(panes.length - 1, 0);
    const usableHeight = 100 - topPadding - bottomPadding - totalGap;
    const totalWeight = panes.reduce((sum, pane) => sum + pane.weight, 0);

    let currentTop = topPadding;
    return panes.map((pane, index) => {
        const height = (pane.weight / totalWeight) * usableHeight;
        const currentPane = { ...pane, top: currentTop, height, gridIndex: index };
        currentTop += height + gap;
        return currentPane;
    });
}


function buildMarkerTooltip(params, t) {
    const point = params?.data || {};
    const [time, price] = point.value || [];
    const lines = [
        `<strong>${params.seriesName}</strong>`,
        `${t?.('history.run_date', 'Date')}: ${time ?? '-'}`,
        `${t?.('trade_log.entry_price', 'Price')}: ${formatPrice(price)}`,
    ];

    if (point.size !== undefined && point.size !== null) {
        lines.push(`${t?.('trade_log.size', 'Size')}: ${point.size}`);
    }

    if (point.pnl !== undefined && point.pnl !== null) {
        const pnlColor = point.pnl >= 0 ? UP_COLOR : DOWN_COLOR;
        lines.push(`${t?.('trade_log.net_pnl', 'Net PnL')}: <span style="color:${pnlColor}">${formatPrice(point.pnl)}</span>`);
    }

    return lines.join('<br/>');
}


function buildCandlestickTooltip(params, t) {
    const point = params?.data || [];
    const axisValue = params?.axisValueLabel ?? params?.axisValue ?? '-';

    return [
        `<strong>${t?.('history.tab_chart', 'Chart')}</strong>`,
        `${t?.('history.run_date', 'Date')}: ${axisValue}`,
        `${t?.('history.ohlc_open', 'Open')}: ${formatPrice(point[0])}`,
        `${t?.('history.ohlc_close', 'Close')}: ${formatPrice(point[1])}`,
        `${t?.('history.ohlc_low', 'Low')}: ${formatPrice(point[2])}`,
        `${t?.('history.ohlc_high', 'High')}: ${formatPrice(point[3])}`,
    ].join('<br/>');
}


function resolveSeriesName(indicator, line, t) {
    const indicatorName = indicator?.name || '';
    const lineName = line?.name || '';

    if (indicatorName === 'Broker' && lineName === 'cash') {
        return t?.('history.broker_cash', 'Broker cash');
    }
    if (indicatorName === 'Broker' && lineName === 'value') {
        return t?.('history.broker_value', 'Broker value');
    }

    return `${indicatorName} ${lineName}`.trim();
}


function resolvePaneName(pane, t) {
    if (pane.key === 'price') {
        return t?.('history.price_chart', 'Price');
    }
    if (pane.key === 'volume') {
        return t?.('history.volume', 'Volume');
    }
    if (pane.key === 'equity') {
        return t?.('history.equity_curve', 'Equity');
    }
    return pane.indicator?.name || '';
}


function formatCompactNumber(value) {
    if (value >= 1000000) {
        return `${(value / 1000000).toFixed(1)}M`;
    }
    if (value >= 1000) {
        return `${(value / 1000).toFixed(1)}K`;
    }
    return Number(value).toFixed(0);
}


function formatPrice(value) {
    if (value === undefined || value === null || Number.isNaN(Number(value))) {
        return '-';
    }
    return `$${Number(value).toLocaleString(undefined, {
        minimumFractionDigits: 2,
        maximumFractionDigits: 2,
    })}`;
}


StrategyPlot.propTypes = {
    result: PropTypes.shape({
        plot_url: PropTypes.string,
        chart_data: PropTypes.object,
        metrics: PropTypes.object,
    }),
    t: PropTypes.func,
};

export default StrategyPlot;
