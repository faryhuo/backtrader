import { Tabs } from 'antd';
import {
    BarChartOutlined,
    StockOutlined,
    CodeOutlined,
    CalendarOutlined,
    DollarOutlined
} from '@ant-design/icons';

/**
 * Results section with header card and tabs
 * Displays backtest results with parameters summary and tab navigation
 */
function ResultsHeader({ t, ticker, selectedStrategy, startDate, endDate, initialCash, paramOverrides, tabItems }) {
    return (
        <div className="results-animate-in">
            <div className="backtest-header-card">
                <div className="backtest-header-icon">
                    <BarChartOutlined />
                </div>
                <div className="backtest-header-content">
                    <h2 className="backtest-header-title">{t('history.backtest_results', 'Backtest Results')}</h2>
                    <div className="backtest-header-meta">
                        <div className="backtest-meta-item">
                            <StockOutlined />
                            <span className="backtest-meta-value">{ticker}</span>
                        </div>
                        <div className="backtest-meta-item">
                            <CodeOutlined />
                            <span className="backtest-meta-value">{selectedStrategy}</span>
                        </div>
                        <div className="backtest-meta-item">
                            <CalendarOutlined />
                            <span className="backtest-meta-value">{startDate} ~ {endDate}</span>
                        </div>
                        <div className="backtest-meta-item">
                            <DollarOutlined />
                            <span className="backtest-meta-value">${parseFloat(initialCash).toLocaleString()}</span>
                        </div>
                    </div>
                    {paramOverrides && Object.keys(paramOverrides).length > 0 && (
                        <div className="param-pills">
                            {Object.entries(paramOverrides).map(([key, value]) => (
                                <span key={key} className="param-pill">
                                    <span className="param-pill-key">{key}:</span>
                                    {typeof value === 'number' ? value.toLocaleString() : String(value)}
                                </span>
                            ))}
                        </div>
                    )}
                </div>
            </div>

            <Tabs
                defaultActiveKey="overview"
                className="strategy-results-tabs"
                items={tabItems}
            />
        </div>
    );
}

export default ResultsHeader;
