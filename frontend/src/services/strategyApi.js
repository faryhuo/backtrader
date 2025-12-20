/**
 * Strategy API - strategy CRUD, versions, templates, and params
 */
import { buildRequest, parseResponse } from './apiCore'

export const strategyApi = {
    async getStrategies() {
        const res = await buildRequest('/strategies')
        const data = await parseResponse(res)
        return data?.strategies || []
    },

    async getStrategy(name) {
        if (!name) return null
        const res = await buildRequest(`/strategy?name=${encodeURIComponent(name)}`)
        return await parseResponse(res)
    },

    async saveStrategy(name, code, commitMessage = null) {
        const res = await buildRequest('/strategy', {
            method: 'POST',
            body: JSON.stringify({ name, code, commit_message: commitMessage })
        })
        return await parseResponse(res)
    },

    // Strategy Version Management

    async getStrategyVersions(name, limit = 50, offset = 0) {
        const params = new URLSearchParams({
            limit: limit.toString(),
            offset: offset.toString()
        });
        const res = await buildRequest(`/strategy/${encodeURIComponent(name)}/versions?${params}`)
        return await parseResponse(res)
    },

    async getStrategyVersion(name, versionNumber) {
        const res = await buildRequest(`/strategy/${encodeURIComponent(name)}/versions/${versionNumber}`)
        return await parseResponse(res)
    },

    async getLatestStrategyVersion(name) {
        const res = await buildRequest(`/strategy/${encodeURIComponent(name)}/versions/latest`)
        return await parseResponse(res)
    },

    async compareVersions(name, fromVersion, toVersion) {
        const params = new URLSearchParams({
            from_version: fromVersion.toString(),
            to_version: toVersion.toString()
        });
        const res = await buildRequest(`/strategy/${encodeURIComponent(name)}/versions/compare?${params}`)
        return await parseResponse(res)
    },

    async rollbackVersion(name, versionNumber, commitMessage = null) {
        const res = await buildRequest(`/strategy/${encodeURIComponent(name)}/versions/${versionNumber}/rollback`, {
            method: 'POST',
            body: JSON.stringify({ commit_message: commitMessage })
        })
        return await parseResponse(res)
    },

    // Strategy Templates

    async getTemplates() {
        const res = await buildRequest('/templates')
        return await parseResponse(res)
    },

    async getTemplateDetail(templateId) {
        const res = await buildRequest(`/templates/${encodeURIComponent(templateId)}`)
        return await parseResponse(res)
    },

    async importTemplate(templateId, name) {
        const res = await buildRequest('/templates/import', {
            method: 'POST',
            body: JSON.stringify({ template_id: templateId, name })
        })
        return await parseResponse(res)
    },

    // Strategy Params

    async getStrategyParams(name) {
        try {
            const res = await buildRequest(`/strategy/${encodeURIComponent(name)}/params`)
            return await parseResponse(res)
        } catch (error) {
            // Return empty params on error, don't throw
            console.warn(`Failed to get strategy params for ${name}:`, error)
            return { name, params: [] }
        }
    }
}
