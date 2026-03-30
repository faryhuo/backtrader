import { useEffect, useMemo, useState } from 'react';
import PropTypes from 'prop-types';
import { Alert, Empty, Segmented, Spin } from 'antd';
import { useTranslation } from 'react-i18next';
import { taskApi, TaskType } from '../../services/taskApi';

const LOG_LEVEL_CLASS_MAP = {
    info: 'info',
    warning: 'warning',
    error: 'error',
};

function formatTimestamp(timestamp) {
    if (!timestamp) return '--';

    const date = new Date(timestamp);
    if (Number.isNaN(date.getTime())) {
        return String(timestamp);
    }

    const pad = (value) => String(value).padStart(2, '0');

    return `${date.getFullYear()}-${pad(date.getMonth() + 1)}-${pad(date.getDate())} ${pad(date.getHours())}:${pad(date.getMinutes())}:${pad(date.getSeconds())}`;
}

function normalizeLogs(logs) {
    if (!Array.isArray(logs)) return [];
    return logs.filter((item) => item && item.message);
}

function TaskExecutionLog({ backtestId, logs: externalLogs = [] }) {
    const { t } = useTranslation();
    const [logs, setLogs] = useState([]);
    const [loading, setLoading] = useState(false);
    const [error, setError] = useState('');
    const [filterMode, setFilterMode] = useState('all');
    const normalizedExternalLogs = useMemo(() => normalizeLogs(externalLogs), [externalLogs]);

    useEffect(() => {
        let active = true;

        async function loadLogs() {
            if (normalizedExternalLogs.length > 0) {
                setLogs(normalizedExternalLogs);
                setError('');
                setLoading(false);
                return;
            }

            if (!backtestId) {
                setLogs([]);
                setError('');
                return;
            }

            setLoading(true);
            setError('');

            try {
                const pageSize = 200;
                let offset = 0;
                let matchedTask = null;
                let total = 0;

                do {
                    const result = await taskApi.listTasks({
                        task_type: TaskType.BACKTEST,
                        limit: pageSize,
                        offset,
                    });

                    if (!active) return;

                    total = result.total || 0;
                    matchedTask = (result.tasks || []).find((task) => task.result_id === backtestId);
                    offset += pageSize;
                } while (!matchedTask && offset < total);

                if (!active) return;

                setLogs(normalizeLogs(matchedTask?.logs));
            } catch (err) {
                if (!active) return;
                setError(err?.message || t('history.task_logs_load_failed', 'Failed to load task logs.'));
                setLogs([]);
            } finally {
                if (active) {
                    setLoading(false);
                }
            }
        }

        loadLogs();

        return () => {
            active = false;
        };
    }, [backtestId, normalizedExternalLogs, t]);

    const filteredLogs = useMemo(() => {
        if (filterMode === 'error') {
            return logs.filter((item) => String(item.level || '').toLowerCase() === 'error');
        }
        return logs;
    }, [filterMode, logs]);

    const hasErrorLogs = logs.some((item) => String(item.level || '').toLowerCase() === 'error');

    if (loading) {
        return (
            <div className="strategy-task-log-loading">
                <Spin size="large" />
            </div>
        );
    }

    return (
        <section className="strategy-task-log-card">
            <div className="strategy-task-log-toolbar">
                <div className="strategy-task-log-title-group">
                    <h3 className="strategy-task-log-title">
                        {t('history.task_logs_title', 'Execution Logs')}
                    </h3>
                    <span className="strategy-task-log-subtitle">
                        {t('history.task_logs_subtitle', 'Task lifecycle and runtime messages for this backtest')}
                    </span>
                </div>
                <Segmented
                    size="small"
                    value={filterMode}
                    onChange={setFilterMode}
                    options={[
                        { value: 'all', label: t('history.task_logs_all', 'Log Output') },
                        { value: 'error', label: t('history.task_logs_errors', 'Error Logs') },
                    ]}
                />
            </div>

            {error ? (
                <Alert
                    type="warning"
                    showIcon
                    message={t('history.task_logs_load_failed', 'Failed to load task logs.')}
                    description={error}
                    className="strategy-task-log-alert"
                />
            ) : null}

            <div className="strategy-task-log-console custom-scrollbar">
                {filteredLogs.length > 0 ? (
                    filteredLogs.map((item, index) => {
                        const level = String(item.level || 'info').toLowerCase();
                        const levelClass = LOG_LEVEL_CLASS_MAP[level] || 'info';

                        return (
                            <div
                                key={`${item.timestamp || 'log'}-${index}`}
                                className={`strategy-task-log-line ${levelClass}`}
                            >
                                <span className="strategy-task-log-time">{formatTimestamp(item.timestamp)}</span>
                                <span className={`strategy-task-log-level ${levelClass}`}>{level.toUpperCase()}</span>
                                <span className="strategy-task-log-message">{item.message}</span>
                            </div>
                        );
                    })
                ) : (
                    <div className="strategy-task-log-empty">
                        <Empty
                            image={Empty.PRESENTED_IMAGE_SIMPLE}
                            description={
                                filterMode === 'error'
                                    ? t('history.task_logs_no_errors', 'No error logs for this backtest.')
                                    : t('history.task_logs_empty', 'No task logs are available for this backtest.')
                            }
                        />
                    </div>
                )}
            </div>

            {filterMode === 'all' && hasErrorLogs ? (
                <div className="strategy-task-log-hint">
                    {t('history.task_logs_error_hint', 'This run contains error-level log entries. Switch to Error Logs to review them quickly.')}
                </div>
            ) : null}
        </section>
    );
}

TaskExecutionLog.propTypes = {
    backtestId: PropTypes.string,
    logs: PropTypes.array,
};

export default TaskExecutionLog;
