/**
 * Site Configuration API
 * 
 * Public API for fetching site-level configuration.
 * No authentication required.
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

export const siteApi = {
    getSiteConfig
};
