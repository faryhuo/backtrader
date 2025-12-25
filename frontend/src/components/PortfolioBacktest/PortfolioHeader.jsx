import { PieChartOutlined } from '@ant-design/icons';

/**
 * Header component for Portfolio Backtest page
 */
function PortfolioHeader({ t }) {
    return (
        <div className="portfolio-header">
            <h2><PieChartOutlined /> {t('portfolio.title', 'Portfolio Backtest')}</h2>
            <p>{t('portfolio.description', 'Run backtests on multiple assets with custom weight allocation')}</p>
        </div>
    );
}

export default PortfolioHeader;
