/**
 * Portfolio API Response Normalizers
 * 
 * This module centralizes response transformation for portfolio APIs.
 * It provides the single source of truth for portfolio data structure,
 * handling legacy field names and ensuring consistent data types.
 */

/**
 * Normalizes portfolio API responses to a consistent schema.
 * 
 * Handles:
 * - Field name aliasing (correlation vs correlation_matrix)
 * - Type guards (ensures individual_results is always an array)
 * - Future schema migrations can be added here
 * 
 * @param {Object|null} data - Raw portfolio response from API
 * @returns {Object|null} Normalized portfolio data
 */
export function normalizePortfolioResult(data) {
    if (!data) return null

    return {
        ...data,
        // Normalize correlation field (handle legacy field names)
        correlation: data.correlation || data.correlation_matrix || null,
        // Normalize optimization field (handle legacy field names)
        optimization: data.optimization || data.optimization_suggestion || null,
        // Ensure individual_results is always an array
        individual_results: Array.isArray(data.individual_results)
            ? data.individual_results
            : []
    }
}

/**
 * Normalizes a list of portfolio history items.
 * 
 * @param {Array} items - Array of portfolio history records
 * @returns {Array} Normalized portfolio history records
 */
export function normalizePortfolioHistory(items) {
    if (!Array.isArray(items)) return []
    return items.map(normalizePortfolioResult)
}
