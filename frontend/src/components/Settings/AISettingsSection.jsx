import { Card, Space, Select, Input, Button } from 'antd';
import { SaveOutlined, UndoOutlined } from '@ant-design/icons';
import { useTranslation } from 'react-i18next';
import { AVAILABLE_MODELS } from '../../constants/settingsConstants';

/**
 * AI Configuration settings section
 */
export function AISettingsSection({
    settings,
    loading,
    saved,
    onModelChange,
    onChange,
    onSave,
    onReset
}) {
    const { t } = useTranslation();

    return (
        <Card title={t('settings.ai_configuration', 'AI Configuration')} bordered={false}>
            <Space direction="vertical" style={{ width: '100%' }} size="large">
                <div>
                    <label>{t('settings.default_model', 'Enabled AI Models (Select or Type to Add)')}</label>
                    <Select
                        mode="tags"
                        style={{ width: '100%' }}
                        placeholder="Select or type model names"
                        value={settings.selectedModels}
                        onChange={onModelChange}
                        options={AVAILABLE_MODELS}
                        loading={loading}
                    />
                    {(!settings.selectedModels || settings.selectedModels.length === 0) && (
                        <p style={{ color: 'var(--error-color)', fontSize: '0.9rem', marginTop: '0.5rem' }}>
                            {t('settings.select_at_least_one', 'Please select at least one model.')}
                        </p>
                    )}
                </div>

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
