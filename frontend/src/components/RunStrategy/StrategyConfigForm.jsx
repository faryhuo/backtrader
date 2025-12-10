import PropTypes from 'prop-types';
import { useTranslation } from 'react-i18next';
import { 
    CalendarOutlined, 
    DollarOutlined, 
    PercentageOutlined, 
    NumberOutlined, 
    StockOutlined, 
    SyncOutlined,
    RocketOutlined 
} from '@ant-design/icons';

function StrategyConfigForm({
    strategies,
    selectedStrategy,
    setSelectedStrategy,
    fetchStrategies,
    ticker,
    setTicker,
    startDate,
    setStartDate,
    endDate,
    setEndDate,
    initialCash,
    setInitialCash,
    commission,
    setCommission,
    stake,
    setStake,
    loading,
    onSubmit,
    error
}) {
    const { t } = useTranslation();

    return (
        <section className="card form-card-enhanced">
            <h2><RocketOutlined /> {t('config_form.title')}</h2>
            <form onSubmit={onSubmit}>
                <div className="form-grid">
                    <div className="form-group strategy-select-group">
                        <label htmlFor="strategy-select">{t('config_form.strategy')}</label>
                        <div className="strategy-input-wrapper">
                            <select
                                id="strategy-select"
                                value={selectedStrategy}
                                onChange={(e) => setSelectedStrategy(e.target.value)}
                                className="styled-select"
                            >
                                {strategies.map((s) => (
                                    <option key={s} value={s}>{s}</option>
                                ))}
                            </select>
                            <button
                                type="button"
                                className="icon-btn"
                                onClick={fetchStrategies}
                                title={t('config_form.refresh')}
                            >
                                <SyncOutlined />
                            </button>
                        </div>
                    </div>

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

                    <div className="form-group">
                        <label htmlFor="initial-cash">{t('config_form.initial_capital')}</label>
                        <div className="input-with-icon">
                            <DollarOutlined className="input-icon" />
                            <input
                                id="initial-cash"
                                type="number"
                                value={initialCash}
                                onChange={(e) => setInitialCash(e.target.value)}
                                required
                            />
                        </div>
                    </div>

                    <div className="form-group">
                        <label htmlFor="commission">{t('config_form.commission')}</label>
                        <div className="input-with-icon">
                            <PercentageOutlined className="input-icon" />
                            <input
                                id="commission"
                                type="number"
                                step="0.0001"
                                value={commission}
                                onChange={(e) => setCommission(e.target.value)}
                                required
                            />
                        </div>
                    </div>

                    <div className="form-group">
                        <label htmlFor="stake">{t('config_form.order_size')}</label>
                        <div className="input-with-icon">
                            <NumberOutlined className="input-icon" />
                            <input
                                id="stake"
                                type="number"
                                value={stake}
                                onChange={(e) => setStake(e.target.value)}
                                required
                            />
                        </div>
                    </div>
                </div>

                <div className="form-actions-enhanced">
                    <button type="submit" className="btn-primary glow-effect" disabled={loading}>
                        {loading ? <span className="spinner-sm"></span> : t('config_form.run_backtest')}
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

StrategyConfigForm.propTypes = {
    strategies: PropTypes.array.isRequired,
    selectedStrategy: PropTypes.string.isRequired,
    setSelectedStrategy: PropTypes.func.isRequired,
    fetchStrategies: PropTypes.func.isRequired,
    ticker: PropTypes.string.isRequired,
    setTicker: PropTypes.func.isRequired,
    startDate: PropTypes.string.isRequired,
    setStartDate: PropTypes.func.isRequired,
    endDate: PropTypes.string.isRequired,
    setEndDate: PropTypes.func.isRequired,
    initialCash: PropTypes.oneOfType([PropTypes.string, PropTypes.number]).isRequired,
    setInitialCash: PropTypes.func.isRequired,
    commission: PropTypes.oneOfType([PropTypes.string, PropTypes.number]).isRequired,
    setCommission: PropTypes.func.isRequired,
    stake: PropTypes.oneOfType([PropTypes.string, PropTypes.number]).isRequired,
    setStake: PropTypes.func.isRequired,
    loading: PropTypes.bool.isRequired,
    onSubmit: PropTypes.func.isRequired,
    error: PropTypes.string
};

export default StrategyConfigForm;
