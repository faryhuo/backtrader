import { useState, useEffect } from 'react'
import { Outlet } from 'react-router-dom'
import { useTranslation } from 'react-i18next'
import { Dropdown, Avatar, Space } from 'antd'
import {
    UserOutlined,
    LogoutOutlined,
    GlobalOutlined
} from '@ant-design/icons'
import { useAuth } from '../../hooks/useAuth'
import Menu from './Menu'
import NotificationCenter from './NotificationCenter'
import '../../index.css'
import './Layout.css'

function Layout() {
    const { t, i18n } = useTranslation();
    const [collapsed, setCollapsed] = useState(false)
    const { signOut, getIdTokenClaims, isAuthenticated, loginEnabled } = useAuth()
    const [userInfo, setUserInfo] = useState({
        email: 'Guest',
        name: 'Guest',
    })

    const toggleLanguage = () => {
        const newLang = i18n.language.startsWith('zh') ? 'en' : 'zh';
        i18n.changeLanguage(newLang);
    };

    // Fetch user information when authenticated
    useEffect(() => {
        if (loginEnabled && isAuthenticated) {
            getIdTokenClaims().then((claims) => {
                setUserInfo({
                    email: claims?.email || 'User',
                    name: claims?.name || claims?.email || 'User',
                    username: claims?.username,
                })
            }).catch((error) => {
                console.error('Failed to get user claims:', error)
            })
        } else {
            setUserInfo({
                email: 'Guest',
                name: 'Guest',
            })
        }
    }, [isAuthenticated, getIdTokenClaims, loginEnabled])

    // Handle logout
    const handleLogout = () => {
        if (!loginEnabled) {
            return
        }
        const postLogoutRedirectUri = import.meta.env.VITE_LOGTO_POST_LOGOUT_REDIRECT_URI
        signOut(postLogoutRedirectUri)
    }

    // User menu items
    const userMenuItems = loginEnabled
        ? [
            {
                key: 'profile',
                label: userInfo?.email || 'User',
                icon: <UserOutlined />,
                disabled: true,
            },
            {
                type: 'divider',
            },
            {
                key: 'logout',
                label: t('auth.logout', 'Logout'),
                icon: <LogoutOutlined />,
                onClick: handleLogout,
                danger: true,
            },
        ]
        : [
            {
                key: 'profile',
                label: userInfo?.email || 'Guest',
                icon: <UserOutlined />,
                disabled: true,
            },
        ]

    return (
        <div className={`layout-container ${collapsed ? 'collapsed' : ''}`}>
            <div className="functional-bg-grid"></div>
            
            <Menu collapsed={collapsed} setCollapsed={setCollapsed} />

            <div className={`main-wrapper ${collapsed ? 'collapsed' : ''}`}>
                <header className="top-header">
                    <div className="header-title">
                        <h1>{t('app.pro_title')}</h1>
                    </div>
                    
                    <div className="header-actions">
                        <Space size="small">
                            <NotificationCenter />
                            
                            <button
                                className="btn-ghost"
                                onClick={toggleLanguage}
                                title="Switch Language"
                                style={{ display: 'flex', alignItems: 'center', gap: '0.5rem' }}
                            >
                                <GlobalOutlined />
                                {i18n.language.startsWith('zh') ? 'English' : '中文'}
                            </button>

                            <Dropdown menu={{ items: userMenuItems }} placement="bottomRight">
                                <Avatar
                                    icon={<UserOutlined />}
                                    style={{ cursor: 'pointer', backgroundColor: '#0ea5e9' }}
                                />
                            </Dropdown>
                        </Space>
                    </div>
                </header>

                <main className="content-area">
                    <Outlet />
                </main>
            </div>
        </div>
    )
}

export default Layout
