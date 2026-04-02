import { useState, useCallback, useEffect, useMemo } from 'react';
import { message } from 'antd';
import { performFullStrategyAnalysis } from '../services/aiAnalysis';

/**
 * Hook for managing AI analysis state and execution.
 *
 * Provides a unified interface for running AI analysis on backtest results,
 * with support for:
 * - Provider-priority backend execution
 * - Pre-loaded analyses (from database)
 * - Optional persistence callback for saving analyses
 *
 * @param {Object} options - Configuration options
 * @param {function} options.getAvailableModels - Function to get available AI models
 * @param {Object} options.settings - Settings from SettingsContext
 * @param {Object} options.initialAnalyses - Pre-loaded analyses from DB (default: {})
 * @param {function} options.onAnalysisSaved - Optional callback for persistence (modelName, analysis) => Promise
 * @returns {Object} AI analysis state and handlers
 */
export function useAIAnalysis({
    settings,
    initialAnalyses = {},
    onAnalysisSaved = null,
}) {
    const [analyses, setAnalyses] = useState({});
    const [activeTab, setActiveTab] = useState(null);
    const [aiLoading, setAiLoading] = useState(false);

    // Merge local analyses with initial analyses (initial has lower priority)
    const allAnalyses = useMemo(
        () => ({ ...initialAnalyses, ...analyses }),
        [initialAnalyses, analyses]
    );

    // Set initial active tab when analyses are available
    useEffect(() => {
        if (!activeTab && Object.keys(allAnalyses).length > 0) {
            setActiveTab(Object.keys(allAnalyses)[0]);
        }
    }, [activeTab, allAnalyses]);

    // Run AI analysis on backtest result
    const runAnalysis = useCallback(async ({
        result,
        strategyName,
        ticker,
        startDate,
        endDate,
        strategyCode,
        backtestId,  // Optional: for persistence callback
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
                model: null,
                initialStrategyCode: strategyCode,
                settings,
            });

            const analysisKey = `${data.provider}:${data.model}`;

            // Update local state
            setAnalyses(prev => ({
                ...prev,
                [analysisKey]: data.analysis
            }));
            setActiveTab(analysisKey);

            // Call persistence callback if provided
            if (onAnalysisSaved && backtestId) {
                try {
                    await onAnalysisSaved(backtestId, analysisKey, data.analysis);
                    message.success(t?.('history.ai_analysis_saved', 'AI analysis saved successfully') ||
                        'AI analysis saved successfully');
                } catch (err) {
                    console.error('Failed to save AI analysis:', err);
                    message.error(t?.('history.ai_analysis_save_error', 'Failed to save AI analysis') ||
                        'Failed to save AI analysis');
                }
            }

            return data.analysis;
        } catch (err) {
            console.error(err);
            message.error(t?.('history.ai_analysis_failed', { error: err.message }) ||
                `AI analysis failed: ${err.message}`);
            return null;
        } finally {
            setAiLoading(false);
        }
    }, [settings, onAnalysisSaved]);

    // Clear all analyses
    const clearAnalyses = useCallback(() => {
        setAnalyses({});
        setActiveTab(null);
    }, []);

    // Check if analysis exists for any model
    const hasAnalysis = Object.keys(allAnalyses).length > 0;

    return {
        analyses: allAnalyses,  // Return merged analyses
        activeTab,
        setActiveTab,
        aiLoading,
        runAnalysis,
        clearAnalyses,
        hasAnalysis,
    };
}

export default useAIAnalysis;
