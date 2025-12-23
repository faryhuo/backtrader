import { useState, useCallback } from 'react';
import { message } from 'antd';
import { performFullStrategyAnalysis } from '../services/aiAnalysis';

/**
 * Hook for managing AI analysis state and execution.
 *
 * @param {Object} options - Configuration options
 * @param {function} options.getAvailableModels - Function to get available AI models
 * @param {Object} options.settings - Settings from SettingsContext
 * @returns {Object} AI analysis state and handlers
 */
export function useAIAnalysis({ getAvailableModels, settings }) {
    const availableModels = getAvailableModels?.() || ['gpt-4o'];
    const [selectedModel, setSelectedModel] = useState(availableModels[0] || 'gpt-4o');
    const [analyses, setAnalyses] = useState({});
    const [activeTab, setActiveTab] = useState(null);
    const [aiLoading, setAiLoading] = useState(false);

    // Run AI analysis on backtest result
    const runAnalysis = useCallback(async ({
        result,
        strategyName,
        ticker,
        startDate,
        endDate,
        strategyCode,
        t, // translation function
    }) => {
        if (!result || (!result.plot_url && !result.metrics)) {
            return null;
        }

        setAiLoading(true);

        try {
            const data = await performFullStrategyAnalysis({
                result: {
                    metrics: result.metrics || result,
                    plot_url: result.plot_url,
                },
                strategyName,
                ticker,
                startDate,
                endDate,
                model: selectedModel,
                initialStrategyCode: strategyCode,
                settings,
            });

            setAnalyses(prev => ({
                ...prev,
                [selectedModel]: data.analysis
            }));
            setActiveTab(selectedModel);

            return data.analysis;
        } catch (err) {
            console.error(err);
            message.error(t?.('history.ai_analysis_failed', { error: err.message }) ||
                `AI analysis failed: ${err.message}`);
            return null;
        } finally {
            setAiLoading(false);
        }
    }, [selectedModel, settings]);

    // Clear all analyses
    const clearAnalyses = useCallback(() => {
        setAnalyses({});
        setActiveTab(null);
    }, []);

    // Check if analysis exists for current model
    const hasAnalysis = Object.keys(analyses).length > 0;

    return {
        selectedModel,
        setSelectedModel,
        analyses,
        activeTab,
        setActiveTab,
        aiLoading,
        runAnalysis,
        clearAnalyses,
        hasAnalysis,
        availableModels,
    };
}

export default useAIAnalysis;
