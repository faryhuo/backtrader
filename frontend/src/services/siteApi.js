/**
 * Site Configuration API
 * 
 * Public API for fetching site-level configuration.
 * No authentication required for GET, requires auth for PUT.
 */

const API_BASE = import.meta.env.VITE_API_BASE_URL || '';

/**
 * Fetch site configuration from backend
 * @returns {Promise<Object>} Site configuration object
 */
export async function getSiteConfig() {
    try {
        const response = await fetch(`${API_BASE}/site/config`);
        if (!response.ok) {
            throw new Error(`Failed to fetch site config: ${response.status}`);
        }
        return await response.json();
    } catch (error) {
        console.warn('Failed to fetch site config, using defaults:', error);
        // Return default config on error
        return {
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
    }
}

/**
 * Fetch site configuration for admin editing (includes sources)
 * @returns {Promise<Object>} Site configuration with sources
 */
export async function getSiteConfigAdmin() {
    const token = localStorage.getItem('auth_token');
    const headers = {
        'Content-Type': 'application/json'
    };
    if (token) {
        headers['Authorization'] = `Bearer ${token}`;
    }

    const response = await fetch(`${API_BASE}/site/config/admin`, { headers });
    if (!response.ok) {
        throw new Error(`Failed to fetch site config: ${response.status}`);
    }
    return await response.json();
}

/**
 * Update site configuration
 * @param {Object} config - Configuration fields to update
 * @returns {Promise<Object>} Update result
 */
export async function updateSiteConfig(config) {
    const token = localStorage.getItem('auth_token');
    const headers = {
        'Content-Type': 'application/json'
    };
    if (token) {
        headers['Authorization'] = `Bearer ${token}`;
    }

    const response = await fetch(`${API_BASE}/site/config`, {
        method: 'PUT',
        headers,
        body: JSON.stringify(config)
    });

    if (!response.ok) {
        const error = await response.json().catch(() => ({ detail: 'Unknown error' }));
        throw new Error(error.detail || `Failed to update site config: ${response.status}`);
    }
    return await response.json();
}

/**
 * Reset site configuration to defaults
 * @returns {Promise<Object>} Reset result
 */
export async function resetSiteConfig() {
    const token = localStorage.getItem('auth_token');
    const headers = {
        'Content-Type': 'application/json'
    };
    if (token) {
        headers['Authorization'] = `Bearer ${token}`;
    }

    const response = await fetch(`${API_BASE}/site/config/reset`, {
        method: 'POST',
        headers
    });

    if (!response.ok) {
        const error = await response.json().catch(() => ({ detail: 'Unknown error' }));
        throw new Error(error.detail || `Failed to reset site config: ${response.status}`);
    }
    return await response.json();
}

export const siteApi = {
    getSiteConfig,
    getSiteConfigAdmin,
    updateSiteConfig,
    resetSiteConfig
};
