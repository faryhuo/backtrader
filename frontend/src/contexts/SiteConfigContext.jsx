/**
 * Site Configuration Context
 * 
 * Provides site configuration to landing page components.
 * Fetches config from backend API on mount.
 */

import { createContext, useContext, useState, useEffect } from 'react';
import { getSiteConfig } from '../services/siteApi';

const SiteConfigContext = createContext(null);

const defaultConfig = {
    site: {
        title: 'Backtrader Pro',
        description: 'Professional quantitative trading platform'
    },
    links: {
        docs: '',
        github: '',
        twitter: '',
        email: ''
    },
    stats: {
        strategies: '50+',
        backtests: '10K+',
        users: '1K+'
    },
    features: {
        loginEnabled: false,
        liveTrading: false
    }
};

export function SiteConfigProvider({ children }) {
    const [config, setConfig] = useState(defaultConfig);
    const [loading, setLoading] = useState(true);

    useEffect(() => {
        let mounted = true;

        getSiteConfig().then((data) => {
            if (mounted) {
                setConfig(data);
                setLoading(false);
            }
        }).catch(() => {
            if (mounted) {
                setLoading(false);
            }
        });

        return () => {
            mounted = false;
        };
    }, []);

    return (
        <SiteConfigContext.Provider value={{ config, loading }}>
            {children}
        </SiteConfigContext.Provider>
    );
}

export function useSiteConfig() {
    const context = useContext(SiteConfigContext);
    if (!context) {
        // Return default if used outside provider
        return { config: defaultConfig, loading: false };
    }
    return context;
}

export default SiteConfigContext;
