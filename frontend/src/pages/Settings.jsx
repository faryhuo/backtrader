import { useState, useEffect } from 'react';
import { useTranslation } from 'react-i18next';
import { SaveOutlined, UndoOutlined } from '@ant-design/icons';
import { Select, message } from 'antd';
import { api } from '../services/api';
import './Settings.css';

const DEFAULT_SETTINGS = {
    selectedModels: ['gpt-5.1', 'deepseek-v3.1'],
    codeAnalysisPrompt: 'Please analyze the following Backtrader strategy code. Explain its logic, potential pitfalls, and suggest improvements:\n\n{code}',
    codeRewritePrompt: 'Please rewrite and optimize the following Backtrader strategy code to follow best practices and fix potential issues. Return ONLY the python code, no markdown formatting or explanation:\n\n{code}',
    fullStrategyAnalysisPrompt: 'Please analyze the trading strategy based on the following configurations, source code, performance metrics, the attached equity curve chart, and the recent trading logs.\n\n{contextText}\n\n{metricsText}\n\n{logsText}\n\nProvide a comprehensive assessment including:\n1. Overall Performance: Is it profitable and consistent?\n2. Risk Profile: analysis of drawdowns and volatility.\n3. Strengths & Weaknesses: What is working well and what isn\'t?\n4. Suggestions: Recommendations for improvement.\n5. Code Analysis: Comments on the strategy logic.\n6. Always return with Chinese.\n7. 不需要对策略代码逻辑进行点评'
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
    const [loading, setLoading] = useState(false);

    useEffect(() => {
        loadSettings();
    }, []);

    const loadSettings = async () => {
        try {
            setLoading(true);

            // Try to load from database
            const response = await api.getSettings();

            if (response.status === 'ok' && response.settings) {
                // Map backend field names to frontend
                const dbSettings = {
                    selectedModels: response.settings.selected_models || DEFAULT_SETTINGS.selectedModels,
                    codeAnalysisPrompt: response.settings.code_analysis_prompt || DEFAULT_SETTINGS.codeAnalysisPrompt,
                    codeRewritePrompt: response.settings.code_rewrite_prompt || DEFAULT_SETTINGS.codeRewritePrompt,
                    fullStrategyAnalysisPrompt: response.settings.full_strategy_analysis_prompt || DEFAULT_SETTINGS.fullStrategyAnalysisPrompt
                };
                setSettings(dbSettings);

                // Check if settings are defaults (not saved yet), try localStorage migration
                const isDefaults = JSON.stringify(dbSettings.selectedModels) === JSON.stringify(DEFAULT_SETTINGS.selectedModels) &&
                    dbSettings.codeAnalysisPrompt === DEFAULT_SETTINGS.codeAnalysisPrompt;

                if (isDefaults) {
                    await migrateFromLocalStorage();
                }
            } else {
                // Fallback: try localStorage migration
                await migrateFromLocalStorage();
            }
        } catch (error) {
            console.error('Failed to load settings from database:', error);
            // Fallback to localStorage
            await migrateFromLocalStorage();
        } finally {
            setLoading(false);
        }
    };

    const migrateFromLocalStorage = async () => {
        const storedSettings = localStorage.getItem('userSettings');
        if (storedSettings) {
            try {
                const parsed = JSON.parse(storedSettings);

                // Migration: old aiModel -> selectedModels
                if (parsed.aiModel && !parsed.selectedModels) {
                    parsed.selectedModels = [parsed.aiModel];
                    delete parsed.aiModel;
                }

                const migratedSettings = { ...DEFAULT_SETTINGS, ...parsed };
                setSettings(migratedSettings);

                // Auto-save to database (silent migration)
                try {
                    await saveToDatabase(migratedSettings, false);
                    console.log('Successfully migrated settings from localStorage to database');
                } catch (e) {
                    console.warn('Failed to auto-migrate settings to database:', e);
                }
            } catch (e) {
                console.error('Failed to parse localStorage settings:', e);
                setSettings(DEFAULT_SETTINGS);
            }
        }
    };

    const handleChange = (key, value) => {
        setSettings(prev => ({ ...prev, [key]: value }));
        setSaved(false);
    };

    const handleModelChange = (value) => {
        setSettings(prev => ({ ...prev, selectedModels: value }));
        setSaved(false);
    };

    const saveToDatabase = async (settingsToSave, showMessage = true) => {
        const payload = {
            selected_models: settingsToSave.selectedModels,
            code_analysis_prompt: settingsToSave.codeAnalysisPrompt,
            code_rewrite_prompt: settingsToSave.codeRewritePrompt,
            full_strategy_analysis_prompt: settingsToSave.fullStrategyAnalysisPrompt
        };

        const response = await api.updateSettings(payload);

        if (response.status === 'ok') {
            if (showMessage) {
                message.success(t('settings.saved', 'Settings saved!'));
            }
            return true;
        }
        return false;
    };

    const handleSave = async () => {
        try {
            setLoading(true);

            // Validate at least one model selected
            if (!settings.selectedModels || settings.selectedModels.length === 0) {
                message.error(t('settings.select_at_least_one', 'Please select at least one model.'));
                return;
            }

            // Try to save to database
            try {
                await saveToDatabase(settings, true);
                setSaved(true);
                setTimeout(() => setSaved(false), 3000);

                // Clear localStorage after successful DB save (optional)
                // localStorage.removeItem('userSettings');
            } catch (error) {
                console.error('Database save failed, falling back to localStorage:', error);
                message.warning('Saved to local storage (database unavailable)');

                // Fallback to localStorage
                localStorage.setItem('userSettings', JSON.stringify(settings));
                setSaved(true);
                setTimeout(() => setSaved(false), 3000);
            }
        } finally {
            setLoading(false);
        }
    };

    const handleReset = async () => {
        if (window.confirm(t('settings.confirm_reset', 'Are you sure you want to reset all settings to default?'))) {
            try {
                setLoading(true);

                // Try to reset in database
                try {
                    const response = await api.resetSettings();
                    if (response.status === 'ok') {
                        setSettings(DEFAULT_SETTINGS);
                        message.success(t('settings.reset_success', 'Settings reset to defaults'));
                        setSaved(true);
                        setTimeout(() => setSaved(false), 3000);
                    }
                } catch (error) {
                    console.error('Database reset failed, using localStorage:', error);

                    // Fallback to localStorage
                    setSettings(DEFAULT_SETTINGS);
                    localStorage.removeItem('userSettings');
                    message.success(t('settings.reset_success', 'Settings reset to defaults'));
                    setSaved(true);
                    setTimeout(() => setSaved(false), 3000);
                }
            } finally {
                setLoading(false);
            }
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
                        loading={loading}
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
                        disabled={loading}
                    />
                </div>

                <div className="settings-form-group">
                    <label>{t('settings.full_strategy_analysis_prompt', 'Full Strategy Analysis Prompt')}</label>
                    <textarea
                        className="settings-textarea"
                        rows={6}
                        value={settings.fullStrategyAnalysisPrompt}
                        onChange={(e) => handleChange('fullStrategyAnalysisPrompt', e.target.value)}
                        placeholder="Use {contextText}, {metricsText}, {logsText} as placeholders"
                        disabled={loading}
                    />
                </div>

                <div className="settings-form-group">
                    <label>{t('settings.code_rewrite_prompt', 'Code Rewrite Prompt')}</label>
                    <textarea
                        className="settings-textarea"
                        value={settings.codeRewritePrompt}
                        onChange={(e) => handleChange('codeRewritePrompt', e.target.value)}
                        placeholder="Use {code} as placeholder"
                        disabled={loading}
                    />
                </div>

                <div className="settings-actions">
                    <span className={`save-success ${saved ? 'visible' : ''}`}>
                        {t('settings.saved', 'Settings saved!')}
                    </span>
                    <button className="btn-secondary" onClick={handleReset} disabled={loading}>
                        <UndoOutlined /> {t('settings.reset', 'Reset Defaults')}
                    </button>
                    <button className="primary-btn" onClick={handleSave} disabled={loading}>
                        <SaveOutlined /> {t('settings.save', 'Save Changes')}
                    </button>
                </div>
            </div>
        </div>
    );
}

export default Settings;
