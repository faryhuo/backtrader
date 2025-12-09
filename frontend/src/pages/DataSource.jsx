import { useState } from 'react';
import { useTranslation } from 'react-i18next';
import { api } from '../services/api';
import CandleStickChart from '../components/CandleStickChart';

function DataSource() {
    const { t } = useTranslation();
    const [ticker, setTicker] = useState('AAPL');
    const [startDate, setStartDate] = useState('2023-01-01');
    const [endDate, setEndDate] = useState('2023-12-31');
    const [chartData, setChartData] = useState([]);
    const [loading, setLoading] = useState(false);
    const [error, setError] = useState(null);

    const handleFetchData = async (e) => {
        e.preventDefault();
        setLoading(true);
        setError(null);
        setChartData([]);

        try {
            const response = await api.fetchMarketData({
                ticker,
                start_date: startDate,
                end_date: endDate
            });
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
            <section className="card">
                <h2>{t('datasource.title')}</h2>
                <form onSubmit={handleFetchData} className="form-grid">
                    <div className="form-group">
                        <label htmlFor="ticker">{t('config_form.asset_ticker')}</label>
                        <input
                            id="ticker"
                            type="text"
                            value={ticker}
                            onChange={(e) => setTicker(e.target.value)}
                            required
                        />
                    </div>
                    <div className="form-group">
                        <label htmlFor="start-date">{t('config_form.start_date')}</label>
                        <input
                            id="start-date"
                            type="date"
                            value={startDate}
                            onChange={(e) => setStartDate(e.target.value)}
                            required
                        />
                    </div>
                    <div className="form-group">
                        <label htmlFor="end-date">{t('config_form.end_date')}</label>
                        <input
                            id="end-date"
                            type="date"
                            value={endDate}
                            onChange={(e) => setEndDate(e.target.value)}
                            required
                        />
                    </div>
                    <div className="form-actions">
                        <button type="submit" className="btn-primary" disabled={loading}>
                            {loading ? <span className="spinner"></span> : t('datasource.fetch_data')}
                        </button>
                    </div>
                </form>

                {error && <div className="error-message" style={{ marginTop: '1rem' }}>{error}</div>}
            </section>

            {chartData.length > 0 && (
                <section className="card">
                     <div style={{ marginBottom: '1rem', display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}>
                        <h3>{ticker} Price History</h3>
                        <span className="muted">{chartData.length} candles</span>
                    </div>
                    <CandleStickChart data={chartData} />
                </section>
            )}
        </div>
    );
}

export default DataSource;
