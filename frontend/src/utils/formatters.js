export const isNumber = (value) => typeof value === 'number' && !Number.isNaN(value)

export const formatNumber = (value, digits = 2) =>
    isNumber(value) ? value.toFixed(digits) : 'N/A'

export const formatPercent = (value, digits = 2, multiplier = 1) =>
    isNumber(value) ? `${(value * multiplier).toFixed(digits)}%` : 'N/A'

export const formatCurrency = (value, digits = 2) =>
    isNumber(value)
        ? `$${value.toLocaleString(undefined, { minimumFractionDigits: digits, maximumFractionDigits: digits })}`
        : 'N/A'

/**
 * Build a text summary of strategy performance metrics.
 * Shared by UI components and AI analysis to ensure consistent formatting.
 * @param {Object} metrics - Metrics object from backtest result
 * @returns {string} Formatted text summary
 */
export const buildMetricsSummary = (metrics) => {
    if (!metrics) return 'No metrics available.';

    const trades = metrics.trades || {};
    const totalTrades = trades.total?.total ?? (metrics.trade_details?.trades?.length ?? 0);
    const closedTrades = trades.total?.closed ?? 0;
    const wins = trades.won?.total ?? 0;
    const winRate = closedTrades ? (wins / closedTrades) * 100 : 0;

    return `
Strategy Performance Metrics:
- Final Value: ${formatCurrency(metrics.final_value)}
- Return: ${formatPercent(metrics.returns)}
- Sharpe Ratio: ${formatNumber(metrics.sharpe)}
- Max Drawdown: ${formatPercent(metrics.drawdown)}
- SQN: ${formatNumber(metrics.sqn)}
- Total Trades: ${totalTrades}
- Win Rate: ${formatPercent(winRate)}
`.trim();
};

/**
 * Build a markdown table of recent trades.
 * Shared by UI components and AI analysis to ensure consistent formatting.
 * @param {Array} trades - Array of trade objects
 * @param {number} limit - Maximum number of trades to include (default: 50)
 * @returns {string} Formatted markdown table or message if no trades
 */
export const buildRecentTradesTable = (trades, limit = 50) => {
    if (!trades || trades.length === 0) {
        return 'No trades executed.';
    }

    const recentTrades = trades.slice(-limit);

    const header = `Recent Trading Logs (Last ${recentTrades.length} trades):
| # | Open Date | Open Price | Close Date | Close Price | Size | Net PnL | Return % |
|---|-----------|------------|------------|-------------|------|---------|----------|`;

    const rows = recentTrades.map(t =>
        `| ${t.trade_num} | ${t.open_date} | ${isNumber(t.open_price) ? t.open_price.toFixed(2) : 'N/A'} | ${t.close_date} | ${isNumber(t.close_price) ? t.close_price.toFixed(2) : 'N/A'} | ${t.size} | ${isNumber(t.net_pnl) ? t.net_pnl.toFixed(2) : 'N/A'} | ${isNumber(t.return_pct) ? t.return_pct.toFixed(2) : 'N/A'}% |`
    ).join('\n');

    return `${header}\n${rows}`;
}
