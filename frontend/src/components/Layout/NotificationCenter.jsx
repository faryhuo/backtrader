import React, { useState } from 'react';
import { Badge, Popover, List, Button, Typography, Empty, Space } from 'antd';
import {
    BellOutlined,
    CheckCircleOutlined,
    InfoCircleOutlined,
    CloseCircleOutlined,
    WarningOutlined,
    DeleteOutlined,
    CheckOutlined
} from '@ant-design/icons';
import { useHeaderNotification } from '../../providers/NotificationProvider';
import './NotificationCenter.css';

const { Text } = Typography;

const NotificationCenter = () => {
    const {
        notifications,
        unreadCount,
        markAllAsRead,
        clearAll,
        markAsRead
    } = useHeaderNotification();

    const [open, setOpen] = useState(false);

    const handleOpenChange = (newOpen) => {
        setOpen(newOpen);
    };

    const getIcon = (type) => {
        switch (type) {
            case 'success': return <CheckCircleOutlined style={{ color: '#52c41a' }} />;
            case 'error': return <CloseCircleOutlined style={{ color: '#ff4d4f' }} />;
            case 'warning': return <WarningOutlined style={{ color: '#faad14' }} />;
            default: return <InfoCircleOutlined style={{ color: '#1890ff' }} />;
        }
    };

    const content = (
        <div className="notification-popover-content">
            <div className="notification-header">
                <Text strong>Notifications</Text>
                <Space>
                    {unreadCount > 0 && (
                        <Button
                            type="text"
                            size="small"
                            icon={<CheckOutlined />}
                            onClick={markAllAsRead}
                        >
                            Mark all read
                        </Button>
                    )}
                    {notifications.length > 0 && (
                        <Button
                            type="text"
                            size="small"
                            icon={<DeleteOutlined />}
                            onClick={clearAll}
                            danger
                        >
                            Clear
                        </Button>
                    )}
                </Space>
            </div>

            <div className="notification-list-container">
                <List
                    itemLayout="horizontal"
                    style={{ width: 350 }}
                    dataSource={notifications}
                    locale={{ emptyText: <Empty image={Empty.PRESENTED_IMAGE_SIMPLE} description="No notifications" /> }}
                    renderItem={(item) => (
                        <List.Item
                            className={`notification-item ${!item.read ? 'unread' : ''}`}
                            onClick={() => !item.read && markAsRead(item.id)}
                        >
                            <List.Item.Meta
                                avatar={getIcon(item.type)}
                                title={
                                    <div className="notification-item-header">
                                        <Text strong={!item.read} className="notification-message">
                                            {item.message}
                                        </Text>
                                        <Text type="secondary" className="notification-time">
                                            {item.timestamp.toLocaleTimeString()}
                                        </Text>
                                    </div>
                                }
                            />
                        </List.Item>
                    )}
                />
            </div>
        </div>
    );

    return (
        <Popover
            content={content}
            trigger="click"
            open={open}
            onOpenChange={handleOpenChange}
            placement="bottomRight"
            overlayClassName="notification-popover"
        >
            <div className="notification-trigger">
                <Badge count={unreadCount} size="small" offset={[-2, 2]}>
                    <Button
                        type="text"
                        shape="circle"
                        icon={<BellOutlined style={{ fontSize: '18px' }} />}
                        className="btn-ghost"
                    />
                </Badge>
            </div>
        </Popover>
    );
};

export default NotificationCenter;
