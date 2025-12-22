/**
 * Report API - generate, list, download, and share reports
 */
import { buildRequest, parseResponse } from './apiCore'

export const reportApi = {
    /**
     * Generate a new report (background task)
     */
    async generateReport(params) {
        const res = await buildRequest('/reports', {
            method: 'POST',
            body: JSON.stringify({
                report_type: params.report_type,
                source_ids: params.source_ids,
                title: params.title || null,
                description: params.description || null,
                config: params.config || null
            })
        })
        return await parseResponse(res)
    },

    /**
     * List reports with filtering and pagination
     */
    async listReports(params = {}) {
        const queryParams = new URLSearchParams()

        if (params.report_type) queryParams.append('report_type', params.report_type)
        if (params.status) queryParams.append('status', params.status)
        if (params.sort_by) queryParams.append('sort_by', params.sort_by)
        if (params.sort_order) queryParams.append('sort_order', params.sort_order)
        if (params.limit) queryParams.append('limit', params.limit.toString())
        if (params.offset) queryParams.append('offset', params.offset.toString())

        const url = `/reports${queryParams.toString() ? '?' + queryParams.toString() : ''}`
        const res = await buildRequest(url)
        return await parseResponse(res)
    },

    /**
     * Get report details by ID
     */
    async getReport(reportId) {
        const res = await buildRequest(`/reports/${reportId}`)
        return await parseResponse(res)
    },

    /**
     * Delete a report
     */
    async deleteReport(reportId) {
        const res = await buildRequest(`/reports/${reportId}`, {
            method: 'DELETE'
        })
        return await parseResponse(res)
    },

    /**
     * Download report as HTML file
     */
    async downloadReport(reportId) {
        const res = await buildRequest(`/reports/${reportId}/download`)
        if (!res.ok) {
            throw new Error(`Failed to download report: ${res.statusText}`)
        }

        // Get filename from Content-Disposition header if available
        const contentDisposition = res.headers.get('Content-Disposition')
        let filename = `report_${reportId}.html`
        if (contentDisposition) {
            const matches = /filename[^;=\n]*=((['"]).*?\2|[^;\n]*)/.exec(contentDisposition)
            if (matches != null && matches[1]) {
                filename = matches[1].replace(/['"]/g, '')
            }
        }

        const blob = await res.blob()
        const url = window.URL.createObjectURL(blob)
        const a = document.createElement('a')
        a.href = url
        a.download = filename
        document.body.appendChild(a)
        a.click()
        window.URL.revokeObjectURL(url)
        document.body.removeChild(a)
    },

    /**
     * Create a share link for a report
     */
    async createShareLink(reportId, expiresInHours = 168) {
        const res = await buildRequest(`/reports/${reportId}/share`, {
            method: 'POST',
            body: JSON.stringify({
                expires_in_hours: expiresInHours
            })
        })
        return await parseResponse(res)
    },

    /**
     * Revoke a report's share link
     */
    async revokeShareLink(reportId) {
        const res = await buildRequest(`/reports/${reportId}/share`, {
            method: 'DELETE'
        })
        return await parseResponse(res)
    },

    /**
     * Access a shared report by token (public, no auth)
     */
    async getSharedReport(shareToken) {
        const res = await buildRequest(`/reports/shared/${shareToken}`)
        if (!res.ok) {
            throw new Error(`Failed to access shared report: ${res.statusText}`)
        }
        return await res.text() // Returns HTML content
    }
}
