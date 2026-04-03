/**
 * Market Data API - ticker info, prices, cache management, and resampling
 */
import { buildRequest, parseResponse } from './apiCore'

export const marketDataApi = {
    async fetchMarketData(params) {
        // Call both APIs in parallel
        const [tickerInfo, pricesData] = await Promise.all([
            this.getTickerInfo(params.ticker),
            this.getTickerPrices(params.ticker, params.start_date, params.end_date)
        ]);

        return {
            ticker_info: tickerInfo,
            data: pricesData.data
        };
    },

    async getTickerInfo(ticker) {
        const res = await buildRequest(`/ticker/${encodeURIComponent(ticker)}/info`);
        return await parseResponse(res);
    },

    async getTickerPrices(ticker, startDate, endDate) {
        const params = new URLSearchParams({
            start_date: startDate,
            end_date: endDate
        });
        const res = await buildRequest(`/ticker/${encodeURIComponent(ticker)}/prices?${params}`);
        return await parseResponse(res);
    },

    async getInstrumentCatalog({ platform = 'yahoo', instrumentType = 'all', query = '', limit = 20 } = {}) {
        const params = new URLSearchParams({
            platform,
            instrument_type: instrumentType,
            query,
            limit: String(limit)
        });
        const res = await buildRequest(`/instruments/catalog?${params}`);
        return await parseResponse(res);
    },

    // ========== Cache Management APIs ==========

    async getCacheStats() {
        const res = await buildRequest('/cache/stats');
        return await parseResponse(res);
    },

    async getCachedTickers() {
        const res = await buildRequest('/cache/tickers');
        return await parseResponse(res);
    },

    async getTickerCacheInfo(ticker) {
        const res = await buildRequest(`/cache/${encodeURIComponent(ticker)}`);
        return await parseResponse(res);
    },

    async warmupCache(params) {
        const res = await buildRequest('/cache/warmup', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify(params)
        });
        return await parseResponse(res);
    },

    async cleanupCache(params) {
        const searchParams = new URLSearchParams();
        if (params.before_date) searchParams.set('before_date', params.before_date);
        if (params.tickers) searchParams.set('tickers', params.tickers);
        if (params.older_than_days) searchParams.set('older_than_days', params.older_than_days);

        const res = await buildRequest(`/cache/cleanup?${searchParams}`, {
            method: 'DELETE'
        });
        return await parseResponse(res);
    },

    async deleteTickerCache(ticker) {
        const res = await buildRequest(`/cache/${encodeURIComponent(ticker)}`, {
            method: 'DELETE'
        });
        return await parseResponse(res);
    },

    // ========== Resample APIs ==========

    async getSupportedTimeframes() {
        const res = await buildRequest('/resample/timeframes');
        return await parseResponse(res);
    },

    async getResampleTargets(sourceTimeframe) {
        const res = await buildRequest(`/resample/targets/${encodeURIComponent(sourceTimeframe)}`);
        return await parseResponse(res);
    },

    async resampleData(params) {
        const res = await buildRequest('/resample', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify(params)
        });
        return await parseResponse(res);
    }
}

