import { useState, useCallback } from 'react';
import { Modal, message } from 'antd';
import { useTranslation } from 'react-i18next';
import { api } from '../services/api';
import { DEFAULT_SETTINGS } from '../constants/settingsConstants';

const FALLBACK_SELECTED_MODELS = DEFAULT_SETTINGS.selectedModels;

/**
 * Custom hook for managing AI settings state and operations
 */
export function useSettings() {
    const { t } = useTranslation();
    const [settings, setSettings] = useState(DEFAULT_SETTINGS);
    const [saved, setSaved] = useState(false);
    const [loading, setLoading] = useState(false);

    const saveToDatabase = useCallback(async (settingsToSave, showMessage = true) => {
        const payload = {
            selected_models: settingsToSave.selectedModels?.length
                ? settingsToSave.selectedModels
                : FALLBACK_SELECTED_MODELS,
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
    }, [t]);

    const migrateFromLocalStorage = useCallback(async () => {
        const storedSettings = localStorage.getItem('userSettings');
        if (storedSettings) {
            try {
                const parsed = JSON.parse(storedSettings);

                if (parsed.aiModel && !parsed.selectedModels) {
                    parsed.selectedModels = [parsed.aiModel];
                    delete parsed.aiModel;
                }

                const migratedSettings = { ...DEFAULT_SETTINGS, ...parsed };
                setSettings(migratedSettings);

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
    }, [saveToDatabase]);

    const loadSettings = useCallback(async () => {
        try {
            setLoading(true);
            const response = await api.getSettings();

            if (response.status === 'ok' && response.settings) {
                const dbSettings = {
                    selectedModels: response.settings.selected_models || DEFAULT_SETTINGS.selectedModels,
                    codeAnalysisPrompt: response.settings.code_analysis_prompt || DEFAULT_SETTINGS.codeAnalysisPrompt,
                    codeRewritePrompt: response.settings.code_rewrite_prompt || DEFAULT_SETTINGS.codeRewritePrompt,
                    fullStrategyAnalysisPrompt: response.settings.full_strategy_analysis_prompt || DEFAULT_SETTINGS.fullStrategyAnalysisPrompt
                };
                setSettings(dbSettings);

                const isDefaults = JSON.stringify(dbSettings.selectedModels) === JSON.stringify(DEFAULT_SETTINGS.selectedModels) &&
                    dbSettings.codeAnalysisPrompt === DEFAULT_SETTINGS.codeAnalysisPrompt;

                if (isDefaults) {
                    await migrateFromLocalStorage();
                }
            } else {
                await migrateFromLocalStorage();
            }
        } catch (error) {
            console.error('Failed to load settings from database:', error);
            await migrateFromLocalStorage();
        } finally {
            setLoading(false);
        }
    }, [migrateFromLocalStorage]);

    const handleChange = useCallback((key, value) => {
        setSettings(prev => ({ ...prev, [key]: value }));
        setSaved(false);
    }, []);

    const handleSave = useCallback(async () => {
        try {
            setLoading(true);

            try {
                await saveToDatabase(settings, true);
                setSaved(true);
                setTimeout(() => setSaved(false), 3000);
            } catch (error) {
                console.error('Database save failed, falling back to localStorage:', error);
                message.warning(t('settings.saved_local', 'Saved to local storage (database unavailable)'));
                localStorage.setItem('userSettings', JSON.stringify(settings));
                setSaved(true);
                setTimeout(() => setSaved(false), 3000);
            }
        } finally {
            setLoading(false);
        }
    }, [settings, saveToDatabase, t]);

    const handleReset = useCallback(async () => {
        const confirmed = await new Promise((resolve) => {
            Modal.confirm({
                title: t('settings.reset', 'Reset'),
                content: t('settings.confirm_reset', 'Are you sure you want to reset all settings to default?'),
                okText: t('common.confirm', 'Confirm'),
                cancelText: t('common.cancel', 'Cancel'),
                okType: 'danger',
                onOk: () => resolve(true),
                onCancel: () => resolve(false),
            });
        });
        if (!confirmed) {
            return;
        }

        try {
            setLoading(true);
            const response = await api.resetSettings();
            if (response.status === 'ok') {
                setSettings(DEFAULT_SETTINGS);
                message.success(t('settings.reset_success', 'Settings reset to defaults'));
                setSaved(true);
                setTimeout(() => setSaved(false), 3000);
            }
        } catch (error) {
            console.error('Database reset failed, using localStorage:', error);
            setSettings(DEFAULT_SETTINGS);
            localStorage.removeItem('userSettings');
            message.success(t('settings.reset_success', 'Settings reset to defaults'));
            setSaved(true);
            setTimeout(() => setSaved(false), 3000);
        } finally {
            setLoading(false);
        }
    }, [t]);

    return {
        settings,
        loading,
        saved,
        loadSettings,
        handleChange,
        handleSave,
        handleReset
    };
}

export default useSettings;
