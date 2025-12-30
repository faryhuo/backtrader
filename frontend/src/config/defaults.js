/**
 * Centralized Default Configuration Values
 * 
 * Fetches default values from backend /site/defaults endpoint and caches them.
 * Provides fallback values if the API is unavailable.
 * 
 * Usage:
 *   import { getDefaults, fetchDefaults } from '../config/defaults';
 *   
 *   // In component initialization or App.js
 *   await fetchDefaults();
 *   
 *   // In component state initialization
 *   const defaults = getDefaults();
 *   const [commission, setCommission] = useState(defaults.backtest.commission);
 */

import { API_URL } from '../services/apiCore';

// Cached defaults after fetching
let cachedDefaults = null;

// Hardcoded fallback defaults in case API fails
// These should match backend/src/contracts/defaults.py
const FALLBACK_DEFAULTS = {
    backtest: {
        initial_cash: 100000.0,
        commission: 0.0005,
        stake: 100,
        timeframe: '1d',
        sizer_type: 'fixed_size',
        sizer_percent: 10.0,
        sizer_risk_percent: 2.0,
    },
    walkforward: {
        initial_cash: 100000.0,
        commission: 0.0005,
        stake: 100,
        train_period_days: 365,
        test_period_days: 90,
        anchored: false,
        optimization_metric: 'sharpe_ratio',
        timeframe: '1d',
        sizer_type: 'fixed_size',
    },
    live: {
        initial_cash: 10000.0,
        commission: 0.001,
    },
    options: {
        timeframes: ['1d', '1h', '15m', '5m', '1m'],
        sizer_types: ['fixed_size', 'percent_sizer', 'all_in_sizer', 'risk_sizer', 'kelly_sizer'],
        optimization_metrics: ['sharpe_ratio', 'total_return', 'profit_factor'],
    }
};

/**
 * Fetch defaults from backend API and cache them.
 * Should be called once during app initialization.
 * 
 * @returns {Promise<Object>} The defaults object
 */
export async function fetchDefaults() {
    if (cachedDefaults) {
        return cachedDefaults;
    }

    try {
        const response = await fetch(`${API_URL}/site/defaults`);
        if (response.ok) {
            cachedDefaults = await response.json();
            return cachedDefaults;
        }
        console.warn('Failed to fetch defaults from API, using fallback');
    } catch (error) {
        console.warn('Error fetching defaults:', error.message);
    }

    return FALLBACK_DEFAULTS;
}

/**
 * Get cached defaults synchronously.
 * Returns fallback if not yet fetched.
 * 
 * @returns {Object} The defaults object
 */
export function getDefaults() {
    return cachedDefaults || FALLBACK_DEFAULTS;
}

/**
 * Clear cached defaults (useful for testing).
 */
export function clearDefaultsCache() {
    cachedDefaults = null;
}

export default {
    fetchDefaults,
    getDefaults,
    clearDefaultsCache,
    FALLBACK_DEFAULTS,
};
