/**
 * Market Data API - ticker info and prices
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
    }
}
