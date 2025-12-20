/**
 * Task API Service - Client for task management endpoints.
 *
 * Provides methods for:
 * - Listing tasks with filtering and pagination
 * - Getting task details
 * - Cancelling tasks
 * - Retrying failed tasks
 * - Deleting task records
 */

import { buildRequest, parseResponse } from './apiCore';

/**
 * Task types enum
 */
export const TaskType = {
    BACKTEST: 'backtest',
    PORTFOLIO: 'portfolio',
    WALKFORWARD: 'walkforward',
    DEEP_ANALYSIS: 'deep_analysis',
};

/**
 * Task status enum
 */
export const TaskStatus = {
    PENDING: 'pending',
    RUNNING: 'running',
    COMPLETED: 'completed',
    FAILED: 'failed',
    CANCELLED: 'cancelled',
};

/**
 * Get display label for task type
 * @param {string} type - Task type value
 * @param {function} t - i18n translation function
 * @returns {string} Display label
 */
export function getTaskTypeLabel(type, t) {
    const labels = {
        [TaskType.BACKTEST]: t('taskCenter.type.backtest', 'Backtest'),
        [TaskType.PORTFOLIO]: t('taskCenter.type.portfolio', 'Portfolio'),
        [TaskType.WALKFORWARD]: t('taskCenter.type.walkforward', 'Walk-Forward'),
        [TaskType.DEEP_ANALYSIS]: t('taskCenter.type.deepAnalysis', 'Deep Analysis'),
    };
    return labels[type] || type;
}

/**
 * Get display label for task status
 * @param {string} status - Task status value
 * @param {function} t - i18n translation function
 * @returns {string} Display label
 */
export function getTaskStatusLabel(status, t) {
    const labels = {
        [TaskStatus.PENDING]: t('taskCenter.status.pending', 'Pending'),
        [TaskStatus.RUNNING]: t('taskCenter.status.running', 'Running'),
        [TaskStatus.COMPLETED]: t('taskCenter.status.completed', 'Completed'),
        [TaskStatus.FAILED]: t('taskCenter.status.failed', 'Failed'),
        [TaskStatus.CANCELLED]: t('taskCenter.status.cancelled', 'Cancelled'),
    };
    return labels[status] || status;
}

export const taskApi = {
    /**
     * List tasks with optional filtering.
     *
     * @param {Object} params - Query parameters
     * @param {string} params.task_type - Filter by type
     * @param {string} params.status - Filter by status
     * @param {number} params.limit - Maximum results (default: 50)
     * @param {number} params.offset - Pagination offset
     * @returns {Promise<{tasks: Array, total: number}>}
     */
    async listTasks(params = {}) {
        const queryParams = new URLSearchParams();
        if (params.task_type) queryParams.append('task_type', params.task_type);
        if (params.status) queryParams.append('status', params.status);
        if (params.limit) queryParams.append('limit', String(params.limit));
        if (params.offset) queryParams.append('offset', String(params.offset));
        if (params.sort_by) queryParams.append('sort_by', params.sort_by);
        if (params.sort_order) queryParams.append('sort_order', params.sort_order);

        const query = queryParams.toString();
        const res = await buildRequest(`/tasks${query ? `?${query}` : ''}`);
        return await parseResponse(res);
    },

    /**
     * Get task details by ID.
     *
     * @param {string} taskId - Task identifier
     * @returns {Promise<Object>} Task object with full details
     */
    async getTask(taskId) {
        const res = await buildRequest(`/tasks/${taskId}`);
        return await parseResponse(res);
    },

    /**
     * Get task manager statistics.
     *
     * @returns {Promise<Object>} Stats object with running_count, pending_count, etc.
     */
    async getTaskStats() {
        const res = await buildRequest('/tasks/stats');
        return await parseResponse(res);
    },

    /**
     * Cancel a pending or running task.
     *
     * @param {string} taskId - Task identifier
     * @returns {Promise<{message: string, task_id: string}>}
     */
    async cancelTask(taskId) {
        const res = await buildRequest(`/tasks/${taskId}/cancel`, {
            method: 'POST',
        });
        return await parseResponse(res);
    },

    /**
     * Retry a failed or cancelled task.
     *
     * @param {string} taskId - Original task identifier
     * @returns {Promise<Object>} New task object
     */
    async retryTask(taskId) {
        const res = await buildRequest(`/tasks/${taskId}/retry`, {
            method: 'POST',
        });
        return await parseResponse(res);
    },

    /**
     * Delete a task record.
     *
     * @param {string} taskId - Task identifier
     * @param {boolean} force - Force delete even running tasks (default: false)
     * @returns {Promise<{message: string, task_id: string}>}
     */
    async deleteTask(taskId, force = false) {
        const queryParams = force ? '?force=true' : '';
        const res = await buildRequest(`/tasks/${taskId}${queryParams}`, {
            method: 'DELETE',
        });
        return await parseResponse(res);
    },
};

// Export individual functions for convenience
export const {
    listTasks,
    getTask,
    getTaskStats,
    cancelTask,
    retryTask,
    deleteTask,
} = taskApi;

export default taskApi;
