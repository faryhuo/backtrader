import { useState, useCallback } from 'react';
import { useTranslation } from 'react-i18next';
import { message } from 'antd';
import { api } from '../services/api';
import CandleStickChart from '../components/DataSource/CandleStickChart';
import DataSourceConfigForm from '../components/DataSource/DataSourceConfigForm';
import TickerInfoPanel from '../components/DataSource/TickerInfoPanel';
import QuickPicks from '../components/DataSource/QuickPicks';
import ChartToolbar from '../components/DataSource/ChartToolbar';
import IndicatorsPanel from '../components/DataSource/IndicatorsPanel';
import { exportToExcel, exportChartAsImage, generateFilename } from '../utils/exportUtils';
import './DataSource.css';

// Helper to get default date range (last 1 month)
const getDefaultDateRange = () => {
    const today = new Date();
    const startDate = new Date(today);
    startDate.setMonth(today.getMonth() - 1);
    return {
        start: startDate.toISOString().split('T')[0],
        end: today.toISOString().split('T')[0]
    };
};

function DataSource() {
    const { t } = useTranslation();
    const defaultRange = getDefaultDateRange();

    const [ticker, setTicker] = useState('AAPL');
    const [startDate, setStartDate] = useState(defaultRange.start);
    const [endDate, setEndDate] = useState(defaultRange.end);
    const [chartData, setChartData] = useState([]);
    const [tickerInfo, setTickerInfo] = useState(null);
    const [loading, setLoading] = useState(false);
    const [error, setError] = useState(null);

    // Chart settings
    const [chartType, setChartType] = useState('candlestick');
    const [timeRange, setTimeRange] = useState('1m'); // Default to 1 month
    const [indicators, setIndicators] = useState({
        volume: false,
        ma5: false,
        ma10: false,
        ma20: false,
        ma50: false
    });

    const fetchData = useCallback(async (overrideTicker) => {
        const tickerToFetch = overrideTicker || ticker;
        setLoading(true);
        setError(null);

        try {
            const response = await api.fetchMarketData({
                ticker: tickerToFetch,
                start_date: startDate,
                end_date: endDate
            });

            // Extract ticker info
            if (response.ticker_info) {
                setTickerInfo(response.ticker_info);
            }

            // Extract chart data
            if (response.data && response.data.length > 0) {
                setChartData(response.data);
            } else {
                setError(t('datasource.errors.no_data_found', 'No data found for the given parameters.'));
            }
        } catch (err) {
            console.error(err);
            setError(err.message || t('datasource.errors.fetch_failed', 'Failed to fetch data.'));
        } finally {
            setLoading(false);
        }
    }, [ticker, startDate, endDate, t]);

    const handleFetchData = async (e) => {
        if (e) e.preventDefault();
        await fetchData();
    };

    const handleQuickPickSelect = (selectedTicker) => {
        setTicker(selectedTicker);
        // Immediately fetch with the new ticker
        fetchData(selectedTicker);
    };

    const handleTimeRangeChange = (range) => {
        setStartDate(range.start);
        setEndDate(range.end);
        setTimeRange(range.range);
    };

    const handleExportData = async () => {
        if (!chartData || chartData.length === 0) {
            message.warning(t('datasource.no_data'));
            return;
        }

        try {
            // Export to Excel (with CSV fallback)
            const filename = generateFilename(ticker, '.xlsx');
            await exportToExcel(chartData, filename, tickerInfo);
            message.success(t('datasource.export_success'));
        } catch (error) {
            console.error('Export failed:', error);
            message.error(t('datasource.export_failed'));
        }
    };

    const handleExportImage = async () => {
        const chartElement = document.querySelector('.chart-card');
        if (!chartElement) {
            message.warning(t('datasource.chart_not_found', 'Chart not found'));
            return;
        }

        try {
            const filename = generateFilename(ticker, '.png');
            await exportChartAsImage(chartElement, filename);
            message.success(t('datasource.export_success'));
        } catch (error) {
            console.error('Export image failed:', error);
            message.error(t('datasource.export_failed'));
        }
    };

    return (
        <div className="page-container datasource-page">
            {/* Main Layout */}
            <div className="datasource-layout">
                {/* Left Sidebar - Configuration */}
                <aside className="datasource-sidebar">
                    <DataSourceConfigForm
                        ticker={ticker}
                        setTicker={setTicker}
                        loading={loading}
                        onSubmit={handleFetchData}
                        error={error}
                    />

                    <QuickPicks
                        onSelectTicker={handleQuickPickSelect}
                        currentTicker={ticker}
                    />

                    {chartData.length > 0 && (
                        <IndicatorsPanel
                            indicators={indicators}
                            onIndicatorsChange={setIndicators}
                        />
                    )}
                </aside>

                {/* Main Content Area */}
                <main className="datasource-content">
                    {(chartData.length > 0 || tickerInfo) ? (
                        <div className="datasource-results">
                            {/* Ticker Info Panel */}
                            {tickerInfo && (
                                <div className="results-section">
                                    <TickerInfoPanel tickerInfo={tickerInfo} />
                                </div>
                            )}

                            {/* Chart */}
                            {chartData.length > 0 && (
                                <div className="results-section">
                                    <section className="card chart-card">
                                        <div className="chart-header">
                                            <div>
                                                <h3>{ticker} {t('datasource.price_history')}</h3>
                                                <span className="chart-meta">
                                                    {t('datasource.chart_meta', { count: chartData.length, start: startDate, end: endDate })}
                                                </span>
                                            </div>
                                        </div>

                                        <ChartToolbar
                                            onTimeRangeChange={handleTimeRangeChange}
                                            onChartTypeChange={setChartType}
                                            onExportData={handleExportData}
                                            onExportImage={handleExportImage}
                                            onFetchData={fetchData}
                                            currentChartType={chartType}
                                            currentTimeRange={timeRange}
                                            startDate={startDate}
                                            endDate={endDate}
                                        />

                                        <CandleStickChart
                                            data={chartData}
                                            chartType={chartType}
                                            indicators={indicators}
                                        />
                                    </section>
                                </div>
                            )}
                        </div>
                    ) : (
                        <div className="empty-state-container">
                            <div className="empty-state-icon">📊</div>
                            <h3>{t('datasource.no_data')}</h3>
                            <p>{t('datasource.empty_state_hint')}</p>
                        </div>
                    )}
                </main>
            </div>
        </div>
    );
}

export default DataSource;

