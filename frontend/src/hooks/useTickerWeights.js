import { useState, useCallback, useMemo } from 'react';

/**
 * Hook for managing ticker/weight pairs in portfolio backtest.
 * Provides add, remove, update, normalize, and equal weight operations.
 *
 * @param {Object} options - Initial configuration
 * @param {string[]} options.initialTickers - Initial ticker symbols
 * @param {number[]} options.initialWeights - Initial weights (0-1)
 * @returns {Object} Ticker/weight state and handlers
 */
export function useTickerWeights({
    initialTickers = ['AAPL', 'GOOGL'],
    initialWeights = [0.5, 0.5],
} = {}) {
    const [tickers, setTickers] = useState(initialTickers);
    const [weights, setWeights] = useState(initialWeights);

    // Add a new ticker with zero weight
    const addTicker = useCallback(() => {
        setTickers(prev => [...prev, '']);
        setWeights(prev => [...prev, 0]);
    }, []);

    // Remove ticker at index
    const removeTicker = useCallback((index) => {
        if (tickers.length <= 1) return;
        setTickers(prev => prev.filter((_, i) => i !== index));
        setWeights(prev => prev.filter((_, i) => i !== index));
    }, [tickers.length]);

    // Update ticker symbol at index
    const updateTicker = useCallback((index, value) => {
        setTickers(prev => {
            const newTickers = [...prev];
            newTickers[index] = value.toUpperCase();
            return newTickers;
        });
    }, []);

    // Update weight at index
    const updateWeight = useCallback((index, value) => {
        setWeights(prev => {
            const newWeights = [...prev];
            newWeights[index] = value || 0;
            return newWeights;
        });
    }, []);

    // Normalize weights to sum to 1
    const normalizeWeights = useCallback(() => {
        const total = weights.reduce((a, b) => a + b, 0);
        if (total > 0) {
            setWeights(weights.map(w => Math.round((w / total) * 100) / 100));
        }
    }, [weights]);

    // Set equal weights for all tickers
    const equalWeights = useCallback(() => {
        const equalWeight = Math.round((1 / tickers.length) * 100) / 100;
        setWeights(tickers.map(() => equalWeight));
    }, [tickers]);

    // Calculate total weight
    const totalWeight = useMemo(() => {
        return weights.reduce((a, b) => a + b, 0);
    }, [weights]);

    // Check if weights are valid (sum to ~1)
    const isWeightValid = useMemo(() => {
        return Math.abs(totalWeight - 1) < 0.01;
    }, [totalWeight]);

    // Get valid tickers (non-empty)
    const validTickers = useMemo(() => {
        return tickers.filter(t => t.trim());
    }, [tickers]);

    // Reset to initial state
    const reset = useCallback(() => {
        setTickers(initialTickers);
        setWeights(initialWeights);
    }, [initialTickers, initialWeights]);

    return {
        tickers,
        weights,
        addTicker,
        removeTicker,
        updateTicker,
        updateWeight,
        normalizeWeights,
        equalWeights,
        totalWeight,
        isWeightValid,
        validTickers,
        reset,
        setTickers,
        setWeights,
    };
}

export default useTickerWeights;
