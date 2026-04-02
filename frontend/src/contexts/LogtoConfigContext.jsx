/* eslint-disable react-refresh/only-export-components */
import { createContext, useContext, useState, useEffect } from 'react';
import PropTypes from 'prop-types';
import { settingsApi } from '../services/settingsApi';

/**
 * Logto Configuration Context
 * 
 * Provides Logto configuration to all components.
 * Fetches configuration from backend API only.
 */

const LogtoConfigContext = createContext(null);

export function LogtoConfigProvider({ children }) {
    const [config, setConfig] = useState(null);
    const [loading, setLoading] = useState(true);
    const [error, setError] = useState(null);

    useEffect(() => {
        async function fetchConfig() {
            try {
                const response = await settingsApi.getLogtoConfig();
                if (response.status === 'ok' && response.config) {
                    setConfig(response.config);
                } else {
                    const errorMsg = 'Failed to fetch Logto config from API';
                    console.warn(errorMsg);
                    setError(new Error(errorMsg));
                    // Default to disabled login when no config
                    setConfig({
                        endpoint: null,
                        appId: null,
                        redirectUri: null,
                        postLogoutRedirectUri: null,
                        enableLogin: false,
                        authProvider: 'none',
                        registrationEnabled: false,
                    });
                }
            } catch (err) {
                console.error('Error fetching Logto config:', err);
                setError(err);
                // Default to disabled login on error
                setConfig({
                    endpoint: null,
                    appId: null,
                    redirectUri: null,
                    postLogoutRedirectUri: null,
                    enableLogin: false,
                    authProvider: 'none',
                    registrationEnabled: false,
                });
            } finally {
                setLoading(false);
            }
        }

        fetchConfig();
    }, []);

    return (
        <LogtoConfigContext.Provider value={{ config, loading, error }}>
            {children}
        </LogtoConfigContext.Provider>
    );
}

LogtoConfigProvider.propTypes = {
    children: PropTypes.node.isRequired,
};

export function useLogtoConfig() {
    const context = useContext(LogtoConfigContext);
    if (context === null) {
        throw new Error('useLogtoConfig must be used within LogtoConfigProvider');
    }
    return context;
}
