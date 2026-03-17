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
    pnlHistory: [],
    currentPnl: 0,
    portfolioValue: 0,
    cash: 0,
    ticker: null,   // { last, bid, ask, timestamp }
    stats: { totalTrades: 0, winningTrades: 0, losingTrades: 0, winRate: 0 },
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
                pnlHistory: [{ timestamp: new Date().toISOString(), pnl: 0 }],
                currentPnl: 0,
                portfolioValue: action.payload.initial_cash || 0,
                cash: action.payload.initial_cash || 0,
                ticker: null,
                stats: { totalTrades: 0, winningTrades: 0, losingTrades: 0, winRate: 0 },
                error: null,
            };

        case 'SESSION_LOADED':
            return { ...state, session: action.payload, error: null };

        case 'SESSION_STOPPED':
            return { ...state, session: action.payload };

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

        case 'TICKER_UPDATE':
            return { ...state, ticker: action.payload };

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

        case 'ORDERS_LOADED':
            return { ...state, orders: action.payload };

        case 'SET_ERROR':
            return { ...state, error: action.payload };

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

    // Ticker polling interval ref
    const tickerIntervalRef = useRef(null);

    // WebSocket message handler
    const handleWSMessage = useCallback((msg) => {
        if (!msg || !msg.type) return;

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

            case WS_MESSAGE_TYPES.LOG:
                break;

            case WS_MESSAGE_TYPES.ERROR: {
                const errorMsg = t('live.notifications.trading_error', { error: msg.data.message });
                message.error(errorMsg);
                addNotification(errorMsg, 'error');
                dispatch({ type: 'SET_ERROR', payload: msg.data.message });
                break;
            }

            case WS_MESSAGE_TYPES.STATUS:
                if (msg.data.status) {
                    dispatch({ type: 'STATUS_UPDATE', payload: msg.data.status || msg.data.new_status });
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
        if (wsSessionId && wsToken) {
            // Small delay to ensure buildUrl ref is updated after render
            const timer = setTimeout(() => wsConnect(), 200);
            return () => clearTimeout(timer);
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

    // ──────────────── actions ────────────────

    const handleStartSession = useCallback(async (config) => {
        try {
            dispatch({ type: 'SET_LOADING', payload: true });
            const result = await liveApi.startSession(config);
            dispatch({ type: 'SESSION_STARTED', payload: result });

            message.success(t('live.notifications.session_started', 'Trading session started'));
            addNotification(t('live.notifications.session_started', 'Trading session started'), 'success');

            // Set WS session/token — the useEffect above will auto-connect
            if (result.session_id && result.ws_token) {
                setWsSessionId(result.session_id);
                setWsToken(result.ws_token);
            }
            startTickerPolling(result.session_id);

        } catch (error) {
            const msg = t('live.notifications.session_start_failed', { error: error.message });
            message.error(msg);
            addNotification(msg, 'error');
            dispatch({ type: 'SET_ERROR', payload: error.message });
        } finally {
            dispatch({ type: 'SET_LOADING', payload: false });
        }
    }, [t, addNotification, startTickerPolling]);

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

            // Clear session after delay so user can see final state
            setTimeout(() => dispatch({ type: 'SESSION_CLEARED' }), 3000);
        } catch (error) {
            const msg = t('live.notifications.session_stop_failed', { error: error.message });
            message.error(msg);
            addNotification(msg, 'error');
        } finally {
            dispatch({ type: 'SET_LOADING', payload: false });
        }
    }, [state.session, t, addNotification, wsDisconnect, stopTickerPolling]);

    const handleRefreshSession = useCallback(async () => {
        if (!state.session?.session_id) return;
        try {
            dispatch({ type: 'SET_LOADING', payload: true });
            const status = await liveApi.getSessionStatus(state.session.session_id);
            dispatch({ type: 'SESSION_LOADED', payload: status });

            const ordersData = await liveApi.getSessionOrders(state.session.session_id);
            dispatch({ type: 'ORDERS_LOADED', payload: ordersData?.orders || [] });
        } catch (_error) {
            message.error(t('live.notifications.session_refresh_failed', 'Failed to refresh'));
        } finally {
            dispatch({ type: 'SET_LOADING', payload: false });
        }
    }, [state.session, t]);

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
                        const ordersData = await liveApi.getSessionOrders(active.session_id);
                        dispatch({ type: 'ORDERS_LOADED', payload: ordersData?.orders || [] });

                        if (active.status === 'running' && active.ws_token) {
                            setWsSessionId(active.session_id);
                            setWsToken(active.ws_token);
                        }
                        startTickerPolling(active.session_id);
                    }
                }
            } catch (error) {
                console.error('Failed to load active sessions:', error);
            }
        };
        loadActive();
        return () => stopTickerPolling();
        // eslint-disable-next-line react-hooks/exhaustive-deps
    }, []);

    return {
        // State
        session: state.session,
        loading: state.loading,
        positions: state.positions,
        orders: state.orders,
        pnlHistory: state.pnlHistory,
        currentPnl: state.currentPnl,
        portfolioValue: state.portfolioValue,
        cash: state.cash,
        ticker: state.ticker,
        stats: state.stats,
        error: state.error,
        wsConnected,

        // Actions
        handleStartSession,
        handleStopSession,
        handleRefreshSession,
        handleCancelOrder,
    };
};
