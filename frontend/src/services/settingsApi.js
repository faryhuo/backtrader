/**
 * Settings and Credentials API
 */
import { buildRequest, parseResponse } from './apiCore'

export const settingsApi = {
    // Settings

    async getSettings() {
        const res = await buildRequest('/settings')
        return await parseResponse(res)
    },

    async updateSettings(settings) {
        const res = await buildRequest('/settings', {
            method: 'PUT',
            body: JSON.stringify(settings)
        })
        return await parseResponse(res)
    },

    async resetSettings() {
        const res = await buildRequest('/settings/reset', {
            method: 'POST'
        })
        return await parseResponse(res)
    },

    // Credentials

    async getCredentials() {
        const res = await buildRequest('/settings/credentials')
        return await parseResponse(res)
    },

    async updateCredentials(credentials) {
        const res = await buildRequest('/settings/credentials', {
            method: 'PUT',
            body: JSON.stringify(credentials)
        })
        return await parseResponse(res)
    },

    async updateCCXTCredentials(exchange, mode, credentials) {
        const res = await buildRequest('/settings/credentials/ccxt', {
            method: 'PUT',
            body: JSON.stringify({ exchange, mode, ...credentials })
        })
        return await parseResponse(res)
    },

    async resetCredential(credentialKey) {
        const res = await buildRequest(`/settings/credentials/${credentialKey}`, {
            method: 'DELETE'
        })
        return await parseResponse(res)
    },

    async testCredential(credentialType, params) {
        const res = await buildRequest('/settings/credentials/test', {
            method: 'POST',
            body: JSON.stringify({ credential_type: credentialType, ...params })
        })
        return await parseResponse(res)
    },

    // Data Source Settings

    async getDataSourceSettings() {
        const res = await buildRequest('/settings/data-source')
        return await parseResponse(res)
    },

    async updateDataSourceSettings(settings) {
        const res = await buildRequest('/settings/data-source', {
            method: 'PUT',
            body: JSON.stringify(settings)
        })
        return await parseResponse(res)
    },

    async resetDataSourceSettings() {
        const res = await buildRequest('/settings/data-source/reset', {
            method: 'POST'
        })
        return await parseResponse(res)
    }
}

