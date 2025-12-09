import { useState } from 'react'
import { Link, useLocation } from 'react-router-dom'
import { useTranslation } from 'react-i18next'
import '../../index.css'

function Layout({ children }) {
    const { t, i18n } = useTranslation();
    const location = useLocation()
    const [collapsed, setCollapsed] = useState(false)

    const toggleLanguage = () => {
        const newLang = i18n.language.startsWith('zh') ? 'en' : 'zh';
        i18n.changeLanguage(newLang);
    };

    return (
        <div className={`layout-container ${collapsed ? 'collapsed' : ''}`}>
            <aside className={`sidebar ${collapsed ? 'collapsed' : ''}`}>
                <div className="sidebar-header">
                    {!collapsed && <h2>{t('app.title')}</h2>}
                </div>
                <nav className="sidebar-nav">
                    <Link
                        to="/"
                        className={`nav-item ${location.pathname === '/' ? 'active' : ''}`}
                        title={t('nav.run_strategy')}
                    >
                        <span className="icon">📈</span>
                        {!collapsed && <span>{t('nav.run_strategy')}</span>}
                    </Link>
                    <Link
                        to="/maintain"
                        className={`nav-item ${location.pathname === '/maintain' ? 'active' : ''}`}
                        title={t('nav.strategy_maintain')}
                    >
                        <span className="icon">📝</span>
                        {!collapsed && <span>{t('nav.strategy_maintain')}</span>}
                    </Link>
                    <Link
                        to="/datasource"
                        className={`nav-item ${location.pathname === '/datasource' ? 'active' : ''}`}
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
                         <button 
                            className="btn-ghost" 
                            onClick={toggleLanguage}
                            title="Switch Language"
                        >
                            {i18n.language.startsWith('zh') ? 'English' : '中文'}
                        </button>
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
