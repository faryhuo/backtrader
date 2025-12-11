import { Link, useLocation } from 'react-router-dom'
import { useTranslation } from 'react-i18next'
import {
    FundOutlined,
    CodeOutlined,
    DatabaseOutlined,
    ThunderboltOutlined,
    MenuFoldOutlined,
    MenuUnfoldOutlined
} from '@ant-design/icons'
import './Menu.css'

const Menu = ({ collapsed, setCollapsed }) => {
    const { t } = useTranslation()
    const location = useLocation()

    const getNavClass = (path) => {
        const current = location.pathname
        // Exact match for root strategy path
        if (path === '/strategy') {
            return current === '/strategy' || current === '/' ? 'nav-item active' : 'nav-item'
        }
        return current.startsWith(path) ? 'nav-item active' : 'nav-item'
    }

    return (
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
                <Link
                    to="/live"
                    className={getNavClass('/live')}
                    title={t('nav.live_trading', 'Live Trading')}
                >
                    <span className="icon"><ThunderboltOutlined /></span>
                    {!collapsed && <span>{t('nav.live_trading', 'Live Trading')}</span>}
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
    )
}

export default Menu
