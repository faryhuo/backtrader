import { buildRequest, parseResponse } from './apiCore'

export const setupApi = {
    async getSetupWizard() {
        const res = await buildRequest('/setup/wizard')
        return await parseResponse(res)
    },

    async saveSetupWizard(config) {
        const res = await buildRequest('/setup/wizard', {
            method: 'PUT',
            body: JSON.stringify({ config })
        })
        return await parseResponse(res)
    },

    async testSetupWizard(type, payload) {
        const res = await buildRequest('/setup/wizard/test', {
            method: 'POST',
            body: JSON.stringify({ type, payload })
        })
        return await parseResponse(res)
    }
}
