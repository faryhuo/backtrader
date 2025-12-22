import { useState, useEffect, useCallback } from 'react';
import { message } from 'antd';
import { useTranslation } from 'react-i18next';
import { useHeaderNotification } from '../providers/NotificationProvider';
import { api } from '../services/api';
import { useWebSocket, WS_MESSAGE_TYPES } from '../services/websocket';

export const useLiveTrading = () => {
    const { t } = useTranslation();
    const { addNotification } = useHeaderNotification();
    // Session state
    const [session, setSession] = useState(null);
    const [loading, setLoading] = useState(false);

    // Trading data state
    const [positions, setPositions] = useState([]);
    const [orders, setOrders] = useState([]);
    const [pnlHistory, setPnlHistory] = useState([]);
    const [currentPnl, setCurrentPnl] = useState(0);
    const [portfolioValue, setPortfolioValue] = useState(0);
    const [cash, setCash] = useState(0);
    // Statistics
    const [stats, setStats] = useState({
        totalTrades: 0,
        winningTrades: 0,
        losingTrades: 0,
        winRate: 0
    });

    // Handle WebSocket messages - defined before useWebSocket to avoid dependency issues
    const handleWebSocketMessage = useCallback((msg) => {
        if (!msg || !msg.type) return;

        switch (msg.type) {
            case WS_MESSAGE_TYPES.CONNECTED:
                // Silently connected - no UI spam
                console.log('WebSocket connected to session');
                break;

            case WS_MESSAGE_TYPES.POSITION:
                setPositions((prevPositions) => {
                    const index = prevPositions.findIndex((p) => p.symbol === msg.data.symbol);
                    if (index >= 0) {
                        const updated = [...prevPositions];
                        updated[index] = { ...updated[index], ...msg.data };
                        return updated;
                    } else {
                        return [...prevPositions, msg.data];
                    }
                });
                break;

            case WS_MESSAGE_TYPES.ORDER:
                setOrders((prevOrders) => {
                    const index = prevOrders.findIndex((o) => o.order_id === msg.data.order_id);
                    if (index >= 0) {
                        const updated = [...prevOrders];
                        updated[index] = { ...updated[index], ...msg.data };
                        return updated;
                    } else {
                        return [msg.data, ...prevOrders];
                    }
                });
                break;

            case WS_MESSAGE_TYPES.PNL: {
                const data = msg.data;
                setCurrentPnl(data.current_pnl || 0);
                setPortfolioValue(data.portfolio_value || 0);
                setCash(data.cash || 0);

                setPnlHistory((prev) => [
                    ...prev,
                    {
                        timestamp: new Date().toISOString(),
                        pnl: data.current_pnl || 0
                    }
                ]);

                if (data.total_trades !== undefined) {
                    setStats((prev) => ({
                        ...prev,
                        totalTrades: data.total_trades || 0,
                        winningTrades: data.winning_trades || 0,
                        losingTrades: data.losing_trades || 0,
                        winRate: data.total_trades > 0
                            ? ((data.winning_trades || 0) / data.total_trades * 100)
                            : 0
                    }));
                }
                break;
            }

            case WS_MESSAGE_TYPES.TRADE: {
                const trade = msg.data;
                const sideLabel = trade.side === 'buy'
                    ? t('live.trade.side.buy', 'Bought')
                    : t('live.trade.side.sell', 'Sold');
                const tradeMsg = t('live.notifications.trade', {
                    side: sideLabel,
                    size: trade.size,
                    symbol: trade.symbol,
                    price: trade.price.toFixed(2)
                });
                message.success(tradeMsg, 3);
                addNotification(tradeMsg, 'success');
                setStats((prev) => ({
                    ...prev,
                    totalTrades: prev.totalTrades + 1
                }));
                break;
            }

            case WS_MESSAGE_TYPES.LOG:
                console.log('[Live Trading]', msg.data.message);
                break;

            case WS_MESSAGE_TYPES.ERROR: {
                const errorMsg = t('live.notifications.trading_error', { error: msg.data.message });
                message.error(errorMsg);
                addNotification(errorMsg, 'error');
                break;
            }

            case WS_MESSAGE_TYPES.STATUS:
                if (msg.data.status) {
                    setSession((prev) => ({ ...prev, status: msg.data.status }));
                }
                break;

            default:
                console.log('Unknown WebSocket message type:', msg.type);
        }
    }, [addNotification, t]);

    // WebSocket connection - initialized at top level per React Hook rules
    // autoConnect: false prevents automatic connection, we manually connect after session starts
    const {
        connect: wsConnect,
        disconnect: wsDisconnect,
        isOpen: wsConnected
    } = useWebSocket(null, {
        autoConnect: false,  // Never auto-connect to prevent reconnection loops
        maxReconnectAttempts: 3,  // Allow some reconnection attempts
        onMessage: handleWebSocketMessage,
        onError: (error) => {
            // Suppress error messages to avoid flooding UI
            console.error('WebSocket error:', error);
        }
    });

    // Start trading session
    const handleStartSession = async (config) => {
        try {
            setLoading(true);
            const result = await api.startLiveTrading(config);

            setSession(result);
            setCurrentPnl(0);
            setPortfolioValue(config.initial_cash);
            setCash(config.initial_cash);
            setPnlHistory([{
                timestamp: new Date().toISOString(),
                pnl: 0
            }]);
            setPositions([]);
            setOrders([]);
            setStats({
                totalTrades: 0,
                winningTrades: 0,
                losingTrades: 0,
                winRate: 0
            });

            const startedMsg = t('live.notifications.session_started', 'Trading session started successfully');
            message.success(startedMsg);
            addNotification(startedMsg, 'success');

            // Manually connect WebSocket after session is successfully created
            // Pass ws_token for authentication
            setTimeout(() => {
                if (result.session_id && result.status === 'running' && result.ws_token) {
                    wsConnect(result.session_id, result.ws_token);
                }
            }, 1000);

        } catch (error) {
            console.error('Failed to start trading session:', error);
            const startFailedMsg = t('live.notifications.session_start_failed', { error: error.message });
            message.error(startFailedMsg);
            addNotification(startFailedMsg, 'error');
        } finally {
            setLoading(false);
        }
    };

    // Stop trading session
    const handleStopSession = async () => {
        if (!session) return;

        try {
            setLoading(true);
            await api.stopLiveTrading(session.session_id);

            const stoppedMsg = t('live.notifications.session_stopped', 'Trading session stopped');
            message.success(stoppedMsg);
            addNotification(stoppedMsg, 'info');
            wsDisconnect();  // Disconnect WebSocket

            setTimeout(() => {
                setSession(null);
            }, 3000);

        } catch (error) {
            console.error('Failed to stop trading session:', error);
            const stopFailedMsg = t('live.notifications.session_stop_failed', { error: error.message });
            message.error(stopFailedMsg);
            addNotification(stopFailedMsg, 'error');
        } finally {
            setLoading(false);
        }
    };

    // Refresh session status
    const handleRefreshSession = async () => {
        if (!session || !session.session_id) {
            console.warn('Cannot refresh: no active session');
            return;
        }

        try {
            setLoading(true);
            const status = await api.getLiveStatus(session.session_id);
            setSession(status);

            const sessionOrders = await api.getSessionOrders(session.session_id);
            setOrders(sessionOrders?.orders || []);

        } catch (error) {
            console.error('Failed to refresh session:', error);
            const refreshFailedMsg = t('live.notifications.session_refresh_failed', 'Failed to refresh session status');
            message.error(refreshFailedMsg);
            addNotification(refreshFailedMsg, 'error');
        } finally {
            setLoading(false);
        }
    };

    const loadActiveSessions = async () => {
        try {
            const result = await api.listLiveSessions({ active_only: true });
            const activeSessions = result?.sessions || [];

            if (activeSessions.length > 0) {
                const activeSession = activeSessions[0];
                setSession(activeSession);

                // Only fetch orders if session_id exists
                if (activeSession.session_id) {
                    const ordersData = await api.getSessionOrders(activeSession.session_id);
                    setOrders(ordersData?.orders || []);

                    if (activeSession.status === 'running' && activeSession.ws_token) {
                        setTimeout(() => wsConnect(activeSession.session_id, activeSession.ws_token), 500);
                    }
                }
            }
        } catch (error) {
            console.error('Failed to load active sessions:', error);
        }
    };

    useEffect(() => {
        loadActiveSessions();
        // eslint-disable-next-line react-hooks/exhaustive-deps
    }, []);

    return {
        session,
        loading,
        positions,
        orders,
        pnlHistory,
        currentPnl,
        portfolioValue,
        cash,
        stats,
        wsConnected,
        handleStartSession,
        handleStopSession,
        handleRefreshSession
    };
};
