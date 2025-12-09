export const isNumber = (value) => typeof value === 'number' && !Number.isNaN(value)

export const formatNumber = (value, digits = 2) =>
    isNumber(value) ? value.toFixed(digits) : 'N/A'

export const formatPercent = (value, digits = 2, multiplier = 1) =>
    isNumber(value) ? `${(value * multiplier).toFixed(digits)}%` : 'N/A'

export const formatCurrency = (value, digits = 2) =>
    isNumber(value)
        ? `$${value.toLocaleString(undefined, { minimumFractionDigits: digits, maximumFractionDigits: digits })}`
        : 'N/A'
