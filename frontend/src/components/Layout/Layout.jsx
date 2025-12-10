import { useState, useEffect } from 'react'
import { Link, useLocation } from 'react-router-dom'
import { useTranslation } from 'react-i18next'
import { useLogto } from '@logto/react'
import { Dropdown, Avatar, Space } from 'antd'
import { UserOutlined, LogoutOutlined } from '@ant-design/icons'
import '../../index.css'

function Layout({ children }) {
    const { t, i18n } = useTranslation();
    const location = useLocation()
    const [collapsed, setCollapsed] = useState(false)
    const { signOut, getIdTokenClaims, isAuthenticated } = useLogto()
    const [userInfo, setUserInfo] = useState(null)

    const toggleLanguage = () => {
        const newLang = i18n.language.startsWith('zh') ? 'en' : 'zh';
        i18n.changeLanguage(newLang);
    };

    // Fetch user information when authenticated
    useEffect(() => {
        if (isAuthenticated) {
            getIdTokenClaims().then((claims) => {
                setUserInfo({
                    email: claims?.email || 'User',
                    name: claims?.name || claims?.email || 'User',
                    username: claims?.username,
                })
            }).catch((error) => {
                console.error('Failed to get user claims:', error)
            })
        }
    }, [isAuthenticated, getIdTokenClaims])

    // Handle logout
    const handleLogout = () => {
        const postLogoutRedirectUri = import.meta.env.VITE_LOGTO_POST_LOGOUT_REDIRECT_URI
        signOut(postLogoutRedirectUri)
    }

    // User menu items
    const userMenuItems = [
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

    return (
        <div className={`layout-container ${collapsed ? 'collapsed' : ''}`}>
            <aside className={`sidebar ${collapsed ? 'collapsed' : ''}`}>
                <div className="sidebar-header">
                    {!collapsed && <h2>{t('app.title')}</h2>}
                </div>
                <nav className="sidebar-nav">
                    <Link
                        to="/app"
                        className={`nav-item ${location.pathname === '/app' ? 'active' : ''}`}
                        title={t('nav.run_strategy')}
                    >
                        <span className="icon">📈</span>
                        {!collapsed && <span>{t('nav.run_strategy')}</span>}
                    </Link>
                    <Link
                        to="/app/maintain"
                        className={`nav-item ${location.pathname === '/app/maintain' ? 'active' : ''}`}
                        title={t('nav.strategy_maintain')}
                    >
                        <span className="icon">📝</span>
                        {!collapsed && <span>{t('nav.strategy_maintain')}</span>}
                    </Link>
                    <Link
                        to="/app/datasource"
                        className={`nav-item ${location.pathname === '/app/datasource' ? 'active' : ''}`}
                        title={t('nav.datasource')}
                    >
                        <span className="icon">📊</span>
                        {!collapsed && <span>{t('nav.datasource')}</span>}
                    </Link>
                </nav>
                <div className="sidebar-footer">
                    <button
                        className="collapse-toggle"
                        onClick={() => setCollapsed(!collapsed)}
                        title={collapsed ? t('common.expand_sidebar') : t('common.collapse_sidebar')}
                    >
                        {collapsed ? '»' : '«'}
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
                            >
                                {i18n.language.startsWith('zh') ? 'English' : '中文'}
                            </button>

                            <Dropdown menu={{ items: userMenuItems }} placement="bottomRight">
                                <Avatar
                                    icon={<UserOutlined />}
                                    style={{ cursor: 'pointer', backgroundColor: '#1890ff' }}
                                />
                            </Dropdown>
                        </Space>
                    </div>
                </header>

                <main className="content-area">
                    {children}
                </main>
            </div>
        </div>
    )
}

export default Layout
