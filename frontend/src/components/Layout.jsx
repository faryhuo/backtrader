import { Link, useLocation } from 'react-router-dom'
import '../index.css'

function Layout({ children }) {
    const location = useLocation()

    return (
        <div className="layout-container">
            <aside className="sidebar">
                <div className="sidebar-header">
                    <h2>Backtrader</h2>
                </div>
                <nav className="sidebar-nav">
                    <Link
                        to="/"
                        className={`nav-item ${location.pathname === '/' ? 'active' : ''}`}
                    >
                        <span className="icon">📈</span>
                        Run Strategy
                    </Link>
                    <Link
                        to="/maintain"
                        className={`nav-item ${location.pathname === '/maintain' ? 'active' : ''}`}
                    >
                        <span className="icon">📝</span>
                        Strategy Maintain
                    </Link>
                </nav>
            </aside>

            <div className="main-wrapper">
                <header className="top-header">
                    <div className="header-title">
                        <h1>Backtrader Pro</h1>
                    </div>
                    <div className="user-profile">
                        <div className="user-info">
                            <span className="user-name">Trader</span>
                            <span className="user-role">Admin</span>
                        </div>
                        <div className="user-avatar">
                            <span>T</span>
                        </div>
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
