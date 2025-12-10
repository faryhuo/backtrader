import { useState, useEffect } from 'react'
import { Link, useLocation, Outlet } from 'react-router-dom'
import { useTranslation } from 'react-i18next'
import { Dropdown, Avatar, Space } from 'antd'
import {
    UserOutlined,
    LogoutOutlined,
    FundOutlined,
    CodeOutlined,
    DatabaseOutlined,
    MenuFoldOutlined,
    MenuUnfoldOutlined,
    GlobalOutlined
} from '@ant-design/icons'
import { useAuth } from '../../hooks/useAuth'
import '../../index.css'

function Layout() {
    const { t, i18n } = useTranslation();
    const location = useLocation()
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

    const getNavClass = (path) => {
        const current = location.pathname
        // Exact match for root strategy path
        if (path === '/strategy') {
            return current === '/strategy' || current === '/' ? 'nav-item active' : 'nav-item'
        }
        return current.startsWith(path) ? 'nav-item active' : 'nav-item'
    }

    return (
        <div className={`layout-container ${collapsed ? 'collapsed' : ''}`}>
            <aside className={`sidebar ${collapsed ? 'collapsed' : ''}`}>
                <div className="sidebar-header">
                    {!collapsed && <h2>{t('app.title')}</h2>}
                </div>
                <nav className="sidebar-nav">
                    <Link to="/strategy" className={getNavClass('/strategy')} title={t('nav.run_strategy')}>
                        <span className="icon"><FundOutlined /></span>
                        {!collapsed && <span>{t('nav.run_strategy')}</span>}
                    </Link>
                    <Link
                        to="/maintain"
                        className={getNavClass('/maintain')}
                        title={t('nav.strategy_maintain')}
                    >
                        <span className="icon"><CodeOutlined /></span>
                        {!collapsed && <span>{t('nav.strategy_maintain')}</span>}
                    </Link>
                    <Link
                        to="/datasource"
                        className={getNavClass('/datasource')}
                        title={t('nav.datasource')}
                    >
                        <span className="icon"><DatabaseOutlined /></span>
                        {!collapsed && <span>{t('nav.datasource')}</span>}
                    </Link>
                </nav>
                <div className="sidebar-footer">
                    <button
                        className="collapse-toggle"
                        onClick={() => setCollapsed(!collapsed)}
                        title={collapsed ? t('common.expand_sidebar') : t('common.collapse_sidebar')}
                    >
                        {collapsed ? <MenuUnfoldOutlined /> : <MenuFoldOutlined />}
                    </button>
                </div>
            </aside>

            <div className={`main-wrapper ${collapsed ? 'collapsed' : ''}`}>
                <header className="top-header">
                    <div className="header-title">
                        <h1>{t('app.pro_title')}</h1>
                    </div>
                    <div className="header-actions">
                        <Space size="middle">
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
