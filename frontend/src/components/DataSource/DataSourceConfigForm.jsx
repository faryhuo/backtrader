import PropTypes from 'prop-types';
import { useTranslation } from 'react-i18next';
import {
    StockOutlined,
    SearchOutlined
} from '@ant-design/icons';
import './DataSourceConfigForm.css';

function DataSourceConfigForm({
    ticker,
    setTicker,
    loading,
    onSubmit,
    error
}) {
    const { t } = useTranslation();

    return (
        <section className="card datasource-config-card">
            <div className="config-header">
                <h2>
                    <SearchOutlined /> {t('datasource.title')}
                </h2>
            </div>

            <form onSubmit={onSubmit}>
                <div className="search-form-row">
                    {/* Ticker Input */}
                    <div className="form-group ticker-group">
                        <div className="input-with-icon">
                            <StockOutlined className="input-icon" />
                            <input
                                id="ticker"
                                type="text"
                                value={ticker}
                                onChange={(e) => setTicker(e.target.value.toUpperCase())}
                                placeholder={t('datasource.search_placeholder')}
                                required
                            />
                        </div>
                    </div>

                    <button type="submit" className="btn-primary btn-search" disabled={loading}>
                        {loading ? (
                            <span className="spinner-sm"></span>
                        ) : (
                            <SearchOutlined />
                        )}
                    </button>
                </div>
            </form>

            {error && (
                <div className="error-message-enhanced error-animate-in">
                    <span>⚠️ {error}</span>
                </div>
            )}
        </section>
    );
}

DataSourceConfigForm.propTypes = {
    ticker: PropTypes.string.isRequired,
    setTicker: PropTypes.func.isRequired,
    loading: PropTypes.bool.isRequired,
    onSubmit: PropTypes.func.isRequired,
    error: PropTypes.string
};

export default DataSourceConfigForm;
