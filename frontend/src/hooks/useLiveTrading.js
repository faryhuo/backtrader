import { useReducer, useState, useEffect, useCallback, useRef } from 'react';
import { message } from 'antd';
import { useTranslation } from 'react-i18next';
import { useHeaderNotification } from '../providers/NotificationProvider';
import { liveApi } from '../services/liveApi';
import { useWebSocket, WS_MESSAGE_TYPES } from '../services/websocket';

// ──────────────────────── state shape & reducer ────────────────────────

const initialState = {
    session: null,
    loading: false,
    positions: [],
    orders: [],
    recentErrors: [],
    pnlHistory: [],
    currentPnl: 0,
    portfolioValue: 0,
    cash: 0,
    ticker: null,   // { last, bid, ask, timestamp }
    prevTicker: null, // Previous ticker for price change calculation
    openPrice: null, // Opening price (first ticker price)
    priceHistory: [], // For price chart: { time, open, high, low, close }
    stats: { totalTrades: 0, winningTrades: 0, losingTrades: 0, winRate: 0 },
    logs: [], // Strategy logs, max 100 entries
    feedStatus: 'warming_up',
    error: null,
};

function reducer(state, action) {
    switch (action.type) {
        case 'SET_LOADING':
            return { ...state, loading: action.payload };

        case 'SESSION_STARTED':
            return {
                ...state,
                session: action.payload,
                positions: [],
                orders: [],
                recentErrors: [],
                pnlHistory: [{ timestamp: new Date().toISOString(), pnl: 0 }],
                currentPnl: 0,
                portfolioValue: action.payload.initial_cash || 0,
                cash: action.payload.initial_cash || 0,
                ticker: null,
                prevTicker: null,
                openPrice: null,
                priceHistory: [],
                stats: { totalTrades: 0, winningTrades: 0, losingTrades: 0, winRate: 0 },
                logs: [],
                feedStatus: action.payload.feed_status || 'warming_up',
                error: null,
            };

        case 'SESSION_LOADED':
            return {
                ...state,
                session: action.payload,
                feedStatus: action.payload.feed_status || state.feedStatus,
                error: null,
            };

        case 'SESSION_STOPPED':
            return {
                ...state,
                session: action.payload,
                feedStatus: action.payload?.feed_status || 'warming_up',
            };

        case 'SESSION_CLEARED':
            return { ...initialState };

        case 'POSITION_UPDATE': {
            const pos = action.payload;
            const idx = state.positions.findIndex(p => p.symbol === pos.symbol);
            const updated = [...state.positions];
            if (idx >= 0) updated[idx] = { ...updated[idx], ...pos };
            else updated.push(pos);
            return { ...state, positions: updated };
        }

        case 'POSITIONS_LOADED':
            return { ...state, positions: action.payload };

        case 'ORDER_UPDATE': {
            const order = action.payload;
            const idx = state.orders.findIndex(o => o.order_id === order.order_id);
            const updated = [...state.orders];
            if (idx >= 0) updated[idx] = { ...updated[idx], ...order };
            else updated.unshift(order);
            return { ...state, orders: updated };
        }

        case 'PNL_UPDATE': {
            const d = action.payload;
            return {
                ...state,
                currentPnl: d.current_pnl || 0,
                portfolioValue: d.portfolio_value || 0,
                cash: d.cash || 0,
                pnlHistory: [
                    ...state.pnlHistory,
                    { timestamp: new Date().toISOString(), pnl: d.current_pnl || 0 },
                ],
                stats: d.total_trades !== undefined ? {
                    totalTrades: d.total_trades || 0,
                    winningTrades: d.winning_trades || 0,
                    losingTrades: d.losing_trades || 0,
                    winRate: d.total_trades > 0
                        ? ((d.winning_trades || 0) / d.total_trades * 100)
                        : 0,
                } : state.stats,
            };
        }

        case 'TICKER_UPDATE': {
            const newTicker = action.payload;
            const now = Math.floor(Date.now() / 1000);
            const lastCandle = state.priceHistory.length > 0
                ? state.priceHistory[state.priceHistory.length - 1]
                : null;

            let newHistory = [...state.priceHistory];

            // If we have a previous candle in the same minute, update it
            if (lastCandle && lastCandle.time >= now - 60) {
                newHistory[newHistory.length - 1] = {
                    time: lastCandle.time,
                    open: lastCandle.open,
                    high: Math.max(lastCandle.high, newTicker.last),
                    low: Math.min(lastCandle.low, newTicker.last),
                    close: newTicker.last,
                };
            } else {
                // Create new candle
                newHistory.push({
                    time: now,
                    open: newTicker.last,
                    high: newTicker.last,
                    low: newTicker.last,
                    close: newTicker.last,
                });
            }

            // Set open price on first ticker
            const openPrice = state.openPrice || (newTicker.last ? Number(newTicker.last) : null);

            return {
                ...state,
                prevTicker: state.ticker,
                ticker: newTicker,
                openPrice,
                priceHistory: newHistory,
            };
        }

        case 'OHLCV_UPDATE': {
            // Initial historical OHLCV data from backfill
            const bars = action.payload.bars || [];
            if (bars.length === 0) return state;

            const history = bars.map(bar => ({
                time: bar.time,
                open: bar.open,
                high: bar.high,
                low: bar.low,
                close: bar.close,
            }));

            return {
                ...state,
                priceHistory: history,
                openPrice: history.length > 0 ? history[0].open : null,
            };
        }

        case 'TRADE_EXECUTED':
            return {
                ...state,
                stats: { ...state.stats, totalTrades: state.stats.totalTrades + 1 },
            };

        case 'STATUS_UPDATE':
            return {
                ...state,
                session: state.session
                    ? { ...state.session, status: action.payload }
                    : state.session,
            };

        case 'FEED_STATUS_UPDATE':
            return {
                ...state,
                feedStatus: action.payload,
                session: state.session
                    ? { ...state.session, feed_status: action.payload }
                    : state.session,
            };

        case 'ORDERS_LOADED':
            return { ...state, orders: action.payload };

        case 'LOG_UPDATE': {
            const newLog = action.payload;
            const logs = [newLog, ...state.logs].slice(0, 100); // Keep max 100
            return { ...state, logs };
        }

        case 'LOGS_LOADED': {
            // Replace logs from REST polling (array of {timestamp, level, message})
            const loaded = action.payload.map(l => ({
                timestamp: l.timestamp || Date.now(),
                level: l.level || 'info',
                message: l.message,
            }));
            return { ...state, logs: loaded.reverse().slice(0, 100) };
        }

        case 'SET_ERROR':
            return { ...state, error: action.payload };

        case 'TRADE_ERROR': {
            const errorEntry = action.payload;
            return {
                ...state,
                error: errorEntry.message,
                recentErrors: [errorEntry, ...state.recentErrors].slice(0, 5),
            };
        }

        case 'TRADE_ERRORS_LOADED':
            return { ...state, recentErrors: action.payload };

        default:
            return state;
    }
}

// ──────────────────────── hook ────────────────────────

export const useLiveTrading = () => {
    const { t } = useTranslation();
    const { addNotification } = useHeaderNotification();
    const [state, dispatch] = useReducer(reducer, initialState);

    // WebSocket session tracking — drives the useWebSocket hook
    const [wsSessionId, setWsSessionId] = useState(null);
    const [wsToken, setWsToken] = useState(null);

    const resolveTradingErrorMessage = useCallback((code, fallbackMessage) => {
        const key = code ? `live.errors.codes.${code}` : null;
        if (key) {
            const translated = t(key);
            if (translated && translated !== key) {
                return translated;
            }
        }
        return fallbackMessage;
    }, [t]);

    const loadTradingState = useCallback(async (sessionId) => {
        const [ordersResult, positionsResult, tradeErrorsResult, accountResult] = await Promise.allSettled([
            liveApi.getSessionOrders(sessionId),
            liveApi.getSessionPositions(sessionId),
            liveApi.getTradeErrors(sessionId),
            liveApi.getSessionAccountSnapshot(sessionId),
        ]);

        if (ordersResult.status === 'fulfilled') {
            dispatch({ type: 'ORDERS_LOADED', payload: ordersResult.value?.orders || [] });
        } else {
            console.warn('[POLLING] Orders fetch failed:', ordersResult.reason?.message || ordersResult.reason);
        }

        if (positionsResult.status === 'fulfilled') {
            dispatch({ type: 'POSITIONS_LOADED', payload: positionsResult.value?.positions || [] });
        } else {
            console.warn('[POLLING] Positions fetch failed:', positionsResult.reason?.message || positionsResult.reason);
        }

        if (tradeErrorsResult.status === 'fulfilled') {
            dispatch({
                type: 'TRADE_ERRORS_LOADED',
                payload: (tradeErrorsResult.value?.errors || []).slice().reverse().map((item) => ({
                    ...item,
                    displayMessage: resolveTradingErrorMessage(item.code, item.message),
                })),
            });
        } else {
            console.warn('[POLLING] Trade errors fetch failed:', tradeErrorsResult.reason?.message || tradeErrorsResult.reason);
        }

        if (accountResult.status === 'fulfilled') {
            dispatch({ type: 'PNL_UPDATE', payload: accountResult.value });
        } else {
            console.warn('[POLLING] Account snapshot fetch failed:', accountResult.reason?.message || accountResult.reason);
        }
    }, [resolveTradingErrorMessage]);

    // Ticker polling interval ref
    const tickerIntervalRef = useRef(null);

    // WebSocket message handler
    const handleWSMessage = useCallback((msg) => {
        if (!msg || !msg.type) return;

        console.log('[WS] Received message:', msg.type, msg.data);

        switch (msg.type) {
            case WS_MESSAGE_TYPES.CONNECTED:
                break;

            case WS_MESSAGE_TYPES.POSITION:
                dispatch({ type: 'POSITION_UPDATE', payload: msg.data });
                break;

            case WS_MESSAGE_TYPES.ORDER:
                dispatch({ type: 'ORDER_UPDATE', payload: msg.data });
                break;

            case WS_MESSAGE_TYPES.PNL:
                dispatch({ type: 'PNL_UPDATE', payload: msg.data });
                break;

            case WS_MESSAGE_TYPES.TICKER:
                dispatch({ type: 'TICKER_UPDATE', payload: msg.data });
                break;

            case WS_MESSAGE_TYPES.OHLCV:
                dispatch({ type: 'OHLCV_UPDATE', payload: msg.data });
                break;

            case WS_MESSAGE_TYPES.TRADE: {
                const trade = msg.data;
                const sideLabel = trade.side === 'buy'
                    ? t('live.trade.side.buy', 'Bought')
                    : t('live.trade.side.sell', 'Sold');
                const tradeMsg = t('live.notifications.trade', {
                    side: sideLabel,
                    size: trade.size,
                    symbol: trade.symbol,
                    price: trade.price?.toFixed(2)
                });
                message.success(tradeMsg, 3);
                addNotification(tradeMsg, 'success');
                dispatch({ type: 'TRADE_EXECUTED' });
                break;
            }

            case WS_MESSAGE_TYPES.LOG: {
                const logEntry = {
                    timestamp: msg.data.timestamp || Date.now(),
                    level: msg.data.level || 'info',
                    message: msg.data.message,
                };
                dispatch({ type: 'LOG_UPDATE', payload: logEntry });
                break;
            }

            case WS_MESSAGE_TYPES.ERROR: {
                const displayMessage = resolveTradingErrorMessage(msg.data.code, msg.data.message);
                const errorMsg = t('live.notifications.trading_error', { error: displayMessage });
                message.error(errorMsg);
                addNotification(errorMsg, 'error');
                dispatch({
                    type: 'TRADE_ERROR',
                    payload: {
                        code: msg.data.code || 'ORDER_REJECTED',
                        message: msg.data.message,
                        displayMessage,
                        timestamp: new Date().toISOString(),
                    },
                });
                break;
            }

            case WS_MESSAGE_TYPES.STATUS:
                if (msg.data.status || msg.data.new_status) {
                    dispatch({ type: 'STATUS_UPDATE', payload: msg.data.status || msg.data.new_status });
                }
                break;

            case WS_MESSAGE_TYPES.FEED_STATUS:
                if (msg.data.status) {
                    dispatch({ type: 'FEED_STATUS_UPDATE', payload: msg.data.status });
                }
                break;

            default:
                break;
        }
    }, [addNotification, t]);

    // WebSocket connection — sessionId/token as state drives the hook
    const {
        connect: wsConnect,
        disconnect: wsDisconnect,
        isOpen: wsConnected
    } = useWebSocket(wsSessionId, {
        token: wsToken,
        autoConnect: false,
        maxReconnectAttempts: 3,
        onMessage: handleWSMessage,
        onError: (error) => console.error('WebSocket error:', error)
    });

    // Auto-connect WS when sessionId/token become available
    useEffect(() => {
        console.log('[WS] SessionId:', wsSessionId, 'Token:', wsToken ? 'set' : 'missing');
        if (wsSessionId && wsToken) {
            // Small delay to ensure buildUrl ref is updated after render
            const timer = setTimeout(() => {
                console.log('[WS] Connecting...');
                wsConnect();
            }, 200);
            return () => clearTimeout(timer);
        } else {
            console.log('[WS] Not connecting - missing sessionId or token');
        }
    }, [wsSessionId, wsToken, wsConnect]);

    // ──────────────── ticker polling (REST fallback) ────────────────

    const tickerErrorCountRef = useRef(0);

    const startTickerPolling = useCallback((sessionId) => {
        if (tickerIntervalRef.current) clearInterval(tickerIntervalRef.current);
        tickerErrorCountRef.current = 0;
        tickerIntervalRef.current = setInterval(async () => {
            try {
                const ticker = await liveApi.getTickerPrice(sessionId);
                dispatch({ type: 'TICKER_UPDATE', payload: ticker });
                tickerErrorCountRef.current = 0;
            } catch {
                tickerErrorCountRef.current += 1;
                // Stop polling after 6 consecutive failures (30s)
                if (tickerErrorCountRef.current >= 6) {
                    clearInterval(tickerIntervalRef.current);
                    tickerIntervalRef.current = null;
                }
            }
        }, 5000);
    }, []);

    const stopTickerPolling = useCallback(() => {
        if (tickerIntervalRef.current) {
            clearInterval(tickerIntervalRef.current);
            tickerIntervalRef.current = null;
        }
    }, []);

    // ──────────────── OHLCV + Logs REST polling (fallback) ────────────────

    const ohlcvIntervalRef = useRef(null);
    const logsIntervalRef = useRef(null);

    const startDataPolling = useCallback((sessionId) => {
        console.log('[POLLING] Starting data polling for session:', sessionId);

        // Poll OHLCV every 30s
        // Initial fetch after 3s (give time for WebSocket to connect first)
        const ohlcvTimer = setTimeout(async () => {
            console.log('[POLLING] Fetching initial OHLCV...');
            try {
                const data = await liveApi.getOhlcv(sessionId);
                console.log('[POLLING] OHLCV received:', data?.bars?.length, 'bars');
                if (data?.bars?.length > 0) {
                    dispatch({ type: 'OHLCV_UPDATE', payload: data });
                }
            } catch (e) {
                console.warn('[POLLING] OHLCV fetch failed:', e.message);
            }

            await loadTradingState(sessionId);

            // Continue polling every 30s
            ohlcvIntervalRef.current = setInterval(async () => {
                try {
                    const data = await liveApi.getOhlcv(sessionId);
                    if (data?.bars?.length > 0) {
                        dispatch({ type: 'OHLCV_UPDATE', payload: data });
                    }
                } catch { /* silently ignore */ }
                await loadTradingState(sessionId);
            }, 30000);
        }, 3000);

        // Store initial timer for cleanup (need to clear both timer and interval)
        ohlcvIntervalRef.current = ohlcvTimer;

        // Poll logs every 5s
        logsIntervalRef.current = setInterval(async () => {
            try {
                const data = await liveApi.getStrategyLogs(sessionId);
                if (data?.logs?.length > 0) {
                    console.log('[POLLING] Logs received:', data.logs.length);
                    dispatch({ type: 'LOGS_LOADED', payload: data.logs });
                }
            } catch { /* silently ignore */ }
            await loadTradingState(sessionId);
        }, 5000);
    }, [loadTradingState]);

    const stopDataPolling = useCallback(() => {
        if (ohlcvIntervalRef.current) {
            clearInterval(ohlcvIntervalRef.current);
            clearTimeout(ohlcvIntervalRef.current);
            ohlcvIntervalRef.current = null;
        }
        if (logsIntervalRef.current) {
            clearInterval(logsIntervalRef.current);
            logsIntervalRef.current = null;
        }
    }, []);

    // ──────────────── actions ────────────────

    const handleStartSession = useCallback(async (config) => {
        try {
            dispatch({ type: 'SET_LOADING', payload: true });
            const result = await liveApi.startSession(config);
            console.log('[SESSION] Start result:', result);
            dispatch({ type: 'SESSION_STARTED', payload: result });

            message.success(t('live.notifications.session_started', 'Trading session started'));
            addNotification(t('live.notifications.session_started', 'Trading session started'), 'success');

            // Set WS session/token — the useEffect above will auto-connect
            if (result.session_id && result.ws_token) {
                console.log('[SESSION] Setting WS sessionId:', result.session_id, 'ws_token:', result.ws_token ? 'set' : 'missing');
                setWsSessionId(result.session_id);
                setWsToken(result.ws_token);
            } else {
                console.warn('[SESSION] Missing session_id or ws_token:', result);
            }
            startTickerPolling(result.session_id);
            startDataPolling(result.session_id);

        } catch (error) {
            const msg = t('live.notifications.session_start_failed', { error: error.message });
            message.error(msg);
            addNotification(msg, 'error');
            dispatch({ type: 'SET_ERROR', payload: error.message });
        } finally {
            dispatch({ type: 'SET_LOADING', payload: false });
        }
    }, [t, addNotification, startTickerPolling, startDataPolling]);

    const handleStopSession = useCallback(async () => {
        if (!state.session) return;
        try {
            dispatch({ type: 'SET_LOADING', payload: true });
            const result = await liveApi.stopSession(state.session.session_id);
            dispatch({ type: 'SESSION_STOPPED', payload: { ...state.session, ...result, status: result.status || 'stopped' } });

            message.success(t('live.notifications.session_stopped', 'Trading session stopped'));
            addNotification(t('live.notifications.session_stopped', 'Trading session stopped'), 'info');
            wsDisconnect();
            setWsSessionId(null);
            setWsToken(null);
            stopTickerPolling();
            stopDataPolling();

            // Clear session after delay so user can see final state
            setTimeout(() => dispatch({ type: 'SESSION_CLEARED' }), 3000);
        } catch (error) {
            const msg = t('live.notifications.session_stop_failed', { error: error.message });
            message.error(msg);
            addNotification(msg, 'error');
        } finally {
            dispatch({ type: 'SET_LOADING', payload: false });
        }
    }, [state.session, t, addNotification, wsDisconnect, stopTickerPolling, stopDataPolling]);

    const handleRefreshSession = useCallback(async () => {
        if (!state.session?.session_id) return;
        try {
            dispatch({ type: 'SET_LOADING', payload: true });
            const status = await liveApi.getSessionStatus(state.session.session_id);
            dispatch({ type: 'SESSION_LOADED', payload: status });

            await loadTradingState(state.session.session_id);
        } catch (_error) {
            message.error(t('live.notifications.session_refresh_failed', 'Failed to refresh'));
        } finally {
            dispatch({ type: 'SET_LOADING', payload: false });
        }
    }, [loadTradingState, state.session, t]);

    const handleCancelOrder = useCallback(async (orderId) => {
        if (!state.session?.session_id) return;
        try {
            await liveApi.cancelOrder(state.session.session_id, orderId);
            message.success(t('live.notifications.order_cancelled', 'Order cancelled'));
            // Order update will come via WebSocket
        } catch (error) {
            message.error(t('live.notifications.order_cancel_failed', { error: error.message }));
        }
    }, [state.session, t]);

    // ──────────────── auto-load active session on mount ────────────────

    useEffect(() => {
        const loadActive = async () => {
            try {
                const result = await liveApi.listSessions({ active_only: true });
                const sessions = result?.sessions || [];
                if (sessions.length > 0) {
                    const active = sessions[0];
                    dispatch({ type: 'SESSION_LOADED', payload: active });

                    if (active.session_id) {
                        await loadTradingState(active.session_id);

                        if (active.status === 'running' && active.ws_token) {
                            setWsSessionId(active.session_id);
                            setWsToken(active.ws_token);
                        }
                        startTickerPolling(active.session_id);
                        startDataPolling(active.session_id);
                    }
                }
            } catch (error) {
                console.error('Failed to load active sessions:', error);
            }
        };
        loadActive();
        return () => {
            stopTickerPolling();
            stopDataPolling();
        };
        // eslint-disable-next-line react-hooks/exhaustive-deps
    }, [loadTradingState]);

    return {
        // State
        session: state.session,
        loading: state.loading,
        positions: state.positions,
        orders: state.orders,
        recentErrors: state.recentErrors,
        pnlHistory: state.pnlHistory,
        currentPnl: state.currentPnl,
        portfolioValue: state.portfolioValue,
        cash: state.cash,
        ticker: state.ticker,
        prevTicker: state.prevTicker,
        openPrice: state.openPrice,
        priceHistory: state.priceHistory,
        stats: state.stats,
        logs: state.logs,
        feedStatus: state.feedStatus,
        error: state.error,
        wsConnected,

        // Actions
        handleStartSession,
        handleStopSession,
        handleRefreshSession,
        handleCancelOrder,
    };
};
