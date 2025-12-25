import { useState, useCallback } from 'react';
import { message } from 'antd';
import { useTranslation } from 'react-i18next';
import { api } from '../services/api';
import { DEFAULT_CREDENTIALS } from '../constants/settingsConstants';

/**
 * Custom hook for managing credentials state and operations
 */
export function useCredentials() {
    const { t } = useTranslation();
    const [credentials, setCredentials] = useState(DEFAULT_CREDENTIALS);
    const [credentialSources, setCredentialSources] = useState({});
    const [testingCredential, setTestingCredential] = useState(null);
    const [loading, setLoading] = useState(false);

    const loadCredentials = useCallback(async () => {
        try {
            const response = await api.getCredentials();
            if (response.credentials) {
                setCredentials(response.credentials);
                setCredentialSources(response.sources || {});
            }
        } catch (error) {
            console.error('Failed to load credentials:', error);
            message.error(t('settings.credentials.load_failed', 'Failed to load credentials'));
        }
    }, [t]);

    const handleCredentialChange = useCallback((key, value) => {
        setCredentials(prev => ({ ...prev, [key]: value }));
    }, []);

    const handleCCXTCredentialChange = useCallback((exchange, mode, field, value) => {
        setCredentials(prev => ({
            ...prev,
            ccxt: {
                ...prev.ccxt,
                [exchange]: {
                    ...prev.ccxt[exchange],
                    [mode]: {
                        ...prev.ccxt[exchange]?.[mode],
                        [field]: value
                    }
                }
            }
        }));
    }, []);

    const handleSaveCredentials = useCallback(async (credentialType) => {
        try {
            setLoading(true);
            let response;

            if (credentialType === 'openai') {
                response = await api.updateCredentials({
                    openai_api_key: credentials.openai_api_key,
                    openai_base_url: credentials.openai_base_url
                });
            } else if (credentialType === 'logto') {
                response = await api.updateCredentials({
                    // Server-side JWT validation settings
                    logto_issuer: credentials.logto_issuer,
                    logto_jwks_uri: credentials.logto_jwks_uri,
                    logto_audience: credentials.logto_audience,
                    logto_required_scopes: credentials.logto_required_scopes,
                    enable_login: credentials.enable_login,
                    // Frontend OAuth configuration
                    logto_endpoint: credentials.logto_endpoint,
                    logto_app_id: credentials.logto_app_id,
                    logto_redirect_uri: credentials.logto_redirect_uri,
                    logto_post_logout_redirect_uri: credentials.logto_post_logout_redirect_uri
                });
            } else if (credentialType === 'proxy') {
                response = await api.updateCredentials({
                    http_proxy: credentials.http_proxy,
                    https_proxy: credentials.https_proxy
                });
            } else if (credentialType.startsWith('ccxt-')) {
                const [, exchange, mode] = credentialType.split('-');
                const creds = credentials.ccxt[exchange]?.[mode] || {};
                response = await api.updateCCXTCredentials(exchange, mode, creds);
            }

            if (response.status === 'ok') {
                message.success(t('settings.credentials.saved', 'Credentials saved successfully'));
                await loadCredentials();

                // Show restart confirmation dialog for settings that require server restart
                if (['logto', 'proxy'].includes(credentialType)) {
                    const { Modal } = await import('antd');
                    Modal.info({
                        title: t('settings.restart_required', 'Server Restart Required'),
                        content: t('settings.restart_hint', 'These settings require a server restart to take effect. Please restart the backend server manually.'),
                        okText: t('common.ok', 'OK')
                    });
                }
            }
        } catch (error) {
            console.error('Failed to save credentials:', error);
            message.error(error.message || t('settings.credentials.save_failed', 'Failed to save credentials'));
        } finally {
            setLoading(false);
        }
    }, [credentials, loadCredentials, t]);

    const handleTestCredential = useCallback(async (credentialType) => {
        try {
            setTestingCredential(credentialType);
            let params = {};

            if (credentialType === 'openai') {
                params = {
                    credential_type: 'openai',
                    api_key: credentials.openai_api_key,
                    base_url: credentials.openai_base_url
                };
            } else if (credentialType === 'logto') {
                params = {
                    credential_type: 'logto',
                    issuer: credentials.logto_issuer,
                    jwks_uri: credentials.logto_jwks_uri
                };
            } else if (credentialType.startsWith('ccxt-')) {
                const [, exchange, mode] = credentialType.split('-');
                const creds = credentials.ccxt[exchange]?.[mode] || {};
                params = {
                    credential_type: 'ccxt',
                    exchange,
                    mode,
                    api_key: creds.api_key,
                    secret: creds.secret,
                    passphrase: creds.passphrase
                };
            }

            const response = await api.testCredential(params.credential_type, params);

            if (response.valid) {
                message.success(response.message || t('settings.credentials.valid', 'Credentials are valid'));
            } else {
                message.error(response.message || t('settings.credentials.invalid', 'Credentials are invalid'));
            }
        } catch (error) {
            console.error('Failed to test credentials:', error);
            message.error(error.message || t('settings.credentials.test_failed', 'Failed to test credentials'));
        } finally {
            setTestingCredential(null);
        }
    }, [credentials, t]);

    const handleResetCredential = useCallback(async (credentialKey) => {
        try {
            setLoading(true);
            const response = await api.resetCredential(credentialKey);

            if (response.status === 'ok') {
                message.success(t('settings.credentials.reset_to_env', { key: credentialKey }));
                await loadCredentials();
            }
        } catch (error) {
            console.error('Failed to reset credential:', error);
            message.error(error.message || t('settings.credentials.reset_failed', 'Failed to reset credential'));
        } finally {
            setLoading(false);
        }
    }, [loadCredentials, t]);

    return {
        credentials,
        credentialSources,
        testingCredential,
        loading,
        loadCredentials,
        handleCredentialChange,
        handleCCXTCredentialChange,
        handleSaveCredentials,
        handleTestCredential,
        handleResetCredential
    };
}

export default useCredentials;
