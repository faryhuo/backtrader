/**
 * Aggregated API exports for backward compatibility
 * 
 * This file re-exports all domain-specific APIs as a single unified `api` object.
 * New code should import directly from the domain-specific modules.
 * 
 * Domain modules:
 * - apiCore.js - Core utilities (buildRequest, parseResponse, auth)
 * - strategyApi.js - Strategy CRUD, versions, templates
 * - backtestApi.js - Backtest run, history, analysis
 * - marketDataApi.js - Ticker info and prices
 * - liveApi.js - Live trading sessions
 * - walkforwardApi.js - Walk-forward optimization
 * - settingsApi.js - Settings and credentials
 * - portfolioApi.js - Portfolio backtesting
 */

// Re-export core utilities
export { API_URL, setTokenGetter, getAccessToken, parseResponse, buildRequest } from './apiCore'

// Import domain APIs
import { strategyApi } from './strategyApi'
import { backtestApi } from './backtestApi'
import { marketDataApi } from './marketDataApi'
import { liveApi } from './liveApi'
import { walkforwardApi } from './walkforwardApi'
import { settingsApi } from './settingsApi'
import { portfolioApi } from './portfolioApi'
import { reportApi } from './reportApi'
import { setupApi } from './setupApi'
import { authApi } from './authApi'
import { basisApi } from './basisApi'

// Re-export domain APIs for direct import
export { strategyApi } from './strategyApi'
export { backtestApi } from './backtestApi'
export { marketDataApi } from './marketDataApi'
export { liveApi } from './liveApi'
export { walkforwardApi } from './walkforwardApi'
export { settingsApi } from './settingsApi'
export { portfolioApi } from './portfolioApi'
export { reportApi } from './reportApi'
export { setupApi } from './setupApi'
export { authApi } from './authApi'
export { basisApi } from './basisApi'

/**
 * Unified API object for backward compatibility
 * All methods from domain-specific modules are merged here
 */
export const api = {
    // Strategy API
    ...strategyApi,

    // Backtest API
    ...backtestApi,

    // Market Data API
    ...marketDataApi,

    // Live Trading API
    ...liveApi,

    // Walk-Forward API
    ...walkforwardApi,

    // Settings API
    ...settingsApi,

    // Portfolio API
    ...portfolioApi,

    // Report API
    ...reportApi,

    // Setup API
    ...setupApi,

    // Auth API
    ...authApi,

    // Basis Monitor API
    ...basisApi
}
