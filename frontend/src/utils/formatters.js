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

// ============= Portfolio-specific formatters =============

/**
 * Format currency value for portfolio displays.
 * Uses zero decimal places by default for larger values.
 * @param {number} value - The currency value
 * @param {number} digits - Decimal places (default 0)
 * @returns {string} Formatted currency string or '-' if invalid
 */
export const formatPortfolioCurrency = (value, digits = 0) => {
    if (value === undefined || value === null) return '-';
    if (!isNumber(value)) return '-';
    return '$' + Math.abs(value).toLocaleString(undefined, {
        minimumFractionDigits: digits,
        maximumFractionDigits: digits
    });
};

/**
 * Format percentage as weight (e.g., 0.25 -> "25.0%").
 * @param {number} value - Weight value (0-1 range)
 * @param {number} digits - Decimal places (default 1)
 * @returns {string} Formatted percentage string or '-' if invalid
 */
export const formatWeight = (value, digits = 1) => {
    if (value === undefined || value === null) return '-';
    if (!isNumber(value)) return '-';
    return (value * 100).toFixed(digits) + '%';
};

/**
 * Get color indicator based on transaction cost severity.
 * @param {number} cost - Transaction cost amount
 * @returns {string} Ant Design color name (green, blue, orange, red)
 */
export const getCostColor = (cost) => {
    if (!cost || !isNumber(cost)) return 'blue';
    if (cost < 50) return 'green';
    if (cost < 200) return 'blue';
    if (cost < 500) return 'orange';
    return 'red';
};

/**
 * Get color based on numeric value (positive/negative).
 * @param {number} value - The value to colorize
 * @returns {string} CSS color value (green for positive, red for negative, gray for zero)
 */
export const getValueColor = (value) => {
    if (!isNumber(value)) return '#8c8c8c';
    if (value > 0) return '#52c41a';
    if (value < 0) return '#ff4d4f';
    return '#8c8c8c';
};

/**
 * Get color for return/change values.
 * @param {number} value - Return or change value
 * @returns {string} CSS color class or value
 */
export const getReturnColor = (value) => {
    if (!isNumber(value)) return 'inherit';
    if (value > 0) return '#52c41a';
    if (value < 0) return '#ff4d4f';
    return 'inherit';
};

/**
 * Format date string to localized date.
 * @param {string} dateStr - ISO date string
 * @param {Object} options - Intl.DateTimeFormat options
 * @returns {string} Formatted date string
 */
export const formatDate = (dateStr, options = { year: 'numeric', month: 'short', day: 'numeric' }) => {
    if (!dateStr) return '-';
    try {
        const date = new Date(dateStr);
        return date.toLocaleDateString(undefined, options);
    } catch {
        return dateStr;
    }
};

/**
 * Format shares count with +/- sign for changes.
 * @param {number} shares - Number of shares (positive for buy, negative for sell)
 * @returns {string} Formatted shares string with sign
 */
export const formatSharesChange = (shares) => {
    if (!isNumber(shares)) return '-';
    const sign = shares > 0 ? '+' : '';
    return `${sign}${shares.toLocaleString()}`;
};
