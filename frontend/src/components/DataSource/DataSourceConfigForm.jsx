import PropTypes from 'prop-types';
import { useTranslation } from 'react-i18next';
import { 
    CalendarOutlined, 
    StockOutlined, 
    CloudDownloadOutlined
} from '@ant-design/icons';

function DataSourceConfigForm({
    ticker,
    setTicker,
    startDate,
    setStartDate,
    endDate,
    setEndDate,
    loading,
    onSubmit,
    error
}) {
    const { t } = useTranslation();

    return (
        <section className="card form-card-enhanced">
            <h2><CloudDownloadOutlined /> {t('datasource.title')}</h2>
            <form onSubmit={onSubmit}>
                <div className="form-grid">
                    <div className="form-group">
                        <label htmlFor="ticker">{t('config_form.asset_ticker')}</label>
                        <div className="input-with-icon">
                            <StockOutlined className="input-icon" />
                            <input
                                id="ticker"
                                type="text"
                                value={ticker}
                                onChange={(e) => setTicker(e.target.value)}
                                required
                            />
                        </div>
                    </div>

                    <div className="form-group">
                        <label htmlFor="start-date">{t('config_form.start_date')}</label>
                        <div className="input-with-icon">
                            <CalendarOutlined className="input-icon" />
                            <input
                                id="start-date"
                                type="date"
                                value={startDate}
                                onChange={(e) => setStartDate(e.target.value)}
                                required
                            />
                        </div>
                    </div>

                    <div className="form-group">
                        <label htmlFor="end-date">{t('config_form.end_date')}</label>
                        <div className="input-with-icon">
                            <CalendarOutlined className="input-icon" />
                            <input
                                id="end-date"
                                type="date"
                                value={endDate}
                                onChange={(e) => setEndDate(e.target.value)}
                                required
                            />
                        </div>
                    </div>
                </div>

                <div className="form-actions-enhanced">
                    <button type="submit" className="btn-primary glow-effect" disabled={loading}>
                        {loading ? <span className="spinner-sm"></span> : t('datasource.fetch_data')}
                    </button>
                </div>
            </form>

            {error && (
                <div className="error-message-enhanced">
                    <span>⚠️ {error}</span>
                </div>
            )}
        </section>
    );
}

DataSourceConfigForm.propTypes = {
    ticker: PropTypes.string.isRequired,
    setTicker: PropTypes.func.isRequired,
    startDate: PropTypes.string.isRequired,
    setStartDate: PropTypes.func.isRequired,
    endDate: PropTypes.string.isRequired,
    setEndDate: PropTypes.func.isRequired,
    loading: PropTypes.bool.isRequired,
    onSubmit: PropTypes.func.isRequired,
    error: PropTypes.string
};

export default DataSourceConfigForm;
