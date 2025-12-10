import { API_URL } from './api';
import { formatCurrency, formatPercent, formatNumber } from '../utils/formatters';

export const performFullStrategyAnalysis = async ({
    result,
    strategyName,
    ticker,
    startDate,
    endDate,
    model = "gpt-5.1"
}) => {
    // 1. Fetch Strategy Code
    let strategyCode = '';
    try {
        if (strategyName) {
            const stratData = await fetch(`${API_URL}/strategy/${strategyName}`);
            strategyCode = stratData?.code || 'Code not available';
        }
    } catch (e) {
        console.warn("Could not fetch strategy code", e);
        strategyCode = 'Error fetching code';
    }

    // 2. Fetch Plot Image Blob
    let file = null;
    try {
        const imageUrl = `${API_URL}${result.plot_url}`;
        const res = await fetch(imageUrl);
        if (res.ok) {
            const blob = await res.blob();
            file = new File([blob], "chart.png", { type: "image/png" });
        } else {
            console.warn("Failed to download chart image for analysis");
        }
    } catch (e) {
        console.warn("Error fetching chart image", e);
    }

    // 3. Prepare Prompt Content
    const metrics = result.metrics || {};
    const trades = metrics.trades || {}; // Note: backend structure might vary, strictly follows StrategyPlot's usage
    // Actually, StrategyPlot used: trades.total?.total etc.
    // Let's copy formatting logic exactly.

    const totalTrades = trades.total?.total ?? (metrics.trade_details?.trades?.length ?? 0);
    const winRate = trades.total?.closed ? ((trades.won?.total ?? 0) / trades.total.closed) * 100 : 0;
    // Fallback if detailed trade analysis isn't in metrics but simple list is

    // Re-implement the metrics extraction from StrategyPlot
    const metricsText = `
Strategy Performance Metrics:
- Final Value: ${formatCurrency(metrics.final_value)}
- Return: ${formatPercent(metrics.returns)}
- Sharpe Ratio: ${formatNumber(metrics.sharpe)}
- Max Drawdown: ${formatPercent(metrics.drawdown)}
- SQN: ${formatNumber(metrics.sqn)}
- Total Trades: ${totalTrades}
- Win Rate: ${formatPercent(winRate)}
`;

    const tradeList = metrics.trade_details?.trades || [];
    const recentTrades = tradeList.slice(-50);

    const logsText = recentTrades.length > 0 ? `
Recent Trading Logs (Last ${recentTrades.length} trades):
| # | Open Date | Open Price | Close Date | Close Price | Size | Net PnL | Return % |
|---|-----------|------------|------------|-------------|------|---------|----------|
${recentTrades.map(t => `| ${t.trade_num} | ${t.open_date} | ${t.open_price.toFixed(2)} | ${t.close_date} | ${t.close_price.toFixed(2)} | ${t.size} | ${t.net_pnl.toFixed(2)} | ${t.return_pct.toFixed(2)}% |`).join('\n')}
` : 'No trades executed.';

    const contextText = `
Backtest Context:
- Target: ${ticker}
- Time Range: ${startDate} to ${endDate}
- Strategy: ${strategyName}

Strategy Source Code:
\`\`\`python
${strategyCode}
\`\`\`
`;

    const message = `Please analyze the trading strategy based on the following configurations, source code, performance metrics, the attached equity curve chart, and the recent trading logs.

${contextText}

${metricsText}

${logsText}

Provide a comprehensive assessment including:
1. Overall Performance: Is it profitable and consistent?
2. Risk Profile: analysis of drawdowns and volatility.
3. Strengths & Weaknesses: What is working well and what isn't?
4. Suggestions: Recommendations for improvement.
5. Code Analysis: Comments on the strategy logic.
6. Always return with Chinese.
7. 不需要对策略代码逻辑进行点评
`;

    // 4. Call API
    // Note: api.analyzeChart expects (message, model, file)
    return await api.analyzeChart(message, model, file);
};
