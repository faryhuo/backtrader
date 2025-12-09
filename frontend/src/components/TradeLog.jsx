import PropTypes from 'prop-types';
import { formatCurrency, formatPercent } from '../utils/formatters';

function TradeLog({ trades }) {
    if (!trades || trades.length === 0) {
        return null;
    }

    return (
        <div className="card">
            <h2>Trade Log</h2>
            <div className="table-container">
                <table className="trade-table">
                    <thead>
                        <tr>
                            <th>#</th>
                            <th>Open Date</th>
                            <th>Open Price</th>
                            <th>Close Date</th>
                            <th>Close Price</th>
                            <th>Size</th>
                            <th>Net PnL</th>
                            <th>Return</th>
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
