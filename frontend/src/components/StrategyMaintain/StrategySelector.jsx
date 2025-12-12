import React from 'react'
import { ReloadOutlined, SyncOutlined, RobotOutlined, ThunderboltOutlined } from '@ant-design/icons'

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
        <>
            <div className="strategy-selector-group">
                <label htmlFor="editor-strategy-select">{t('maintain.active_strategy')}:</label>
                <select
                    id="editor-strategy-select"
                    className="strategy-select"
                    value={selectedStrategy}
                    onChange={(e) => onSelectStrategy(e.target.value)}
                    disabled={loading}
                >
                    {strategies.map((s) => (
                        <option key={s} value={s}>{s}</option>
                    ))}
                </select>
            </div>

            <div className="toolbar-actions">
                <button
                    type="button"
                    className="btn-ghost"
                    onClick={onReload}
                    disabled={loading}
                    title={t('maintain.reload')}
                >
                    <ReloadOutlined />
                </button>
                <button
                    type="button"
                    className="btn-ghost"
                    onClick={onRefreshList}
                    disabled={loading}
                    title={t('maintain.refresh_list')}
                >
                    <SyncOutlined />
                </button>
            </div>

            <div className="toolbar-divider"></div>

            <div className="toolbar-actions">
                <button
                    type="button"
                    className="btn-secondary"
                    onClick={onAIAnalysis}
                    disabled={loading}
                    title="Analyze code structure and logic"
                >
                    <RobotOutlined /> {t('maintain.ai_analysis')}
                </button>
                <button
                    type="button"
                    className="btn-secondary"
                    onClick={onAIRewrite}
                    disabled={loading}
                    title="Rewrite code for optimization"
                >
                    <ThunderboltOutlined /> {t('maintain.ai_rewrite')}
                </button>
            </div>
        </>
    )
}

export default StrategySelector
