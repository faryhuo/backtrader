/**
 * Coerce a parameter value to the appropriate type.
 * Used by strategy parameter inputs to parse user input.
 *
 * @param {string} type - Parameter type ('int', 'float', or other)
 * @param {string|number} value - Raw input value
 * @returns {number|string} Parsed value of the appropriate type
 */
export function coerceParamValue(type, value) {
    if (type === 'int') {
        return parseInt(value, 10) || 0;
    }
    if (type === 'float') {
        return parseFloat(value) || 0;
    }
    return value;
}
