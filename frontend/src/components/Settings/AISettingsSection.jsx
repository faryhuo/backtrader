import { Card, Space, Input, Button } from 'antd';
import { SaveOutlined, UndoOutlined } from '@ant-design/icons';
import { useTranslation } from 'react-i18next';

/**
 * AI prompt settings section
 */
export function AISettingsSection({
    settings,
    loading,
    saved,
    onChange,
    onSave,
    onReset
}) {
    const { t } = useTranslation();

    return (
        <Card title={t('settings.ai_prompts', 'AI Prompts')} bordered={false}>
            <Space direction="vertical" style={{ width: '100%' }} size="large">
                <div>
                    <label>{t('settings.code_analysis_prompt', 'Code Analysis Prompt')}</label>
                    <Input.TextArea
                        rows={4}
                        value={settings.codeAnalysisPrompt}
                        onChange={(e) => onChange('codeAnalysisPrompt', e.target.value)}
                        placeholder="Use {code} as placeholder"
                        disabled={loading}
                    />
                </div>

                <div>
                    <label>{t('settings.full_strategy_analysis_prompt', 'Full Strategy Analysis Prompt')}</label>
                    <Input.TextArea
                        rows={6}
                        value={settings.fullStrategyAnalysisPrompt}
                        onChange={(e) => onChange('fullStrategyAnalysisPrompt', e.target.value)}
                        placeholder="Use {contextText}, {metricsText}, {logsText} as placeholders"
                        disabled={loading}
                    />
                </div>

                <div>
                    <label>{t('settings.code_rewrite_prompt', 'Code Rewrite Prompt')}</label>
                    <Input.TextArea
                        rows={4}
                        value={settings.codeRewritePrompt}
                        onChange={(e) => onChange('codeRewritePrompt', e.target.value)}
                        placeholder="Use {code} as placeholder"
                        disabled={loading}
                    />
                </div>

                <div style={{ display: 'flex', justifyContent: 'flex-end', gap: '1rem', marginTop: '1rem' }}>
                    {saved && (
                        <span style={{ color: 'var(--success-color)', marginRight: 'auto', fontWeight: 500 }}>
                            {t('settings.saved', 'Settings saved!')}
                        </span>
                    )}
                    <Button icon={<UndoOutlined />} onClick={onReset} disabled={loading}>
                        {t('settings.reset', 'Reset Defaults')}
                    </Button>
                    <Button type="primary" icon={<SaveOutlined />} onClick={onSave} loading={loading}>
                        {t('settings.save', 'Save Changes')}
                    </Button>
                </div>
            </Space>
        </Card>
    );
}

export default AISettingsSection;
