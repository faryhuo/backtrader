import { useCallback, useEffect, useMemo, useRef, useState } from 'react'
import { api } from '../services/api'

/**
 * Hook for fetching and managing the strategies list.
 *
 * - Loads strategies when `enabled` is true
 * - Optionally auto-selects the first strategy if current selection is empty/invalid
 * - Provides a `refresh` function for manual reload
 */
export function useStrategies(options = {}) {
    const {
        enabled = true,
        autoSelectFirst = true,
        initialSelectedStrategy = ''
    } = options

    const [strategies, setStrategies] = useState([])
    const [selectedStrategy, setSelectedStrategy] = useState(initialSelectedStrategy)
    const [loading, setLoading] = useState(false)
    const [error, setError] = useState(null)

    const requestIdRef = useRef(0)

    const refresh = useCallback(async () => {
        if (!enabled) return []

        const requestId = ++requestIdRef.current
        setLoading(true)
        setError(null)

        try {
            const names = await api.getStrategies()
            if (requestId !== requestIdRef.current) return names || []

            const safeNames = Array.isArray(names) ? names : []
            setStrategies(safeNames)

            if (autoSelectFirst) {
                setSelectedStrategy(prev => {
                    if (!safeNames.length) return prev || ''
                    if (!prev || !safeNames.includes(prev)) return safeNames[0]
                    return prev
                })
            }

            return safeNames
        } catch (err) {
            if (requestId !== requestIdRef.current) return []
            console.error('Failed to fetch strategies:', err)
            setStrategies([])
            setError(err)
            return []
        } finally {
            if (requestId === requestIdRef.current) setLoading(false)
        }
    }, [enabled, autoSelectFirst])

    useEffect(() => {
        if (!enabled) return
        refresh()
    }, [enabled, refresh])

    return useMemo(() => ({
        strategies,
        selectedStrategy,
        setSelectedStrategy,
        loading,
        error,
        refresh
    }), [strategies, selectedStrategy, loading, error, refresh])
}

export default useStrategies

