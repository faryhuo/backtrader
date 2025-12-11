import React, { useState } from 'react';
import ReactMarkdown from 'react-markdown';
import PropTypes from 'prop-types';
import { useTranslation } from 'react-i18next';
import { BulbOutlined, RobotOutlined, CaretRightOutlined, CaretDownOutlined } from '@ant-design/icons';
import './RunStrategy.css'; // Ensure we use the shared styles

function AIInsight({ analyses, activeTab, onTabChange }) {
    const { t } = useTranslation();
    const [isThinkingOpen, setIsThinkingOpen] = useState(false);

    if (!analyses || Object.keys(analyses).length === 0) {
        return null;
    }

    const currentContent = analyses[activeTab];

    const renderContent = () => {
        if (!currentContent) return null;

        const thinkMatch = currentContent.match(/<think>([\s\S]*?)<\/think>/);
        
        let thoughtProcess = null;
        let mainContent = currentContent;

        if (thinkMatch) {
            thoughtProcess = thinkMatch[1].trim();
            mainContent = currentContent.replace(/<think>[\s\S]*?<\/think>/, '').trim();
        }

        return (
            <div className="ai-content-body animate-fade-in">
                {thoughtProcess && (
                    <div className="thought-process-container">
                        <button 
                            className="thought-toggle-btn"
                            onClick={() => setIsThinkingOpen(!isThinkingOpen)}
                        >
                            {isThinkingOpen ? <CaretDownOutlined /> : <CaretRightOutlined />}
                            <span>{t('ai_insight.thinking_process', 'Thinking Process')}</span>
                        </button>
                        
                        {isThinkingOpen && (
                            <div className="thought-content custom-scrollbar">
                                <ReactMarkdown>{thoughtProcess}</ReactMarkdown>
                            </div>
                        )}
                    </div>
                )}
                
                <div className="main-analysis-content markdown-body">
                    <ReactMarkdown>{mainContent}</ReactMarkdown>
                </div>
            </div>
        );
    };

    return (
        <div className="ai-insight-card">
            <div className="ai-insight-header">
                <div className="ai-title-group">
                    <div className="ai-icon-wrapper">
                        <RobotOutlined />
                    </div>
                    <h3>{t('ai_insight.title', 'AI Strategy Insight')}</h3>
                </div>
                
                <div className="model-tabs">
                    {Object.keys(analyses).map(modelKey => (
                        <button
                            key={modelKey}
                            className={`model-tab ${activeTab === modelKey ? 'active' : ''}`}
                            onClick={() => onTabChange(modelKey)}
                        >
                            {modelKey}
                        </button>
                    ))}
                </div>
            </div>

            <div className="ai-insight-body">
                {renderContent()}
            </div>
            
            <div className="ai-insight-footer">
                <BulbOutlined />
                <span>{t('ai_insight.disclaimer', 'AI-generated insights may vary. Verify with quantitative data.')}</span>
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