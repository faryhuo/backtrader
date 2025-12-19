import { API_URL, getAccessToken, parseResponse } from './api';
import { formatCurrency, formatPercent, formatNumber } from '../utils/formatters';

export const getAISettings = () => {
    const DEFAULT_SETTINGS = {
        selectedModels: ['gpt-5.1'],
        codeAnalysisPrompt: 'Please analyze the following Backtrader strategy code. Explain its logic, potential pitfalls, and suggest improvements:\n\n{code}',
        codeRewritePrompt: 'Please rewrite and optimize the following Backtrader strategy code to follow best practices and fix potential issues. Return ONLY the python code, no markdown formatting or explanation:\n\n{code}',
        fullStrategyAnalysisPrompt: 'Please analyze the trading strategy based on the following configurations, source code, performance metrics, the attached equity curve chart, and the recent trading logs.\n\n{contextText}\n\n{metricsText}\n\n{logsText}\n\nProvide a comprehensive assessment including:\n1. Overall Performance: Is it profitable and consistent?\n2. Risk Profile: analysis of drawdowns and volatility.\n3. Strengths & Weaknesses: What is working well and what isn\'t?\n4. Suggestions: Recommendations for improvement.\n5. Code Analysis: Comments on the strategy logic.\n6. Always return with Chinese.\n7. 不需要对策略代码逻辑进行点评'
    };

    try {
        const stored = localStorage.getItem('userSettings');
        if (stored) {
            const parsed = JSON.parse(stored);
            // Migration handling
            if (parsed.aiModel && !parsed.selectedModels) {
                parsed.selectedModels = [parsed.aiModel];
                delete parsed.aiModel;
            }
            return { ...DEFAULT_SETTINGS, ...parsed };
        }
    } catch (e) {
        console.error('Failed to read settings from localStorage', e);
    }
    return DEFAULT_SETTINGS;
};

export const getAvailableModels = () => {
    const settings = getAISettings();
    return settings.selectedModels && settings.selectedModels.length > 0
        ? settings.selectedModels
        : ['gpt-5.1'];
};

export const analyzeChart = async (message, model, file) => {
    const formData = new FormData()
    formData.append('message', message)
    formData.append('model', model)
    if (file) {
        formData.append('file', file)
    }

    // Build headers with auth token
    const headers = new Headers()
    const token = await getAccessToken()
    if (token) {
        headers.set('Authorization', `Bearer ${token}`)
    }

    const res = await fetch(`${API_URL}/ai_analyze`, {
        method: 'POST',
        headers,
        body: formData
    })
    return await parseResponse(res)
}

export const performFullStrategyAnalysis = async ({
    result,
    strategyName,
    ticker,
    startDate,
    endDate,
    model = "gpt-5.1",
    initialStrategyCode
}) => {
    // 1. Fetch Strategy Code
    let strategyCode = '';
    if (initialStrategyCode) {
        strategyCode = initialStrategyCode;
    } else {
        try {
            if (strategyName) {
                const token = await getAccessToken();
                const headers = token ? { 'Authorization': `Bearer ${token}` } : {};
                const res = await fetch(`${API_URL}/strategy?name=${strategyName}`, { headers });
                if (res.ok) {
                    const stratData = await res.json();
                    strategyCode = stratData?.code || 'Code not available';
                } else {
                    console.warn(`Failed to fetch strategy code: ${res.status}`);
                    strategyCode = 'Code not available';
                }
            }
        } catch (e) {
            console.warn("Could not fetch strategy code", e);
            strategyCode = 'Error fetching code';
        }
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

    const settings = getAISettings();
    const promptTemplate = settings.fullStrategyAnalysisPrompt || `Please analyze the trading strategy based on the following configurations, source code, performance metrics, the attached equity curve chart, and the recent trading logs.

{contextText}

{metricsText}

{logsText}

Provide a comprehensive assessment including:
1. Overall Performance: Is it profitable and consistent?
2. Risk Profile: analysis of drawdowns and volatility.
3. Strengths & Weaknesses: What is working well and what isn't?
4. Suggestions: Recommendations for improvement.
5. Code Analysis: Comments on the strategy logic.
6. Always return with Chinese.
7. 不需要对策略代码逻辑进行点评`;

    const message = promptTemplate
        .replace('{contextText}', contextText)
        .replace('{metricsText}', metricsText)
        .replace('{logsText}', logsText);

    // 4. Call API
    // Note: api.analyzeChart expects (message, model, file)
    return await analyzeChart(message, model, file);
};

export const analyzeCode = async (code, model = null) => {
    const settings = getAISettings();
    const effectiveModel = model || (settings.selectedModels && settings.selectedModels.length > 0 ? settings.selectedModels[0] : 'gpt-5.1');
    const prompt = settings.codeAnalysisPrompt.replace('{code}', code);

    const data = await analyzeChart(prompt, effectiveModel, null);
    return data.analysis;
};

export const rewriteCode = async (code, model = null) => {
    const settings = getAISettings();
    const effectiveModel = model || (settings.selectedModels && settings.selectedModels.length > 0 ? settings.selectedModels[0] : 'gpt-5.1');
    const prompt = settings.codeRewritePrompt.replace('{code}', code);

    const data = await analyzeChart(prompt, effectiveModel, null);
    let cleanCode = data.analysis;
    if (cleanCode.startsWith('```python')) {
        cleanCode = cleanCode.replace(/^```python\n/, '').replace(/\n```$/, '');
    } else if (cleanCode.startsWith('```')) {
        cleanCode = cleanCode.replace(/^```\n/, '').replace(/\n```$/, '');
    }
    return cleanCode;
};

