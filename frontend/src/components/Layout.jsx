import { useState } from 'react'
import { Link, useLocation } from 'react-router-dom'
import '../index.css'

function Layout({ children }) {
    const location = useLocation()
    const [collapsed, setCollapsed] = useState(false)

    return (
        <div className={`layout-container ${collapsed ? 'collapsed' : ''}`}>
            <aside className={`sidebar ${collapsed ? 'collapsed' : ''}`}>
                <div className="sidebar-header">
                    {!collapsed && <h2>Backtrader</h2>}
                </div>
                <nav className="sidebar-nav">
                    <Link
                        to="/"
                        className={`nav-item ${location.pathname === '/' ? 'active' : ''}`}
                        title="Run Strategy"
                    >
                        <span className="icon">📈</span>
                        {!collapsed && <span>Run Strategy</span>}
                    </Link>
                    <Link
                        to="/maintain"
                        className={`nav-item ${location.pathname === '/maintain' ? 'active' : ''}`}
                        title="Strategy Maintain"
                    >
                        <span className="icon">📝</span>
                        {!collapsed && <span>Strategy Maintain</span>}
                    </Link>
                </nav>
                <div className="sidebar-footer">
                    <button
                        className="collapse-toggle"
                        onClick={() => setCollapsed(!collapsed)}
                        title={collapsed ? "Expand Sidebar" : "Collapse Sidebar"}
                    >
                        {collapsed ? '»' : '«'}
                    </button>
                </div>
            </aside>

            <div className={`main-wrapper ${collapsed ? 'collapsed' : ''}`}>
                <header className="top-header">
                    <div className="header-title">
                        <h1>Backtrader Pro</h1>
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
