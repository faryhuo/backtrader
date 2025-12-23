import { Link, useLocation } from 'react-router-dom'
import { useTranslation } from 'react-i18next'
import {
    FundOutlined,
    CodeOutlined,
    DatabaseOutlined,
    HistoryOutlined,
    ExperimentOutlined,
    PieChartOutlined,
    ThunderboltOutlined,
    CloudServerOutlined,
    UnorderedListOutlined,
    FileTextOutlined,
    SettingOutlined,
    MenuFoldOutlined,
    MenuUnfoldOutlined
} from '@ant-design/icons'
import './Menu.css'
import { TrendingUp } from 'lucide-react'

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
                <div className="header-logo-icon">
                    <TrendingUp size={20} />
                </div>
                {!collapsed && <div className="header-title">
                    <a href="/" className="header-logo-link">
                        <h1>{t('app.title')}<span className="text-gradient">Pro</span></h1>
                    </a>
                </div>}
            </div>
            <nav className="sidebar-nav">
                {/* Strategy & Trading Group */}
                {!collapsed && <div className="nav-group-header">{t('nav.group_strategy')}</div>}
                <Link
                    to="/maintain"
                    className={getNavClass('/maintain')}
                    title={t('nav.strategy_maintain')}
                >
                    <span className="icon"><CodeOutlined /></span>
                    {!collapsed && <span>{t('nav.strategy_maintain')}</span>}
                </Link>
                <Link to="/strategy" className={getNavClass('/strategy')} title={t('nav.run_strategy')}>
                    <span className="icon"><FundOutlined /></span>
                    {!collapsed && <span>{t('nav.run_strategy')}</span>}
                </Link>
                <Link
                    to="/live"
                    className={getNavClass('/live')}
                    title={t('nav.live_trading', 'Live Trading')}
                >
                    <span className="icon"><ThunderboltOutlined /></span>
                    {!collapsed && <span>{t('nav.live_trading', 'Live Trading')}</span>}
                </Link>

                {/* Analysis & Optimization Group */}
                {!collapsed && <div className="nav-group-header">{t('nav.group_analysis')}</div>}
                <Link
                    to="/history"
                    className={getNavClass('/history')}
                    title={t('nav.history')}
                >
                    <span className="icon"><HistoryOutlined /></span>
                    {!collapsed && <span>{t('nav.history')}</span>}
                </Link>
                <Link
                    to="/walkforward"
                    className={getNavClass('/walkforward')}
                    title={t('nav.walkforward')}
                >
                    <span className="icon"><ExperimentOutlined /></span>
                    {!collapsed && <span>{t('nav.walkforward')}</span>}
                </Link>
                <Link
                    to="/portfolio"
                    className={getNavClass('/portfolio')}
                    title={t('nav.portfolio', 'Portfolio')}
                >
                    <span className="icon"><PieChartOutlined /></span>
                    {!collapsed && <span>{t('nav.portfolio', 'Portfolio')}</span>}
                </Link>

                {/* Infrastructure Group */}
                {!collapsed && <div className="nav-group-header">{t('nav.group_infrastructure')}</div>}
                <Link
                    to="/datasource"
                    className={getNavClass('/datasource')}
                    title={t('nav.datasource')}
                >
                    <span className="icon"><DatabaseOutlined /></span>
                    {!collapsed && <span>{t('nav.datasource')}</span>}
                </Link>
                <Link
                    to="/data_management"
                    className={getNavClass('/data_management')}
                    title={t('nav.data_management', 'Data Management')}
                >
                    <span className="icon"><CloudServerOutlined /></span>
                    {!collapsed && <span>{t('nav.data_management', 'Data Management')}</span>}
                </Link>
                <Link
                    to="/tasks"
                    className={getNavClass('/tasks')}
                    title={t('nav.task_center', 'Task Center')}
                >
                    <span className="icon"><UnorderedListOutlined /></span>
                    {!collapsed && <span>{t('nav.task_center', 'Task Center')}</span>}
                </Link>
                <Link
                    to="/reports"
                    className={getNavClass('/reports')}
                    title={t('nav.reports', 'Reports')}
                >
                    <span className="icon"><FileTextOutlined /></span>
                    {!collapsed && <span>{t('nav.reports', 'Reports')}</span>}
                </Link>
                <Link
                    to="/settings"
                    className={getNavClass('/settings')}
                    title={t('nav.settings', 'Settings')}
                >
                    <span className="icon"><SettingOutlined /></span>
                    {!collapsed && <span>{t('nav.settings', 'Settings')}</span>}
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
