import { useState } from 'react';
import { useTranslation } from 'react-i18next';
import { api } from '../services/api';
import CandleStickChart from '../components/DataSource/CandleStickChart';
import DataSourceConfigForm from '../components/DataSource/DataSourceConfigForm';
import TickerInfoPanel from '../components/DataSource/TickerInfoPanel';

function DataSource() {
    const { t } = useTranslation();
    const [ticker, setTicker] = useState('AAPL');
    const [startDate, setStartDate] = useState('2023-01-01');
    const [endDate, setEndDate] = useState('2023-12-31');
    const [chartData, setChartData] = useState([]);
    const [tickerInfo, setTickerInfo] = useState(null);
    const [loading, setLoading] = useState(false);
    const [error, setError] = useState(null);

    const handleFetchData = async (e) => {
        e.preventDefault();
        setLoading(true);
        setError(null);
        setChartData([]);
        setTickerInfo(null);

        try {
            const response = await api.fetchMarketData({
                ticker,
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
                setError('No data found for the given parameters.');
            }
        } catch (err) {
            console.error(err);
            setError(err.message || 'Failed to fetch data.');
        } finally {
            setLoading(false);
        }
    };

    return (
        <div className="page-container">
            <DataSourceConfigForm
                ticker={ticker}
                setTicker={setTicker}
                startDate={startDate}
                setStartDate={setStartDate}
                endDate={endDate}
                setEndDate={setEndDate}
                loading={loading}
                onSubmit={handleFetchData}
                error={error}
            />

            {(chartData.length > 0 || tickerInfo) && (
                <div className="datasource-results-grid">
                    {/* Left Column: Ticker Info Panel */}
                    {tickerInfo && (
                        <div className="ticker-info-column">
                            <TickerInfoPanel tickerInfo={tickerInfo} />
                        </div>
                    )}

                    {/* Right Column: Chart */}
                    {chartData.length > 0 && (
                        <div className="chart-column">
                            <section className="card results-animate-in">
                                <div style={{ marginBottom: '1rem', display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}>
                                    <h3>{ticker} Price History</h3>
                                    <span className="muted">{chartData.length} candles</span>
                                </div>
                                <CandleStickChart data={chartData} />
                            </section>
                        </div>
                    )}
                </div>
            )}
        </div>
    );
}

export default DataSource;
