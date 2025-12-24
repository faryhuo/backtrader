import { API_URL, buildRequest, parseResponse, strategyApi } from './api';
import { buildMetricsSummary, buildRecentTradesTable } from '../utils/formatters';
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

    const res = await buildRequest('/ai_analyze', {
        method: 'POST',
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
    } else if (strategyName) {
        try {
            const stratData = await strategyApi.getStrategy(strategyName);
            strategyCode = stratData?.code || 'Code not available';
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

    // 3. Prepare Prompt Content - using shared formatters to ensure consistency with UI
    const metrics = result.metrics || {};
    const metricsText = buildMetricsSummary(metrics);
    const tradeList = metrics.trade_details?.trades || [];
    const logsText = buildRecentTradesTable(tradeList, 50);

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
