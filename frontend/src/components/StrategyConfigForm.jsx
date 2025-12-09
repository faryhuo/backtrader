import PropTypes from 'prop-types';

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
    return (
        <section className="card form-card">
            <h2>Strategy Configuration</h2>
            <form onSubmit={onSubmit} className="form-grid">
                <div className="form-group">
                    <label htmlFor="strategy-select">Strategy</label>
                    <div className="strategy-row">
                        <select
                            id="strategy-select"
                            value={selectedStrategy}
                            onChange={(e) => setSelectedStrategy(e.target.value)}
                        >
                            {strategies.map((s) => (
                                <option key={s} value={s}>{s}</option>
                            ))}
                        </select>
                        <button
                            type="button"
                            className="btn-ghost"
                            onClick={fetchStrategies}
                            title="Refresh strategies"
                        >
                            Refresh
                        </button>
                    </div>
                </div>

                <div className="form-group">
                    <label htmlFor="ticker">Asset Ticker</label>
                    <input
                        id="ticker"
                        type="text"
                        value={ticker}
                        onChange={(e) => setTicker(e.target.value)}
                        required
                    />
                </div>

                <div className="form-group">
                    <label htmlFor="start-date">Start Date</label>
                    <input
                        id="start-date"
                        type="date"
                        value={startDate}
                        onChange={(e) => setStartDate(e.target.value)}
                        required
                    />
                </div>

                <div className="form-group">
                    <label htmlFor="end-date">End Date</label>
                    <input
                        id="end-date"
                        type="date"
                        value={endDate}
                        onChange={(e) => setEndDate(e.target.value)}
                        required
                    />
                </div>

                <div className="form-group">
                    <label htmlFor="initial-cash">Initial Capital ($)</label>
                    <input
                        id="initial-cash"
                        type="number"
                        value={initialCash}
                        onChange={(e) => setInitialCash(e.target.value)}
                        required
                    />
                </div>

                <div className="form-group">
                    <label htmlFor="commission">Commission (rate)</label>
                    <input
                        id="commission"
                        type="number"
                        step="0.0001"
                        value={commission}
                        onChange={(e) => setCommission(e.target.value)}
                        required
                    />
                </div>

                <div className="form-group">
                    <label htmlFor="stake">Order Size (shares/contracts)</label>
                    <input
                        id="stake"
                        type="number"
                        value={stake}
                        onChange={(e) => setStake(e.target.value)}
                        required
                    />
                </div>

                <div className="form-actions">
                    <button type="submit" className="btn-primary" disabled={loading}>
                        {loading ? <span className="spinner"></span> : 'Run Backtest'}
                    </button>
                </div>
            </form>

            {error && <div className="error-message">{error}</div>}
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
