import PropTypes from 'prop-types';
import { useTranslation } from 'react-i18next';
import { formatCurrency, formatPercent } from '../../utils/formatters';

function TradeLog({ trades }) {
    const { t } = useTranslation();

    if (!trades || trades.length === 0) {
        return null;
    }

    return (
        <div className="card">
            <h2>{t('trade_log.title')}</h2>
            <div className="table-container">
                <table className="trade-table">
                    <thead>
                        <tr>
                            <th>#</th>
                            <th>{t('trade_log.open_date')}</th>
                            <th>{t('trade_log.open_price')}</th>
                            <th>{t('trade_log.close_date')}</th>
                            <th>{t('trade_log.close_price')}</th>
                            <th>{t('trade_log.size')}</th>
                            <th>{t('trade_log.net_pnl')}</th>
                            <th>{t('trade_log.return')}</th>
                        </tr>
                    </thead>
                    <tbody>
                        {trades.map((trade) => (
                            <tr key={trade.trade_num}>
                                <td>{trade.trade_num}</td>
                                <td>{trade.open_date}</td>
                                <td>{formatCurrency(trade.open_price)}</td>
                                <td>{trade.close_date}</td>
                                <td>{formatCurrency(trade.close_price)}</td>
                                <td>{trade.size}</td>
                                <td className={trade.net_pnl >= 0 ? 'positive' : 'negative'}>
                                    {formatCurrency(trade.net_pnl)}
                                </td>
                                <td className={trade.return_pct >= 0 ? 'positive' : 'negative'}>
                                    {formatPercent(trade.return_pct, 2, 1)}
                                </td>
                            </tr>
                        ))}
                    </tbody>
                </table>
            </div>
        </div>
    );
}

TradeLog.propTypes = {
    trades: PropTypes.array
};

export default TradeLog;
