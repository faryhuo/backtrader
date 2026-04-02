/* eslint-disable react-refresh/only-export-components */
/**
 * Settings Context
 * 
 * Provides AI settings (models, prompts) to components.
 * Fetches settings from backend API on mount, with localStorage fallback.
 */

import { createContext, useContext, useState, useEffect, useCallback, useMemo } from 'react';
import PropTypes from 'prop-types';
import { api } from '../services/api';
import { DEFAULT_SETTINGS } from '../constants/settingsConstants';

const SettingsContext = createContext(null);

export function SettingsProvider({ children }) {
    const [settings, setSettings] = useState(DEFAULT_SETTINGS);
    const [loading, setLoading] = useState(true);

    const loadFromLocalStorage = useCallback(() => {
        try {
            const stored = localStorage.getItem('userSettings');
            if (stored) {
                const parsed = JSON.parse(stored);
                // Migration handling
                if (parsed.aiModel && !parsed.selectedModels) {
                    parsed.selectedModels = [parsed.aiModel];
                    delete parsed.aiModel;
                }
                setSettings({ ...DEFAULT_SETTINGS, ...parsed });
            }
        } catch (e) {
            console.error('Failed to read settings from localStorage', e);
        }
    }, []);

    const loadSettings = useCallback(async () => {
        try {
            const response = await api.getSettings();

            if (response.status === 'ok' && response.settings) {
                const dbSettings = {
                    selectedModels: response.settings.selected_models || DEFAULT_SETTINGS.selectedModels,
                    codeAnalysisPrompt: response.settings.code_analysis_prompt || DEFAULT_SETTINGS.codeAnalysisPrompt,
                    codeRewritePrompt: response.settings.code_rewrite_prompt || DEFAULT_SETTINGS.codeRewritePrompt,
                    fullStrategyAnalysisPrompt: response.settings.full_strategy_analysis_prompt || DEFAULT_SETTINGS.fullStrategyAnalysisPrompt
                };
                setSettings(dbSettings);
                // Also sync to localStorage for backward compatibility
                localStorage.setItem('userSettings', JSON.stringify(dbSettings));
            } else {
                // Fallback to localStorage
                loadFromLocalStorage();
            }
        } catch (error) {
            console.error('Failed to load settings from API:', error);
            loadFromLocalStorage();
        } finally {
            setLoading(false);
        }
    }, [loadFromLocalStorage]);

    useEffect(() => {
        loadSettings();
    }, [loadSettings]);

    const getAvailableModels = useCallback(() => {
        return settings.selectedModels && settings.selectedModels.length > 0
            ? settings.selectedModels
            : DEFAULT_SETTINGS.selectedModels;
    }, [settings.selectedModels]);

    const refreshSettings = useCallback(() => {
        setLoading(true);
        loadSettings();
    }, [loadSettings]);

    const contextValue = useMemo(() => ({
        settings,
        loading,
        getAvailableModels,
        refreshSettings
    }), [settings, loading, getAvailableModels, refreshSettings]);

    return (
        <SettingsContext.Provider value={contextValue}>
            {children}
        </SettingsContext.Provider>
    );
}

SettingsProvider.propTypes = {
    children: PropTypes.node.isRequired
};

export function useSettingsContext() {
    const context = useContext(SettingsContext);
    if (!context) {
        // Return defaults if used outside provider
        return {
            settings: DEFAULT_SETTINGS,
            loading: false,
            getAvailableModels: () => DEFAULT_SETTINGS.selectedModels,
            refreshSettings: () => { }
        };
    }
    return context;
}

export default SettingsContext;

