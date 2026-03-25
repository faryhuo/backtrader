import { Button } from 'antd';
import { RobotOutlined } from '@ant-design/icons';
import AIInsight from './AIInsight';

/**
 * AI Insight tab content component
 * Provides model selection, analysis button, and displays AI analysis results
 */
function AIInsightTab({
    t, analyses, activeTab, setActiveTab, aiLoading, handleAIAnalysis, plotUrl, result
}) {
    return (
        <div style={{ padding: '20px' }}>
            <div style={{
                display: 'flex',
                justifyContent: 'space-between',
                alignItems: 'center',
                padding: '1.25rem 2rem',
                background: 'rgba(255, 255, 255, 0.03)',
                borderRadius: '12px',
                marginBottom: '1.5rem',
                border: '1px solid rgba(255, 255, 255, 0.05)'
            }}>
                <div style={{ display: 'flex', alignItems: 'center', gap: '1rem' }}>
                    <RobotOutlined style={{ fontSize: '1.5rem', color: '#22d3ee' }} />
                    <span style={{ fontSize: '1.1rem', fontWeight: 600, color: '#e2e8f0' }}>
                        {t('strategy_plot.ai_interpretation', 'AI Analysis')}
                    </span>
                </div>
                <div style={{ display: 'flex', gap: '1rem', alignItems: 'center' }}>
                    <Button
                        type="primary"
                        icon={<RobotOutlined />}
                        onClick={handleAIAnalysis}
                        loading={aiLoading}
                        disabled={!plotUrl && !result}
                        style={{
                            height: '40px',
                            padding: '0 24px',
                            borderRadius: '8px',
                            background: 'linear-gradient(135deg, #22d3ee 0%, #0891b2 100%)',
                            border: 'none',
                            boxShadow: '0 4px 6px -1px rgba(34, 211, 238, 0.2)'
                        }}
                    >
                        {aiLoading ? t('strategy_plot.interpreting', 'Analysing...') : t('strategy_plot.ai_interpretation', 'Start Analysis')}
                    </Button>
                </div>
            </div>

            {Object.keys(analyses).length > 0 ? (
                <AIInsight
                    analyses={analyses}
                    activeTab={activeTab || Object.keys(analyses)[0]}
                    onTabChange={setActiveTab}
                />
            ) : (
                <div style={{ textAlign: 'center', padding: '2rem', color: '#888' }}>
                    {t('history.no_ai_analysis', 'No AI analysis available. Click the button above to generate one.')}
                </div>
            )}
        </div>
    );
}

export default AIInsightTab;
