import { formatStrategyError, shouldShowStrategyErrorDetail } from './strategyErrorFormatter';

function parseJsonPayload(raw) {
    if (typeof raw !== 'string') {
        return null;
    }

    const trimmed = raw.trim();
    if (!trimmed.startsWith('{')) {
        return null;
    }

    try {
        const parsed = JSON.parse(trimmed);
        if (parsed && typeof parsed === 'object' && parsed.detail) {
            return parsed;
        }
    } catch {
        return null;
    }

    return null;
}

export function normalizeAppError(error) {
    if (!error) {
        return null;
    }

    if (error.payload && typeof error.payload === 'object') {
        return error.payload;
    }

    if (error.error && typeof error.error === 'object' && error.error.detail) {
        return error.error;
    }

    if (typeof error === 'object' && error.detail) {
        return error;
    }

    if (typeof error === 'object' && error.error_message) {
        return parseJsonPayload(error.error_message) || {
            detail: String(error.error_message),
            error_code: error.error_code || 'UNKNOWN_ERROR',
            request_id: error.request_id || null,
            details: error.details || null,
            retryable: Boolean(error.retryable),
        };
    }

    if (error instanceof Error) {
        return {
            detail: error.message,
            error_code: error.error_code || 'UNKNOWN_ERROR',
            request_id: error.request_id || null,
            details: error.details || null,
            retryable: Boolean(error.retryable),
        };
    }

    const parsed = parseJsonPayload(error);
    if (parsed) {
        return parsed;
    }

    return {
        detail: String(error),
        error_code: 'UNKNOWN_ERROR',
        request_id: null,
        details: null,
        retryable: false,
    };
}

export function formatAppError(error, t) {
    const normalized = normalizeAppError(error);
    const strategyFormatted = formatStrategyError(normalized?.detail || error, t);

    return {
        ...strategyFormatted,
        errorCode: normalized?.error_code || null,
        requestId: normalized?.request_id || null,
        retryable: Boolean(normalized?.retryable),
        details: normalized?.details || null,
        showTechnicalDetail: shouldShowStrategyErrorDetail(strategyFormatted),
    };
}

