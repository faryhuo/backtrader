import React from 'react'

const StrategySelector = ({ 
    strategies, 
    selectedStrategy, 
    onSelectStrategy, 
    onReload, 
    onRefreshList, 
    onAIAnalysis,
    onAIRewrite,
    loading, 
    t 
}) => {
    return (
        <div className="strategy-toolbar">
            <div className="strategy-row">
                <label htmlFor="editor-strategy-select">{t('maintain.active_strategy')}</label>
                <select
                    id="editor-strategy-select"
                    value={selectedStrategy}
                    onChange={(e) => onSelectStrategy(e.target.value)}
                    disabled={loading}
                >
                    {strategies.map((s) => (
                        <option key={s} value={s}>{s}</option>
                    ))}
                </select>
                <button
                    type="button"
                    className="btn-ghost"
                    onClick={onReload}
                    disabled={loading}
                >
                    {t('maintain.reload')}
                </button>
                <button
                    type="button"
                    className="btn-ghost"
                    onClick={onRefreshList}
                    disabled={loading}
                >
                    {t('maintain.refresh_list')}
                </button>
                <div style={{ width: '1px', height: '20px', background: 'var(--border-color)', margin: '0 0.5rem' }}></div>
                <button
                    type="button"
                    className="btn-secondary"
                    onClick={onAIAnalysis}
                    disabled={loading}
                    title="Analyze code structure and logic"
                >
                    {t('maintain.ai_analysis')}
                </button>
                <button
                    type="button"
                    className="btn-secondary"
                    onClick={onAIRewrite}
                    disabled={loading}
                    title="Rewrite code for optimization"
                >
                    {t('maintain.ai_rewrite')}
                </button>
            </div>
        </div>
    )
}

export default StrategySelector
