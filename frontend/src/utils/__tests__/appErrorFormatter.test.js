import { describe, expect, it } from 'vitest';

import { formatAppError, normalizeAppError } from '../appErrorFormatter';

describe('appErrorFormatter', () => {
    const mockT = (key, fallbackOrOptions) => {
        if (typeof fallbackOrOptions === 'string') {
            return fallbackOrOptions;
        }

        return fallbackOrOptions?.defaultValue || key;
    };

    it('normalizes structured JSON strings from persisted task/report errors', () => {
        const payload = normalizeAppError(JSON.stringify({
            detail: 'Service temporarily unavailable',
            error_code: 'SERVICE_UNAVAILABLE',
            request_id: 'req-123',
            retryable: true,
        }));

        expect(payload).toMatchObject({
            detail: 'Service temporarily unavailable',
            error_code: 'SERVICE_UNAVAILABLE',
            request_id: 'req-123',
            retryable: true,
        });
    });

    it('formats structured errors while preserving metadata', () => {
        const formatted = formatAppError({
            detail: 'Backtest failed: division by zero',
            error_code: 'INTERNAL_ERROR',
            request_id: 'req-456',
            retryable: false,
        }, mockT);

        expect(formatted.title).toBe('Strategy execution failed');
        expect(formatted.requestId).toBe('req-456');
        expect(formatted.retryable).toBe(false);
        expect(formatted.detail).toBe('Backtest failed: division by zero');
    });
});

