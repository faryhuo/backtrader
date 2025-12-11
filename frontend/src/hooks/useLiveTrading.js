import { useState, useEffect, useCallback } from 'react';
import { message } from 'antd';
import { api } from '../services/api';
import { useWebSocket, WS_MESSAGE_TYPES } from '../services/websocket';

export const useLiveTrading = () => {
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

    // Handle WebSocket messages
    const handleWebSocketMessage = useCallback((msg) => {
        if (!msg || !msg.type) return;

        switch (msg.type) {
            case WS_MESSAGE_TYPES.CONNECTED:
                message.success('Connected to live trading session');
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

            case WS_MESSAGE_TYPES.PNL:
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

            case WS_MESSAGE_TYPES.TRADE:
                const trade = msg.data;
                const side = trade.side === 'buy' ? 'Bought' : 'Sold';
                message.success(`${side} ${trade.size} ${trade.symbol} @ $${trade.price.toFixed(2)}`, 3);
                setStats((prev) => ({
                    ...prev,
                    totalTrades: prev.totalTrades + 1
                }));
                break;

            case WS_MESSAGE_TYPES.LOG:
                console.log('[Live Trading]', msg.data.message);
                break;

            case WS_MESSAGE_TYPES.ERROR:
                message.error(`Trading error: ${msg.data.message}`);
                break;

            case WS_MESSAGE_TYPES.STATUS:
                if (msg.data.status) {
                    setSession((prev) => ({ ...prev, status: msg.data.status }));
                }
                break;

            default:
                console.log('Unknown WebSocket message type:', msg.type);
        }
    }, []);

    // WebSocket connection
    const {
        isOpen: wsConnected,
        connect: wsConnect,
        disconnect: wsDisconnect
    } = useWebSocket(session?.session_id, {
        autoConnect: false,
        onMessage: handleWebSocketMessage,
        onError: (error) => {
            console.error('WebSocket error:', error);
            message.error('WebSocket connection error');
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

            message.success('Trading session started successfully');

            setTimeout(() => {
                wsConnect();
            }, 1000);

        } catch (error) {
            console.error('Failed to start trading session:', error);
            message.error(`Failed to start session: ${error.message}`);
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

            message.success('Trading session stopped');
            wsDisconnect();

            setTimeout(() => {
                setSession(null);
            }, 3000);

        } catch (error) {
            console.error('Failed to stop trading session:', error);
            message.error(`Failed to stop session: ${error.message}`);
        } finally {
            setLoading(false);
        }
    };

    // Refresh session status
    const handleRefreshSession = async () => {
        if (!session) return;

        try {
            setLoading(true);
            const status = await api.getLiveStatus(session.session_id);
            setSession(status);

            const sessionOrders = await api.getSessionOrders(session.session_id);
            setOrders(sessionOrders?.orders || []);

        } catch (error) {
            console.error('Failed to refresh session:', error);
            message.error('Failed to refresh session status');
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

                if (activeSession.session_id) {
                    const ordersData = await api.getSessionOrders(activeSession.session_id);
                    setOrders(ordersData?.orders || []);

                    setTimeout(() => {
                        wsConnect();
                    }, 500);
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

    useEffect(() => {
        return () => {
            wsDisconnect();
        };
    }, [wsDisconnect]);

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
