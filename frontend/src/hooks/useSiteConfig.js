import { useState, useCallback } from 'react';
import { message } from 'antd';
import { useTranslation } from 'react-i18next';
import { getSiteConfigAdmin, updateSiteConfig, resetSiteConfig } from '../services/siteApi';

const DEFAULT_SITE_CONFIG = {
    site_title: '',
    site_description: '',
    site_docs_url: '',
    site_github_url: '',
    site_twitter_url: '',
    site_email: '',
    site_stats_strategies: '',
    site_stats_backtests: '',
    site_stats_users: ''
};

/**
 * Custom hook for managing site configuration state
 */
export function useSiteConfig() {
    const { t } = useTranslation();
    const [config, setConfig] = useState(DEFAULT_SITE_CONFIG);
    const [sources, setSources] = useState({});
    const [loading, setLoading] = useState(false);
    const [saved, setSaved] = useState(false);

    const loadConfig = useCallback(async () => {
        setLoading(true);
        try {
            const response = await getSiteConfigAdmin();
            if (response.config) {
                setConfig(response.config);
                setSources(response.sources || {});
            }
        } catch (error) {
            console.error('Failed to load site config:', error);
            message.error(t('settings.load_error', 'Failed to load site configuration'));
        } finally {
            setLoading(false);
        }
    }, [t]);

    const handleChange = useCallback((field, value) => {
        setConfig(prev => ({
            ...prev,
            [field]: value
        }));
    }, []);

    const handleSave = useCallback(async () => {
        setLoading(true);
        try {
            await updateSiteConfig(config);
            message.success(t('settings.saved', 'Settings saved!'));
            setSaved(true);
            setTimeout(() => setSaved(false), 3000);
            // Reload to get updated sources
            await loadConfig();
        } catch (error) {
            console.error('Failed to save site config:', error);
            message.error(t('settings.save_error', 'Failed to save site configuration'));
        } finally {
            setLoading(false);
        }
    }, [config, loadConfig, t]);

    const handleReset = useCallback(async () => {
        if (!window.confirm(t('settings.reset_confirm', 'Reset site configuration to defaults?'))) {
            return;
        }

        setLoading(true);
        try {
            await resetSiteConfig();
            message.success(t('settings.reset_success', 'Site configuration reset to defaults'));
            await loadConfig();
        } catch (error) {
            console.error('Failed to reset site config:', error);
            message.error(t('settings.reset_error', 'Failed to reset site configuration'));
        } finally {
            setLoading(false);
        }
    }, [loadConfig, t]);

    return {
        config,
        sources,
        loading,
        saved,
        loadConfig,
        handleChange,
        handleSave,
        handleReset
    };
}
