import { useState, useEffect } from 'react';
import { useTranslation } from 'react-i18next';
import { SaveOutlined, UndoOutlined } from '@ant-design/icons';
import { Select } from 'antd';
import './Settings.css';

const DEFAULT_SETTINGS = {
    selectedModels: ['gpt-5.1', 'deepseek-v3.1'],
    codeAnalysisPrompt: 'Please analyze the following Backtrader strategy code. Explain its logic, potential pitfalls, and suggest improvements:\n\n{code}',
    codeRewritePrompt: 'Please rewrite and optimize the following Backtrader strategy code to follow best practices and fix potential issues. Return ONLY the python code, no markdown formatting or explanation:\n\n{code}'
};

const AVAILABLE_MODELS = [
    { value: 'gpt-5.1', label: 'GPT-5.1' },
    { value: 'gpt-4o', label: 'GPT-4o' },
    { value: 'gpt-4-turbo', label: 'GPT-4 Turbo' },
    { value: 'gpt-3.5-turbo', label: 'GPT-3.5 Turbo' },
    { value: 'deepseek-v3.1', label: 'DeepSeek V3.1' },
    { value: 'gemini-3-pro', label: 'Gemini 3 Pro' }
];

function Settings() {
    const { t } = useTranslation();
    const [settings, setSettings] = useState(DEFAULT_SETTINGS);
    const [saved, setSaved] = useState(false);

    useEffect(() => {
        const storedSettings = localStorage.getItem('userSettings');
        if (storedSettings) {
            // Migration: if old aiModel exists, convert to selectedModels
            const parsed = JSON.parse(storedSettings);
            if (parsed.aiModel && !parsed.selectedModels) {
                parsed.selectedModels = [parsed.aiModel];
                delete parsed.aiModel;
            }
            setSettings({ ...DEFAULT_SETTINGS, ...parsed });
        }
    }, []);

    const handleChange = (key, value) => {
        setSettings(prev => ({ ...prev, [key]: value }));
        setSaved(false);
    };

    const handleModelChange = (value) => {
        setSettings(prev => ({ ...prev, selectedModels: value }));
        setSaved(false);
    };

    const handleSave = () => {
        localStorage.setItem('userSettings', JSON.stringify(settings));
        setSaved(true);
        setTimeout(() => setSaved(false), 3000);
    };

    const handleReset = () => {
        if (window.confirm(t('settings.confirm_reset', 'Are you sure you want to reset all settings to default?'))) {
            setSettings(DEFAULT_SETTINGS);
            localStorage.removeItem('userSettings');
            setSaved(true);
            setTimeout(() => setSaved(false), 3000);
        }
    };

    return (
        <div className="page-container settings-page">
            <div className="settings-header">
                <h1>{t('settings.title', 'Settings')}</h1>
            </div>

            <div className="settings-section">
                <h2>{t('settings.ai_configuration', 'AI Configuration')}</h2>
                
                <div className="settings-form-group">
                    <label>{t('settings.default_model', 'Enabled AI Models (Select or Type to Add)')}</label>
                    <Select
                        mode="tags"
                        style={{ width: '100%' }}
                        placeholder="Select or type model names"
                        value={settings.selectedModels}
                        onChange={handleModelChange}
                        options={AVAILABLE_MODELS}
                    />
                    {(!settings.selectedModels || settings.selectedModels.length === 0) && (
                        <p style={{ color: 'var(--error-color)', fontSize: '0.9rem', marginTop: '0.5rem' }}>
                            {t('settings.select_at_least_one', 'Please select at least one model.')}
                        </p>
                    )}
                </div>

                <div className="settings-form-group">
                    <label>{t('settings.code_analysis_prompt', 'Code Analysis Prompt')}</label>
                    <textarea 
                        className="settings-textarea"
                        value={settings.codeAnalysisPrompt}
                        onChange={(e) => handleChange('codeAnalysisPrompt', e.target.value)}
                        placeholder="Use {code} as placeholder"
                    />
                </div>

                <div className="settings-form-group">
                    <label>{t('settings.code_rewrite_prompt', 'Code Rewrite Prompt')}</label>
                    <textarea 
                        className="settings-textarea"
                        value={settings.codeRewritePrompt}
                        onChange={(e) => handleChange('codeRewritePrompt', e.target.value)}
                        placeholder="Use {code} as placeholder"
                    />
                </div>

                <div className="settings-actions">
                    <span className={`save-success ${saved ? 'visible' : ''}`}>
                        {t('settings.saved', 'Settings saved!')}
                    </span>
                    <button className="btn-secondary" onClick={handleReset}>
                        <UndoOutlined /> {t('settings.reset', 'Reset Defaults')}
                    </button>
                    <button className="primary-btn" onClick={handleSave}>
                        <SaveOutlined /> {t('settings.save', 'Save Changes')}
                    </button>
                </div>
            </div>
        </div>
    );
}

export default Settings;
