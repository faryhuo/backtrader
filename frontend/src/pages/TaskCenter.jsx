/**
 * TaskCenter Page - Unified background task management.
 *
 * Features:
 * - List all background tasks with filters
 * - Real-time status updates via WebSocket
 * - Cancel, retry, and delete tasks
 * - Navigate to task results
 */

import { useState, useEffect, useCallback } from 'react';
import { useNavigate } from 'react-router-dom';
import { useTranslation } from 'react-i18next';
import './TaskCenter.css';

import {
    listTasks,
    getTaskStats,
    cancelTask,
    retryTask,
    deleteTask,
    TaskType,
    TaskStatus,
    getTaskTypeLabel,
    getTaskStatusLabel,
} from '../services/taskApi';
import { useTaskWebSocket, TASK_EVENT_TYPES } from '../hooks/useTaskWebSocket';

function TaskCenter() {
    const { t } = useTranslation();
    const navigate = useNavigate();

    // State
    const [tasks, setTasks] = useState([]);
    const [total, setTotal] = useState(0);
    const [loading, setLoading] = useState(true);
    const [stats, setStats] = useState(null);
    const [error, setError] = useState(null);

    // Filters
    const [filters, setFilters] = useState({
        task_type: '',
        status: '',
        limit: 50,
        offset: 0,
    });

    // WebSocket for real-time updates
    const { isConnected } = useTaskWebSocket({
        onTaskUpdate: useCallback((message) => {
            const { type, task_id, data } = message;

            setTasks(prevTasks => {
                // Find and update the task
                const taskIndex = prevTasks.findIndex(t => t.task_id === task_id);

                if (taskIndex >= 0) {
                    const updatedTasks = [...prevTasks];
                    updatedTasks[taskIndex] = {
                        ...updatedTasks[taskIndex],
                        ...data,
                    };
                    return updatedTasks;
                } else if (type === TASK_EVENT_TYPES.CREATED) {
                    // Add new task at the beginning
                    return [data, ...prevTasks];
                }
                return prevTasks;
            });

            // Refresh stats on task changes
            if ([TASK_EVENT_TYPES.CREATED, TASK_EVENT_TYPES.COMPLETED, TASK_EVENT_TYPES.FAILED, TASK_EVENT_TYPES.CANCELLED].includes(type)) {
                fetchStats();
            }
        }, []),
    });

    // Fetch tasks
    const fetchTasks = useCallback(async () => {
        try {
            setLoading(true);
            const result = await listTasks({
                ...filters,
                task_type: filters.task_type || undefined,
                status: filters.status || undefined,
            });
            setTasks(result.tasks || []);
            setTotal(result.total || 0);
            setError(null);
        } catch (err) {
            setError(err.message);
        } finally {
            setLoading(false);
        }
    }, [filters]);

    // Fetch stats
    const fetchStats = useCallback(async () => {
        try {
            const result = await getTaskStats();
            setStats(result);
        } catch (err) {
            console.error('Failed to fetch stats:', err);
        }
    }, []);

    // Initial load
    useEffect(() => {
        fetchTasks();
        fetchStats();
    }, [fetchTasks, fetchStats]);

    // Handle filter change
    const handleFilterChange = (key, value) => {
        setFilters(prev => ({
            ...prev,
            [key]: value,
            offset: 0, // Reset pagination
        }));
    };

    // Handle cancel task
    const handleCancel = async (taskId) => {
        try {
            await cancelTask(taskId);
            fetchTasks();
            fetchStats();
        } catch (err) {
            // If cancel fails, offer to delete the task record
            const shouldDelete = confirm(
                t('taskCenter.cancelFailedDelete',
                    `Failed to cancel task: ${err.message}\n\nDo you want to delete this task record instead?`)
            );
            if (shouldDelete) {
                try {
                    await deleteTask(taskId, true);  // force=true for stuck running tasks
                    fetchTasks();
                    fetchStats();
                } catch (deleteErr) {
                    alert(`Failed to delete task: ${deleteErr.message}`);
                }
            }
        }
    };

    // Handle retry task
    const handleRetry = async (taskId) => {
        try {
            await retryTask(taskId);
            fetchTasks();
            fetchStats();
        } catch (err) {
            alert(`Failed to retry task: ${err.message}`);
        }
    };

    // Handle delete task
    const handleDelete = async (taskId) => {
        if (!confirm(t('taskCenter.confirmDelete', 'Are you sure you want to delete this task?'))) {
            return;
        }
        try {
            await deleteTask(taskId);
            fetchTasks();
            fetchStats();
        } catch (err) {
            alert(`Failed to delete task: ${err.message}`);
        }
    };

    // Navigate to result
    const handleViewResult = (task) => {
        if (!task.result_id) return;

        switch (task.task_type) {
            case TaskType.BACKTEST:
            case TaskType.DEEP_ANALYSIS:
                navigate(`/history`);
                break;
            case TaskType.PORTFOLIO:
                navigate(`/history`);
                break;
            case TaskType.WALKFORWARD:
                navigate(`/walkforward`);
                break;
            default:
                break;
        }
    };

    // Format duration
    const formatDuration = (seconds) => {
        if (!seconds) return '-';
        if (seconds < 60) return `${Math.round(seconds)}s`;
        if (seconds < 3600) return `${Math.round(seconds / 60)}m`;
        return `${Math.round(seconds / 3600)}h`;
    };

    // Format date
    const formatDate = (isoString) => {
        if (!isoString) return '-';
        return new Date(isoString).toLocaleString();
    };

    return (
        <div className="task-center">
            {/* Header */}
            <div className="task-center-header">
                <h1>{t('taskCenter.title', 'Task Center')}</h1>

                <div className="task-stats">
                    <div className="task-stat">
                        <span className="stat-label">{t('taskCenter.running', 'Running')}</span>
                        <span className="stat-value running">
                            {tasks.filter(task => task.status === TaskStatus.RUNNING).length}
                        </span>
                    </div>
                    <div className="task-stat">
                        <span className="stat-label">{t('taskCenter.failed', 'Failed')}</span>
                        <span className="stat-value failed">
                            {tasks.filter(task => task.status === TaskStatus.FAILED).length}
                        </span>
                    </div>
                    <div className="task-stat">
                        <span className="stat-label">{t('taskCenter.total', 'Total')}</span>
                        <span className="stat-value">{total || 0}</span>
                    </div>
                    <div className="task-stat">
                        <span className="stat-label">{t('taskCenter.maxConcurrent', 'Max Concurrent')}</span>
                        <span className="stat-value">{stats?.max_concurrent || 3}</span>
                    </div>
                    <div className="connection-status">
                        <span className={`connection-dot ${isConnected ? 'connected' : 'disconnected'}`} />
                        <span>{isConnected ? t('taskCenter.connected', 'Live') : t('taskCenter.disconnected', 'Offline')}</span>
                    </div>
                </div>
            </div>

            {/* Filters */}
            <div className="task-filters">
                <div className="task-filter">
                    <label>{t('taskCenter.filterType', 'Type')}</label>
                    <select
                        value={filters.task_type}
                        onChange={(e) => handleFilterChange('task_type', e.target.value)}
                    >
                        <option value="">{t('taskCenter.allTypes', 'All Types')}</option>
                        <option value={TaskType.BACKTEST}>{getTaskTypeLabel(TaskType.BACKTEST, t)}</option>
                        <option value={TaskType.PORTFOLIO}>{getTaskTypeLabel(TaskType.PORTFOLIO, t)}</option>
                        <option value={TaskType.WALKFORWARD}>{getTaskTypeLabel(TaskType.WALKFORWARD, t)}</option>
                        <option value={TaskType.DEEP_ANALYSIS}>{getTaskTypeLabel(TaskType.DEEP_ANALYSIS, t)}</option>
                    </select>
                </div>

                <div className="task-filter">
                    <label>{t('taskCenter.filterStatus', 'Status')}</label>
                    <select
                        value={filters.status}
                        onChange={(e) => handleFilterChange('status', e.target.value)}
                    >
                        <option value="">{t('taskCenter.allStatus', 'All Status')}</option>
                        <option value={TaskStatus.PENDING}>{getTaskStatusLabel(TaskStatus.PENDING, t)}</option>
                        <option value={TaskStatus.RUNNING}>{getTaskStatusLabel(TaskStatus.RUNNING, t)}</option>
                        <option value={TaskStatus.COMPLETED}>{getTaskStatusLabel(TaskStatus.COMPLETED, t)}</option>
                        <option value={TaskStatus.FAILED}>{getTaskStatusLabel(TaskStatus.FAILED, t)}</option>
                        <option value={TaskStatus.CANCELLED}>{getTaskStatusLabel(TaskStatus.CANCELLED, t)}</option>
                    </select>
                </div>
            </div>

            {/* Error */}
            {error && (
                <div className="task-error" style={{ color: 'red', marginBottom: '1rem' }}>
                    {error}
                </div>
            )}

            {/* Task Table */}
            <div className="task-table-container">
                {loading ? (
                    <div className="task-loading">
                        {t('common.loading', 'Loading...')}
                    </div>
                ) : tasks.length === 0 ? (
                    <div className="task-empty">
                        <div className="task-empty-icon">📋</div>
                        <h3>{t('taskCenter.noTasks', 'No Tasks')}</h3>
                        <p>{t('taskCenter.noTasksDesc', 'Run a backtest or optimization to see tasks here.')}</p>
                    </div>
                ) : (
                    <table className="task-table">
                        <thead>
                            <tr>
                                <th>{t('taskCenter.colName', 'Task')}</th>
                                <th>{t('taskCenter.colType', 'Type')}</th>
                                <th>{t('taskCenter.colStatus', 'Status')}</th>
                                <th>{t('taskCenter.colProgress', 'Progress')}</th>
                                <th>{t('taskCenter.colDuration', 'Duration')}</th>
                                <th>{t('taskCenter.colCreated', 'Created')}</th>
                                <th>{t('taskCenter.colUser', 'User')}</th>
                                <th>{t('taskCenter.colActions', 'Actions')}</th>
                            </tr>
                        </thead>
                        <tbody>
                            {tasks.map(task => (
                                <tr key={task.task_id}>
                                    <td>
                                        <div className="task-name">{task.name || 'Unnamed Task'}</div>
                                        <div className="task-id">{task.task_id.substring(0, 8)}...</div>
                                    </td>
                                    <td>
                                        <span className={`task-type-badge ${task.task_type}`}>
                                            {getTaskTypeLabel(task.task_type, t)}
                                        </span>
                                    </td>
                                    <td>
                                        <span className={`task-status-badge ${task.status}`}>
                                            <span className={`status-dot ${task.status}`} />
                                            {getTaskStatusLabel(task.status, t)}
                                        </span>
                                        {task.error_message && (
                                            <div className="task-error-message" title={task.error_message}>
                                                {task.error_message}
                                            </div>
                                        )}
                                    </td>
                                    <td>
                                        <div className="task-progress">
                                            <div className="progress-bar">
                                                <div
                                                    className="progress-fill"
                                                    style={{ width: `${task.progress || 0}%` }}
                                                />
                                            </div>
                                            <span className="progress-text">{task.progress || 0}%</span>
                                        </div>
                                    </td>
                                    <td className="task-duration">
                                        {formatDuration(task.duration_seconds)}
                                    </td>
                                    <td>
                                        {formatDate(task.created_at)}
                                    </td>
                                    <td className="task-user">
                                        {task.user_id ? task.user_id.substring(0, 8) + '...' : '-'}
                                    </td>
                                    <td>
                                        <div className="task-actions">
                                            {/* Cancel button - only for pending/running */}
                                            {(task.status === TaskStatus.PENDING || task.status === TaskStatus.RUNNING) && (
                                                <button
                                                    className="task-action-btn cancel"
                                                    onClick={() => handleCancel(task.task_id)}
                                                >
                                                    {t('taskCenter.cancel', 'Cancel')}
                                                </button>
                                            )}

                                            {/* Retry button - only for failed/cancelled */}
                                            {(task.status === TaskStatus.FAILED || task.status === TaskStatus.CANCELLED) && (
                                                <button
                                                    className="task-action-btn retry"
                                                    onClick={() => handleRetry(task.task_id)}
                                                >
                                                    {t('taskCenter.retry', 'Retry')}
                                                </button>
                                            )}

                                            {/* View result button - only for completed with result_id */}
                                            {task.status === TaskStatus.COMPLETED && task.result_id && (
                                                <button
                                                    className="task-action-btn view"
                                                    onClick={() => handleViewResult(task)}
                                                >
                                                    {t('taskCenter.viewResult', 'View')}
                                                </button>
                                            )}

                                            {/* Delete button - not for running */}
                                            {task.status !== TaskStatus.RUNNING && (
                                                <button
                                                    className="task-action-btn delete"
                                                    onClick={() => handleDelete(task.task_id)}
                                                >
                                                    {t('taskCenter.delete', 'Delete')}
                                                </button>
                                            )}
                                        </div>
                                    </td>
                                </tr>
                            ))}
                        </tbody>
                    </table>
                )}
            </div>

            {/* Total count */}
            {!loading && tasks.length > 0 && (
                <div style={{ marginTop: '1rem', color: 'var(--text-secondary)', fontSize: '0.875rem' }}>
                    {t('taskCenter.showingTasks', 'Showing {{count}} of {{total}} tasks', {
                        count: tasks.length,
                        total: total,
                    })}
                </div>
            )}
        </div>
    );
}

export default TaskCenter;
