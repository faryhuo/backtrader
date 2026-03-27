function normalizeErrorMessage(rawMessage) {
    let normalized = String(rawMessage || '').trim()

    const removablePrefixes = [
        'Backtest failed:',
        'Strategy load failed:',
    ]

    for (const prefix of removablePrefixes) {
        if (normalized.toLowerCase().startsWith(prefix.toLowerCase())) {
            normalized = normalized.slice(prefix.length).trim()
        }
    }

    return normalized
}

function parseInsufficientData(message) {
    const match = message.match(
        /range\s+(?<startDate>\d{4}-\d{2}-\d{2})\s+to\s+(?<endDate>\d{4}-\d{2}-\d{2})\s+returned\s+(?<availableBars>\d+)\s+bars?,\s+but\s+the strategy indicators need at least\s+(?<requiredBars>\d+)\s+bars?/i
    )

    if (!match?.groups) {
        return null
    }

    return {
        startDate: match.groups.startDate,
        endDate: match.groups.endDate,
        availableBars: Number(match.groups.availableBars),
        requiredBars: Number(match.groups.requiredBars),
    }
}

function buildDescriptor({
    type,
    title,
    description = '',
    suggestions = [],
    detail = '',
}) {
    return {
        type,
        title,
        description,
        suggestions,
        detail,
    }
}

function translate(t, key, defaultValue, options = null) {
    const interpolate = (text) => {
        if (!options || typeof text !== 'string') {
            return text
        }

        return Object.entries(options).reduce(
            (result, [optionKey, optionValue]) => result.replaceAll(`{{${optionKey}}}`, String(optionValue)),
            text
        )
    }

    if (typeof t !== 'function') {
        return interpolate(defaultValue || key)
    }

    if (options && Object.keys(options).length > 0) {
        const translated = t(key, { ...options, defaultValue })
        if (typeof translated === 'string' && translated !== key) {
            return interpolate(translated)
        }
    }

    const fallbackResult = t(key, defaultValue)
    if (typeof fallbackResult === 'string') {
        return interpolate(fallbackResult)
    }

    return interpolate(defaultValue || key)
}

export function formatStrategyError(rawMessage, t = (key, fallback) => fallback || key) {
    const detail = String(rawMessage || '').trim()
    const message = normalizeErrorMessage(rawMessage)

    if (!message) {
        return buildDescriptor({
            type: 'generic',
            title: translate(
                t,
                'common.strategy_errors.generic.title',
                'Strategy execution failed'
            ),
            description: translate(
                t,
                'common.strategy_errors.generic.description',
                'The strategy could not be executed. Please review the parameters or strategy code and try again.'
            ),
            detail,
        })
    }

    const insufficientData = parseInsufficientData(message)
    if (insufficientData || /insufficient market data/i.test(message)) {
        const description = insufficientData
            ? translate(
                t,
                'common.strategy_errors.insufficient_data.description_with_counts',
                'The selected range returned {{availableBars}} bars from {{startDate}} to {{endDate}}, but this strategy needs at least {{requiredBars}} bars before it can start calculating signals.',
                insufficientData
            )
            : translate(
                t,
                'common.strategy_errors.insufficient_data.description',
                'The selected date range does not contain enough bars for this strategy to initialize its indicators.'
            )

        return buildDescriptor({
            type: 'insufficient_data',
            title: translate(
                t,
                'common.strategy_errors.insufficient_data.title',
                'Not enough market data to run this strategy'
            ),
            description,
            suggestions: [
                translate(
                    t,
                    'common.strategy_errors.insufficient_data.suggestions.extend_range',
                    'Move the start date earlier so the strategy has enough warm-up data.'
                ),
                translate(
                    t,
                    'common.strategy_errors.insufficient_data.suggestions.reduce_periods',
                    'If the strategy supports it, reduce indicator periods such as MA, RSI, or KDJ parameters.'
                ),
            ],
            detail,
        })
    }

    if (/timed out/i.test(message)) {
        return buildDescriptor({
            type: 'timeout',
            title: translate(
                t,
                'common.strategy_errors.timeout.title',
                'The strategy took too long to finish'
            ),
            description: translate(
                t,
                'common.strategy_errors.timeout.description',
                'Try a smaller date range, a higher timeframe, or simplify the strategy logic before running again.'
            ),
            suggestions: [
                translate(
                    t,
                    'common.strategy_errors.timeout.suggestions.reduce_range',
                    'Reduce the amount of historical data in this run.'
                ),
                translate(
                    t,
                    'common.strategy_errors.timeout.suggestions.simplify',
                    'Check whether the strategy has expensive loops or repeated indicator calculations.'
                ),
            ],
            detail,
        })
    }

    if (/cancelled/i.test(message)) {
        return buildDescriptor({
            type: 'cancelled',
            title: translate(
                t,
                'common.strategy_errors.cancelled.title',
                'The strategy run was cancelled'
            ),
            description: translate(
                t,
                'common.strategy_errors.cancelled.description',
                'No result was generated. Start the task again when you are ready.'
            ),
            detail,
        })
    }

    if (
        /failed to load market data|no data returned|returned no data|symbol may be delisted|possibly delisted|failed download/i.test(message)
    ) {
        return buildDescriptor({
            type: 'market_data',
            title: translate(
                t,
                'common.strategy_errors.market_data.title',
                'Market data could not be loaded'
            ),
            description: translate(
                t,
                'common.strategy_errors.market_data.description',
                'Check the ticker symbol, date range, and data source availability, then try again.'
            ),
            suggestions: [
                translate(
                    t,
                    'common.strategy_errors.market_data.suggestions.check_ticker',
                    'Confirm the ticker symbol and timeframe are valid for the selected market.'
                ),
                translate(
                    t,
                    'common.strategy_errors.market_data.suggestions.adjust_dates',
                    'Use a date range where the asset has trading data.'
                ),
            ],
            detail,
        })
    }

    if (
        /userstrategy class not found|must inherit from backtrader\.strategy|strategy '.+' not found|failed to load strategy|strategy load/i.test(message)
    ) {
        return buildDescriptor({
            type: 'strategy_load',
            title: translate(
                t,
                'common.strategy_errors.strategy_load.title',
                'The strategy file could not be loaded'
            ),
            description: translate(
                t,
                'common.strategy_errors.strategy_load.description',
                'Check whether the strategy exists, whether the class is named UserStrategy, and whether the code can be compiled successfully.'
            ),
            suggestions: [
                translate(
                    t,
                    'common.strategy_errors.strategy_load.suggestions.class_name',
                    'Make sure the strategy defines a UserStrategy class.'
                ),
                translate(
                    t,
                    'common.strategy_errors.strategy_load.suggestions.syntax',
                    'Review the strategy code for syntax errors or unsupported imports.'
                ),
            ],
            detail,
        })
    }

    return buildDescriptor({
        type: 'generic',
        title: translate(
            t,
            'common.strategy_errors.generic.title',
            'Strategy execution failed'
        ),
        description: translate(
            t,
            'common.strategy_errors.generic.description',
            'The strategy could not be executed. Please review the parameters or strategy code and try again.'
        ),
        suggestions: [
            translate(
                t,
                'common.strategy_errors.generic.suggestions.check_params',
                'Review the selected symbol, timeframe, date range, and strategy parameters.'
            ),
            translate(
                t,
                'common.strategy_errors.generic.suggestions.check_code',
                'If the problem persists, inspect the strategy code or the task center details.'
            ),
        ],
        detail,
    })
}

export function shouldShowStrategyErrorDetail(errorDescriptor) {
    if (!errorDescriptor?.detail) {
        return false
    }

    return !['insufficient_data', 'cancelled'].includes(errorDescriptor.type)
}
