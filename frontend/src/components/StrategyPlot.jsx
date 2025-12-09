import { useState } from 'react';
import ReactMarkdown from 'react-markdown';
import PropTypes from 'prop-types';
import { performFullStrategyAnalysis } from '../services/aiAnalysis';
import AIInsight from './AIInsight';

function StrategyPlot({ result, ticker, startDate, endDate, strategyName }) {
    const [isPlotMaximized, setIsPlotMaximized] = useState(false);
    const [plotScale, setPlotScale] = useState(1);
    const [aiLoading, setAiLoading] = useState(false);
    const [analyses, setAnalyses] = useState({});
    const [activeTab, setActiveTab] = useState(null);
    const [selectedModel, setSelectedModel] = useState('gpt-5.1');
    const AVAILABLE_MODELS = ['gpt-5.1', 'deepseek-v3.1', 'gemini-3-pro'];

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

        } catch (err) {
            console.error(err);
            setAnalyses(prev => ({
                ...prev,
                [selectedModel]: "Failed to perform AI analysis: " + err.message
            }));
            setActiveTab(selectedModel);
        } finally {
            setAiLoading(false);
        }
    }

    const hasAnalyses = Object.keys(analyses).length > 0;

    return (
        <>
            <div className="card plot-card">
                <div className="plot-header">
                    <h2>Strategy Visualization</h2>
                    <div className="plot-actions">
                        <button
                            type="button"
                            className="btn-ghost"
                            onClick={() => setIsPlotMaximized(true)}
                        >
                            Maximize
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
                        {AVAILABLE_MODELS.map(m => (
                            <option key={m} value={m}>{m}</option>
                        ))}
                    </select>
                    <button className="btn-secondary" onClick={handleAIAnalysis} disabled={aiLoading}>
                        {aiLoading ? 'Interpreting...' : 'AI Interpretation'}
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
                                    Reset
                                </button>
                            </div>
                            <button
                                type="button"
                                className="btn-ghost"
                                onClick={() => setIsPlotMaximized(false)}
                            >
                                Close
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
