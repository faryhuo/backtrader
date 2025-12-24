/**
 * Site Configuration API
 *
 * Public API for fetching site-level configuration.
 * No authentication required for GET, requires auth for PUT.
 */

import { buildRequest, parseResponse, API_URL } from './apiCore';

const DEFAULT_CONFIG = {
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

/**
 * Fetch site configuration from backend
 * @returns {Promise<Object>} Site configuration object
 */
export async function getSiteConfig() {
    try {
        // Public endpoint - use simple fetch without auth
        const response = await fetch(`${API_URL}/site/config`);
        return await parseResponse(response);
    } catch (error) {
        console.warn('Failed to fetch site config, using defaults:', error);
        return DEFAULT_CONFIG;
    }
}

/**
 * Fetch site configuration for admin editing (includes sources)
 * @returns {Promise<Object>} Site configuration with sources
 */
export async function getSiteConfigAdmin() {
    const response = await buildRequest('/site/config/admin');
    return await parseResponse(response);
}

/**
 * Update site configuration
 * @param {Object} config - Configuration fields to update
 * @returns {Promise<Object>} Update result
 */
export async function updateSiteConfig(config) {
    const response = await buildRequest('/site/config', {
        method: 'PUT',
        body: JSON.stringify(config)
    });
    return await parseResponse(response);
}

/**
 * Reset site configuration to defaults
 * @returns {Promise<Object>} Reset result
 */
export async function resetSiteConfig() {
    const response = await buildRequest('/site/config/reset', {
        method: 'POST'
    });
    return await parseResponse(response);
}

export const siteApi = {
    getSiteConfig,
    getSiteConfigAdmin,
    updateSiteConfig,
    resetSiteConfig
};
