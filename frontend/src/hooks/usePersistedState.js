import { useState, useCallback } from 'react';

/**
 * A useState wrapper that persists state to localStorage.
 * Falls back to regular useState if localStorage is unavailable.
 *
 * @param {string} key - localStorage key
 * @param {*} defaultValue - default value if nothing is stored
 * @param {Object} options - optional serialization options
 * @param {Function} options.serialize - custom serializer (default: JSON.stringify)
 * @param {Function} options.deserialize - custom deserializer (default: JSON.parse)
 * @returns {[*, Function]} - [value, setValue] like useState
 */
export function usePersistedState(key, defaultValue, options = {}) {
    const {
        serialize = JSON.stringify,
        deserialize = JSON.parse,
    } = options;

    const [value, setValue] = useState(() => {
        try {
            const stored = localStorage.getItem(key);
            if (stored !== null) {
                return deserialize(stored);
            }
        } catch {
            // localStorage unavailable or corrupt data
        }
        return typeof defaultValue === 'function' ? defaultValue() : defaultValue;
    });

    const setPersistedValue = useCallback((newValue) => {
        setValue(prev => {
            const resolved = typeof newValue === 'function' ? newValue(prev) : newValue;
            try {
                localStorage.setItem(key, serialize(resolved));
            } catch {
                // localStorage full or unavailable
            }
            return resolved;
        });
    }, [key, serialize]);

    return [value, setPersistedValue];
}

export default usePersistedState;
