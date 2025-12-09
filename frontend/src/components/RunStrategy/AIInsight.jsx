import React from 'react';
import ReactMarkdown from 'react-markdown';
import PropTypes from 'prop-types';
import { useTranslation } from 'react-i18next';

function AIInsight({ analyses, activeTab, onTabChange }) {
    const { t } = useTranslation();

    if (!analyses || Object.keys(analyses).length === 0) {
        return null;
    }

    return (
        <div className="ai-insight-section">
            <div className="tabs">
                {Object.keys(analyses).map(modelKey => (
                    <button
                        key={modelKey}
                        className={`tab ${activeTab === modelKey ? 'active' : ''}`}
                        onClick={() => onTabChange(modelKey)}
                    >
                        {modelKey}
                    </button>
                ))}
            </div>
            <div className="ai-markdown-content">
                {(() => {
                    const content = analyses[activeTab];
                    if (!content) return null;

                    const thinkMatch = content.match(/<think>([\s\S]*?)<\/think>/);
                    if (thinkMatch) {
                        const thoughtProcess = thinkMatch[1];
                        const mainContent = content.replace(/<think>[\s\S]*?<\/think>/, '').trim();

                        return (
                            <>
                                <details className="thought-process-details">
                                    <summary>{t('ai_insight.thinking_process')}</summary>
                                    <div className="thought-content">
                                        <ReactMarkdown>{thoughtProcess}</ReactMarkdown>
                                    </div>
                                </details>
                                <ReactMarkdown>{mainContent}</ReactMarkdown>
                            </>
                        );
                    }

                    return <ReactMarkdown>{content}</ReactMarkdown>;
                })()}
            </div>
        </div>
    );
}

AIInsight.propTypes = {
    analyses: PropTypes.object.isRequired,
    activeTab: PropTypes.string,
    onTabChange: PropTypes.func.isRequired
};

export default AIInsight;
