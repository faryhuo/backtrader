import { useCallback, useEffect, useMemo, useRef, useState } from 'react'
import { api } from '../services/api'
import { coerceParamValue } from '../utils/paramUtils'

/**
 * Hook for fetching and managing strategy parameters.
 * Shared between RunStrategy and PortfolioBacktest pages.
 *
 * @param {string} selectedStrategy - Currently selected strategy name
 * @param {object} [options]
 * @param {boolean} [options.enabled=true] - Whether to fetch strategy data
 * @param {boolean} [options.includeCode=true] - Whether to fetch strategy code
 * @param {object|null} [options.initialOverrides=null] - Values to override defaults
 * @returns {Object} Strategy params state and handlers
 */
export function useStrategyParams(selectedStrategy, options = {}) {
    const {
        enabled = true,
        includeCode = true,
        initialOverrides = null
    } = options

    const [strategyParams, setStrategyParams] = useState([])
    const [paramOverrides, setParamOverrides] = useState({})
    const [paramDefaults, setParamDefaults] = useState({})
    const [strategyCode, setStrategyCode] = useState('')
    const [loading, setLoading] = useState(false)
    const [error, setError] = useState(null)

    const requestIdRef = useRef(0)

    const refresh = useCallback(async () => {
        if (!enabled) return

        const requestId = ++requestIdRef.current

        if (!selectedStrategy) {
            setStrategyParams([])
            setParamOverrides({})
            setParamDefaults({})
            setStrategyCode('')
            setError(null)
            return
        }

        setLoading(true)
        setError(null)

        try {
            const paramsData = await api.getStrategyParams(selectedStrategy)
            if (requestId !== requestIdRef.current) return

            const params = paramsData?.params || []
            setStrategyParams(params)

            const defaults = {}
            params.forEach(p => {
                defaults[p.name] = p.value
            })
            setParamDefaults(defaults)

            const mergedOverrides = initialOverrides
                ? { ...defaults, ...initialOverrides }
                : defaults
            setParamOverrides(mergedOverrides)

            if (includeCode) {
                try {
                    const strategyData = await api.getStrategy(selectedStrategy)
                    if (requestId !== requestIdRef.current) return
                    setStrategyCode(strategyData?.code || '')
                } catch {
                    if (requestId !== requestIdRef.current) return
                    setStrategyCode('')
                }
            } else {
                setStrategyCode('')
            }
        } catch (err) {
            if (requestId !== requestIdRef.current) return
            console.warn('Failed to fetch strategy details:', err)
            setStrategyParams([])
            setParamOverrides({})
            setParamDefaults({})
            setStrategyCode('')
            setError(err)
        } finally {
            if (requestId === requestIdRef.current) setLoading(false)
        }
    }, [enabled, selectedStrategy, includeCode, initialOverrides])

    useEffect(() => {
        refresh()
    }, [refresh])

    // Handle parameter value change with type coercion
    const handleParamChange = useCallback((name, value, type) => {
        const parsedValue = coerceParamValue(type, value)
        setParamOverrides(prev => ({ ...prev, [name]: parsedValue }))
    }, [])

    // Reset params to defaults
    const resetParams = useCallback(() => {
        setParamOverrides(paramDefaults)
    }, [paramDefaults])

    // Get params object for API call (null if no overrides)
    const getParamsForApi = useCallback(() => {
        return Object.keys(paramOverrides).length > 0 ? paramOverrides : null
    }, [paramOverrides])

    return useMemo(() => ({
        strategyParams,
        paramOverrides,
        setParamOverrides,
        paramDefaults,
        strategyCode,
        loading,
        error,
        refresh,
        handleParamChange,
        resetParams,
        getParamsForApi
    }), [
        strategyParams,
        paramOverrides,
        paramDefaults,
        strategyCode,
        loading,
        error,
        refresh,
        handleParamChange,
        resetParams,
        getParamsForApi
    ])
}

export default useStrategyParams;
