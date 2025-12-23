import { API_URL, getAccessToken, parseResponse } from './api';
import { formatCurrency, formatPercent, formatNumber } from '../utils/formatters';
import { DEFAULT_SETTINGS } from '../constants/settingsConstants';

/**
 * Get effective settings by merging provided settings with defaults.
 * Eliminates the need to read localStorage directly - callers should
 * inject settings from SettingsContext.
 * @param {Object} providedSettings - Settings injected from SettingsContext (optional)
 * @returns {Object} Merged settings with defaults as fallback
 */
const getEffectiveSettings = (providedSettings) => {
    if (providedSettings && Object.keys(providedSettings).length > 0) {
        return { ...DEFAULT_SETTINGS, ...providedSettings };
    }
    return DEFAULT_SETTINGS;
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

/**
 * Perform full strategy analysis with AI.
 * @param {Object} params - Analysis parameters
 * @param {Object} params.settings - Settings from SettingsContext (optional, uses defaults if not provided)
 */
export const performFullStrategyAnalysis = async ({
    result,
    strategyName,
    ticker,
    startDate,
    endDate,
    model = "gpt-5.1",
    initialStrategyCode,
    settings: providedSettings
}) => {
    const settings = getEffectiveSettings(providedSettings);

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
    const trades = metrics.trades || {};

    const totalTrades = trades.total?.total ?? (metrics.trade_details?.trades?.length ?? 0);
    const winRate = trades.total?.closed ? ((trades.won?.total ?? 0) / trades.total.closed) * 100 : 0;

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

    const promptTemplate = settings.fullStrategyAnalysisPrompt || DEFAULT_SETTINGS.fullStrategyAnalysisPrompt;

    const message = promptTemplate
        .replace('{contextText}', contextText)
        .replace('{metricsText}', metricsText)
        .replace('{logsText}', logsText);

    // 4. Call API
    return await analyzeChart(message, model, file);
};

/**
 * Analyze strategy code with AI.
 * @param {string} code - Strategy code to analyze
 * @param {string} model - AI model to use (optional)
 * @param {Object} providedSettings - Settings from SettingsContext (optional)
 */
export const analyzeCode = async (code, model = null, providedSettings = null) => {
    const settings = getEffectiveSettings(providedSettings);
    const effectiveModel = model || (settings.selectedModels && settings.selectedModels.length > 0 ? settings.selectedModels[0] : DEFAULT_SETTINGS.selectedModels[0]);
    const prompt = settings.codeAnalysisPrompt.replace('{code}', code);

    const data = await analyzeChart(prompt, effectiveModel, null);
    return data.analysis;
};

/**
 * Rewrite strategy code with AI.
 * @param {string} code - Strategy code to rewrite
 * @param {string} model - AI model to use (optional)
 * @param {Object} providedSettings - Settings from SettingsContext (optional)
 */
export const rewriteCode = async (code, model = null, providedSettings = null) => {
    const settings = getEffectiveSettings(providedSettings);
    const effectiveModel = model || (settings.selectedModels && settings.selectedModels.length > 0 ? settings.selectedModels[0] : DEFAULT_SETTINGS.selectedModels[0]);
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
