import { useState, useCallback } from 'react';
import { api } from '../services/api';
import { taskApi } from '../services/taskApi';

/**
 * Hook for running backtests with task polling.
 * Handles both async task-based and legacy synchronous backtest responses.
 *
 * @returns {Object} Backtest execution state and handlers
 */
export function useBacktest() {
    const [result, setResult] = useState(null);
    const [loading, setLoading] = useState(false);
    const [error, setError] = useState(null);
    const [taskProgress, setTaskProgress] = useState(null);

    // Poll for task completion
    const pollTaskCompletion = useCallback(async (taskId, taskName, fetchResult) => {
        let taskStatus = 'pending';
        let taskData = null;

        // Initial progress
        setTaskProgress({
            status: taskStatus,
            progress: 0,
            name: taskName,
            message: 'Starting...'
        });

        while (taskStatus === 'pending' || taskStatus === 'running') {
            await new Promise(resolve => setTimeout(resolve, 1000));
            taskData = await taskApi.getTask(taskId);
            taskStatus = taskData.status;

            setTaskProgress({
                status: taskStatus,
                progress: taskData.progress || 0,
                name: taskData.name || taskName,
                message: taskData.logs?.slice(-1)?.[0]?.message ||
                    (taskStatus === 'running' ? 'Running...' : 'Waiting...')
            });
        }

        if (taskStatus === 'completed' && taskData?.result_id) {
            return await fetchResult(taskData.result_id);
        } else if (taskStatus === 'failed') {
            throw new Error(taskData?.error_message || 'Task failed');
        } else if (taskStatus === 'cancelled') {
            throw new Error('Task was cancelled');
        }

        return null;
    }, []);

    // Run single-asset backtest
    const runBacktest = useCallback(async (params, t) => {
        const {
            ticker,
            startDate,
            endDate,
            initialCash,
            commission,
            stake,
            selectedStrategy,
            paramOverrides,
        } = params;

        if (!selectedStrategy) {
            setError(t?.('config_form.select_strategy_required') || 'Please select a strategy first.');
            return null;
        }

        setLoading(true);
        setError(null);
        setResult(null);
        setTaskProgress(null);

        try {
            const paramsToSend = Object.keys(paramOverrides || {}).length > 0 ? paramOverrides : null;

            const taskResponse = await api.runBacktest({
                ticker,
                start_date: startDate,
                end_date: endDate,
                initial_cash: parseFloat(initialCash),
                commission: parseFloat(commission),
                stake: parseInt(stake, 10),
                strategy_name: selectedStrategy,
                params: paramsToSend
            });

            // Handle async task-based response
            if (taskResponse.task_id) {
                const taskName = taskResponse.name || `Backtest ${ticker} - ${selectedStrategy}`;
                const backtestResult = await pollTaskCompletion(
                    taskResponse.task_id,
                    taskName,
                    api.getBacktestDetail
                );
                setResult(backtestResult);
                return backtestResult;
            } else {
                // Legacy synchronous response
                setResult(taskResponse);
                return taskResponse;
            }
        } catch (err) {
            console.error(err);
            setError(err.message || t?.('common.error_occurred') || 'An error occurred');
            return null;
        } finally {
            setLoading(false);
            setTaskProgress(null);
        }
    }, [pollTaskCompletion]);

    // Run portfolio backtest
    const runPortfolioBacktest = useCallback(async (params, t) => {
        const {
            tickers,
            weights,
            startDate,
            endDate,
            initialCash,
            commission,
            stake,
            selectedStrategy,
            paramOverrides,
        } = params;

        const validTickers = tickers.filter(ticker => ticker.trim());
        if (validTickers.length === 0) {
            setError(t?.('portfolio.validation.no_ticker') || 'Please enter at least one ticker');
            return null;
        }

        setLoading(true);
        setError(null);
        setResult(null);
        setTaskProgress(null);

        try {
            const paramsToSend = Object.keys(paramOverrides || {}).length > 0 ? paramOverrides : null;

            const taskResponse = await api.runPortfolioBacktest({
                tickers: validTickers,
                weights: weights.slice(0, validTickers.length),
                start_date: startDate,
                end_date: endDate,
                initial_cash: initialCash,
                commission: commission,
                stake: stake,
                strategy_name: selectedStrategy || null,
                params: paramsToSend
            });

            // Handle async task-based response
            if (taskResponse.task_id) {
                const taskName = taskResponse.name || `Portfolio Backtest`;
                const portfolioResult = await pollTaskCompletion(
                    taskResponse.task_id,
                    taskName,
                    api.getPortfolioDetail
                );
                setResult(portfolioResult);
                return portfolioResult;
            } else {
                // Legacy synchronous response
                setResult(taskResponse);
                return taskResponse;
            }
        } catch (err) {
            setError(err?.message || t?.('portfolio.error.run_failed') || 'Portfolio backtest failed');
            return null;
        } finally {
            setLoading(false);
            setTaskProgress(null);
        }
    }, [pollTaskCompletion]);

    // Clear results
    const clearResult = useCallback(() => {
        setResult(null);
        setError(null);
        setTaskProgress(null);
    }, []);

    return {
        result,
        loading,
        error,
        taskProgress,
        runBacktest,
        runPortfolioBacktest,
        clearResult,
        setResult,
        setError,
    };
}

export default useBacktest;
