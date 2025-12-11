import { createContext, useContext, useState, useCallback } from 'react';

const NotificationContext = createContext(null);

export const NotificationProvider = ({ children }) => {
    const [notifications, setNotifications] = useState([]);
    const [unreadCount, setUnreadCount] = useState(0);

    const addNotification = useCallback((message, type = 'info') => {
        const newNotification = {
            id: Date.now(),
            message,
            type,
            timestamp: new Date(),
            read: false,
        };

        setNotifications(prev => [newNotification, ...prev]);
        setUnreadCount(prev => prev + 1);
    }, []);

    const markAsRead = useCallback((id) => {
        setNotifications(prev => prev.map(n => 
            n.id === id ? { ...n, read: true } : n
        ));
        setUnreadCount(prev => Math.max(0, prev - 1));
    }, []);

    const markAllAsRead = useCallback(() => {
        setNotifications(prev => prev.map(n => ({ ...n, read: true })));
        setUnreadCount(0);
    }, []);

    const clearAll = useCallback(() => {
        setNotifications([]);
        setUnreadCount(0);
    }, []);

    return (
        <NotificationContext.Provider value={{ 
            notifications, 
            unreadCount, 
            addNotification, 
            markAsRead, 
            markAllAsRead, 
            clearAll 
        }}>
            {children}
        </NotificationContext.Provider>
    );
};

export const useHeaderNotification = () => {
    const context = useContext(NotificationContext);
    if (!context) {
        throw new Error('useHeaderNotification must be used within a NotificationProvider');
    }
    return context;
};