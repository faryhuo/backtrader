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
    const isZh = i18n.language.startsWith('zh');
    const [userInfo, setUserInfo] = useState({
        email: null,
        name: null,
    })

    const toggleLanguage = () => {
        const newLang = isZh ? 'en' : 'zh';
        i18n.changeLanguage(newLang);
    };

    // Fetch user information when authenticated
    useEffect(() => {
        if (loginEnabled && isAuthenticated) {
            getIdTokenClaims().then((claims) => {
                setUserInfo({
                    email: claims?.email || null,
                    name: claims?.name || claims?.email || null,
                    username: claims?.username,
                })
            }).catch((error) => {
                console.error('Failed to get user claims:', error)
            })
        } else {
            setUserInfo({
                email: null,
                name: null,
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
                label: userInfo?.email || t('common.user', 'User'),
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
                label: userInfo?.email || t('common.guest', 'Guest'),
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
                    </div>

                    <div className="header-actions">
                        <Space size="small">
                            <NotificationCenter />

                            <button
                                className="btn-ghost"
                                onClick={toggleLanguage}
                                title={t('common.language.switch_title', 'Switch Language')}
                                style={{ display: 'flex', alignItems: 'center', gap: '0.5rem' }}
                            >
                                <GlobalOutlined />
                                {isZh ? t('common.language.switch_to_en', 'English') : t('common.language.switch_to_zh', '中文')}
                            </button>

                            <Dropdown menu={{ items: userMenuItems }} placement="bottomRight">
                                <Avatar
                                    icon={<UserOutlined />}
                                    style={{ cursor: 'pointer', backgroundColor: '#22d3ee' }}
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
