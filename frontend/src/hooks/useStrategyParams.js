import { useState, useEffect, useCallback } from 'react';
import { api } from '../services/api';

/**
 * Hook for fetching and managing strategy parameters.
 * Shared between RunStrategy and PortfolioBacktest pages.
 *
 * @param {string} selectedStrategy - Currently selected strategy name
 * @returns {Object} Strategy params state and handlers
 */
export function useStrategyParams(selectedStrategy) {
    const [strategyParams, setStrategyParams] = useState([]);
    const [paramOverrides, setParamOverrides] = useState({});
    const [strategyCode, setStrategyCode] = useState('');
    const [loading, setLoading] = useState(false);

    // Fetch strategy parameters and code when strategy changes
    useEffect(() => {
        const fetchStrategyDetails = async () => {
            if (!selectedStrategy) {
                setStrategyParams([]);
                setParamOverrides({});
                setStrategyCode('');
                return;
            }

            setLoading(true);
            try {
                // Fetch parameters
                const paramsData = await api.getStrategyParams(selectedStrategy);
                setStrategyParams(paramsData.params || []);

                // Initialize overrides with default values
                const defaults = {};
                (paramsData.params || []).forEach(p => {
                    defaults[p.name] = p.value;
                });
                setParamOverrides(defaults);

                // Fetch strategy code
                try {
                    const strategyData = await api.getStrategy(selectedStrategy);
                    if (strategyData && strategyData.code) {
                        setStrategyCode(strategyData.code);
                    }
                } catch {
                    // Strategy code is optional
                    setStrategyCode('');
                }
            } catch (err) {
                console.warn('Failed to fetch strategy details:', err);
                setStrategyParams([]);
                setParamOverrides({});
            } finally {
                setLoading(false);
            }
        };

        fetchStrategyDetails();
    }, [selectedStrategy]);

    // Handle parameter value change with type coercion
    const handleParamChange = useCallback((name, value, type) => {
        let parsedValue = value;
        if (type === 'int') {
            parsedValue = parseInt(value, 10) || 0;
        } else if (type === 'float') {
            parsedValue = parseFloat(value) || 0;
        }
        setParamOverrides(prev => ({ ...prev, [name]: parsedValue }));
    }, []);

    // Reset params to defaults
    const resetParams = useCallback(() => {
        const defaults = {};
        strategyParams.forEach(p => {
            defaults[p.name] = p.value;
        });
        setParamOverrides(defaults);
    }, [strategyParams]);

    // Get params object for API call (null if no overrides)
    const getParamsForApi = useCallback(() => {
        return Object.keys(paramOverrides).length > 0 ? paramOverrides : null;
    }, [paramOverrides]);

    return {
        strategyParams,
        paramOverrides,
        setParamOverrides,
        strategyCode,
        loading,
        handleParamChange,
        resetParams,
        getParamsForApi,
    };
}

export default useStrategyParams;
