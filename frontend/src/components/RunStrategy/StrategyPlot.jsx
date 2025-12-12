import { useState } from 'react';
import ReactMarkdown from 'react-markdown';
import PropTypes from 'prop-types';
import { useTranslation } from 'react-i18next';
import { message } from 'antd';
import { performFullStrategyAnalysis, getAvailableModels } from '../../services/aiAnalysis';
import { api } from '../../services/api';
import AIInsight from './AIInsight';

function StrategyPlot({ result, ticker, startDate, endDate, strategyName }) {
    const { t } = useTranslation();
    const [isPlotMaximized, setIsPlotMaximized] = useState(false);
    const [plotScale, setPlotScale] = useState(1);
    const [aiLoading, setAiLoading] = useState(false);
    const [analyses, setAnalyses] = useState({});
    const [activeTab, setActiveTab] = useState(null);
    
    // Initialize available models from settings
    const availableModels = getAvailableModels();
    const [selectedModel, setSelectedModel] = useState(availableModels[0] || 'gpt-5.1');

    if (!result || !result.plot_url) {
        return null;
    }

    const handleAIAnalysis = async () => {
        if (!result || !result.plot_url) {
            return;
        }
        setAiLoading(true);
        // Do not clear previous analyses, just add/overwrite the selected model key later

        try {
            const data = await performFullStrategyAnalysis({
                result,
                strategyName,
                ticker,
                startDate,
                endDate,
                model: selectedModel
            });

            setAnalyses(prev => {
                const newState = { ...prev, [selectedModel]: data.analysis };
                return newState;
            });
            setActiveTab(selectedModel);

            // Save AI analysis to backtest history if backtest_id exists
            if (result.backtest_id) {
                try {
                    await api.updateBacktestAiAnalysis(result.backtest_id,model, data.analysis);
                } catch (err) {
                    console.error("Failed to save AI analysis to history:", err);
                    // Don't show error to user - analysis is still displayed
                }
            }

        } catch (err) {
            console.error(err);
            message.error("Failed to perform AI analysis: " + err.message);
        } finally {
            setAiLoading(false);
        }
    }

    const hasAnalyses = Object.keys(analyses).length > 0;

    return (
        <>
            <div className="card plot-card">
                <div className="plot-header">
                    <h2>{t('strategy_plot.title')}</h2>
                    <div className="plot-actions">
                        <button
                            type="button"
                            className="btn-ghost"
                            onClick={() => setIsPlotMaximized(true)}
                        >
                            {t('strategy_plot.maximize')}
                        </button>
                    </div>
                </div>
                <div className="plot-container">
                    <img src={result.plot_url} alt="Strategy Plot" />
                </div>

                <div className="analysis-controls" style={{ marginTop: '1rem', display: 'flex', justifyContent: 'center', gap: '1rem', alignItems: 'center' }}>
                    <select
                        className="input-field"
                        value={selectedModel}
                        onChange={(e) => setSelectedModel(e.target.value)}
                        style={{ maxWidth: '150px' }}
                    >
                        {availableModels.map(m => (
                            <option key={m} value={m}>{m}</option>
                        ))}
                    </select>
                    <button className="btn-secondary" onClick={handleAIAnalysis} disabled={aiLoading}>
                        {aiLoading ? t('strategy_plot.interpreting') : t('strategy_plot.ai_interpretation')}
                    </button>
                </div>

                <AIInsight
                    analyses={analyses}
                    activeTab={activeTab}
                    onTabChange={setActiveTab}
                />
            </div>

            {isPlotMaximized && (
                <div className="plot-overlay" onClick={() => setIsPlotMaximized(false)}>
                    <div className="plot-overlay-content" onClick={(e) => e.stopPropagation()}>
                        <div className="plot-overlay-actions">
                            <div className="plot-overlay-controls">
                                <button
                                    type="button"
                                    className="btn-ghost"
                                    onClick={() => setPlotScale((s) => Math.max(0.5, +(s - 0.1).toFixed(2)))}
                                >
                                    -
                                </button>
                                <input
                                    type="range"
                                    min="0.5"
                                    max="2.5"
                                    step="0.1"
                                    value={plotScale}
                                    onChange={(e) => setPlotScale(parseFloat(e.target.value))}
                                />
                                <button
                                    type="button"
                                    className="btn-ghost"
                                    onClick={() => setPlotScale((s) => Math.min(2.5, +(s + 0.1).toFixed(2)))}
                                >
                                    +
                                </button>
                                <button
                                    type="button"
                                    className="btn-ghost"
                                    onClick={() => setPlotScale(1)}
                                >
                                    {t('strategy_plot.reset')}
                                </button>
                            </div>
                            <button
                                type="button"
                                className="btn-ghost"
                                onClick={() => setIsPlotMaximized(false)}
                            >
                                {t('strategy_plot.close')}
                            </button>
                        </div>
                        <div className="plot-overlay-viewport">
                            <img
                                src={result.plot_url}
                                alt="Strategy Plot Enlarged"
                                style={{ transform: `scale(${plotScale})` }}
                            />
                        </div>
                    </div>
                </div>
            )}
        </>
    );
}

StrategyPlot.propTypes = {
    result: PropTypes.shape({
        plot_url: PropTypes.string,
        metrics: PropTypes.object
    }),
    ticker: PropTypes.string,
    startDate: PropTypes.string,
    endDate: PropTypes.string,
    strategyName: PropTypes.string
};

export default StrategyPlot;
