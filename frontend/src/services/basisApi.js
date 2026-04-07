import { buildRequest, parseResponse } from './apiCore';

const OKX_BASE_URL = 'https://www.okx.com/api/v5';

async function fetchOkx(path) {
    const response = await fetch(`${OKX_BASE_URL}${path}`);
    if (!response.ok) {
        throw new Error(`OKX request failed: ${response.status}`);
    }

    const payload = await response.json();
    if (payload?.code !== '0') {
        throw new Error(payload?.msg || 'OKX request failed');
    }

    return payload?.data?.[0] || null;
}

export async function getBasisSnapshot(symbol = 'ETH') {
    const normalizedSymbol = String(symbol || 'ETH').toUpperCase();
    const spotInstId = `${normalizedSymbol}-USDT`;
    const swapInstId = `${normalizedSymbol}-USDT-SWAP`;

    const [funding, swapTicker, spotTicker] = await Promise.all([
        fetchOkx(`/public/funding-rate?instId=${swapInstId}`),
        fetchOkx(`/market/ticker?instId=${swapInstId}`),
        fetchOkx(`/market/ticker?instId=${spotInstId}`),
    ]);

    const fundingRate = Number(funding?.fundingRate || 0);
    const swapPrice = Number(swapTicker?.last || 0);
    const spotPrice = Number(spotTicker?.last || 0);
    const basis = swapPrice - spotPrice;

    return {
        symbol: normalizedSymbol,
        instId: swapInstId,
        fundingRate,
        swapPrice,
        spotPrice,
        basis,
        basisPercent: spotPrice > 0 ? basis / spotPrice : 0,
        fundingTime: Number(funding?.fundingTime || 0),
        nextFundingTime: Number(funding?.nextFundingTime || 0),
        ts: Number(funding?.ts || Date.now()),
    };
}

export const basisApi = {
    getBasisSnapshot,
    async getCredentialStatus(exchange) {
        const params = new URLSearchParams({ exchange });
        const response = await buildRequest(`/basis/credentials-status?${params.toString()}`);
        return await parseResponse(response);
    },
    async previewTrade(payload) {
        const response = await buildRequest('/basis/preview', {
            method: 'POST',
            body: JSON.stringify(payload),
        });
        return await parseResponse(response);
    },
    async getTradePrecheck(payload) {
        const response = await buildRequest('/basis/precheck', {
            method: 'POST',
            body: JSON.stringify(payload),
        });
        return await parseResponse(response);
    },
    async openTrade(payload) {
        const response = await buildRequest('/basis/trade/open', {
            method: 'POST',
            body: JSON.stringify(payload),
        });
        return await parseResponse(response);
    },
    async closeTrade(payload) {
        const response = await buildRequest('/basis/trade/close', {
            method: 'POST',
            body: JSON.stringify(payload),
        });
        return await parseResponse(response);
    },
    async getTradeState(exchange, mode, symbol) {
        const params = new URLSearchParams({ exchange, mode, symbol });
        const response = await buildRequest(`/basis/trade/state?${params.toString()}`);
        return await parseResponse(response);
    },
};
