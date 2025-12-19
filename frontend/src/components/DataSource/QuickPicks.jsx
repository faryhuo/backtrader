import { useState } from 'react';
import PropTypes from 'prop-types';
import { useTranslation } from 'react-i18next';
import {
    StockOutlined,
    StarOutlined,
    StarFilled,
    HistoryOutlined,
    RiseOutlined
} from '@ant-design/icons';
import './QuickPicks.css';

function QuickPicks({ onSelectTicker, currentTicker }) {
    const { t } = useTranslation();
    const [watchlist, setWatchlist] = useState(() => {
        const saved = localStorage.getItem('ticker_watchlist');
        return saved ? JSON.parse(saved) : [];
    });
    const [recentSearches, setRecentSearches] = useState(() => {
        const saved = localStorage.getItem('recent_ticker_searches');
        return saved ? JSON.parse(saved) : [];
    });

    // Popular stocks configuration
    const popularStocks = [
        { symbol: 'AAPL', name: 'Apple' },
        { symbol: 'GOOGL', name: 'Google' },
        { symbol: 'MSFT', name: 'Microsoft' },
        { symbol: 'TSLA', name: 'Tesla' },
        { symbol: 'AMZN', name: 'Amazon' },
        { symbol: 'META', name: 'Meta' },
        { symbol: 'NVDA', name: 'NVIDIA' },
        { symbol: 'NFLX', name: 'Netflix' }
    ];

    // Major indices
    const majorIndices = [
        { symbol: 'SPY', name: 'S&P 500' },
        { symbol: 'QQQ', name: 'NASDAQ' },
        { symbol: 'DIA', name: 'Dow Jones' },
        { symbol: 'IWM', name: 'Russell 2000' }
    ];

    const handleTickerClick = (symbol) => {
        // Add to recent searches
        const updated = [symbol, ...recentSearches.filter(s => s !== symbol)].slice(0, 10);
        setRecentSearches(updated);
        localStorage.setItem('recent_ticker_searches', JSON.stringify(updated));

        onSelectTicker(symbol);
    };

    const toggleWatchlist = (symbol, e) => {
        e.stopPropagation();
        const isInWatchlist = watchlist.includes(symbol);
        const updated = isInWatchlist
            ? watchlist.filter(s => s !== symbol)
            : [...watchlist, symbol];

        setWatchlist(updated);
        localStorage.setItem('ticker_watchlist', JSON.stringify(updated));
    };

    const clearHistory = () => {
        setRecentSearches([]);
        localStorage.removeItem('recent_ticker_searches');
    };

    const isInWatchlist = (symbol) => watchlist.includes(symbol);

    return (
        <div className="quick-picks-container">
            {/* Popular Stocks */}
            <section className="quick-picks-section">
                <div className="section-header">
                    <h3>
                        <RiseOutlined /> {t('datasource.popular_stocks')}
                    </h3>
                </div>
                <div className="ticker-grid">
                    {popularStocks.map(stock => (
                        <button
                            key={stock.symbol}
                            className={`ticker-chip ${currentTicker === stock.symbol ? 'active' : ''}`}
                            onClick={() => handleTickerClick(stock.symbol)}
                        >
                            <div className="ticker-chip-content">
                                <span className="ticker-symbol">{stock.symbol}</span>
                                <span className="ticker-name">{stock.name}</span>
                            </div>
                            <button
                                className="watchlist-btn"
                                onClick={(e) => toggleWatchlist(stock.symbol, e)}
                                title={isInWatchlist(stock.symbol)
                                    ? t('datasource.remove_from_watchlist')
                                    : t('datasource.add_to_watchlist')}
                            >
                                {isInWatchlist(stock.symbol) ? <StarFilled /> : <StarOutlined />}
                            </button>
                        </button>
                    ))}
                </div>
            </section>

            {/* Major Indices */}
            <section className="quick-picks-section">
                <div className="section-header">
                    <h3>
                        <StockOutlined /> {t('datasource.major_indices')}
                    </h3>
                </div>
                <div className="ticker-grid indices-grid">
                    {majorIndices.map(index => (
                        <button
                            key={index.symbol}
                            className={`ticker-chip index-chip ${currentTicker === index.symbol ? 'active' : ''}`}
                            onClick={() => handleTickerClick(index.symbol)}
                        >
                            <div className="ticker-chip-content">
                                <span className="ticker-symbol">{index.symbol}</span>
                                <span className="ticker-name">{index.name}</span>
                            </div>
                            <button
                                className="watchlist-btn"
                                onClick={(e) => toggleWatchlist(index.symbol, e)}
                                title={isInWatchlist(index.symbol)
                                    ? t('datasource.remove_from_watchlist')
                                    : t('datasource.add_to_watchlist')}
                            >
                                {isInWatchlist(index.symbol) ? <StarFilled /> : <StarOutlined />}
                            </button>
                        </button>
                    ))}
                </div>
            </section>

            {/* Watchlist */}
            {watchlist.length > 0 && (
                <section className="quick-picks-section">
                    <div className="section-header">
                        <h3>
                            <StarFilled /> {t('datasource.watchlist')}
                        </h3>
                    </div>
                    <div className="ticker-grid">
                        {watchlist.map(symbol => (
                            <button
                                key={symbol}
                                className={`ticker-chip watchlist-chip ${currentTicker === symbol ? 'active' : ''}`}
                                onClick={() => handleTickerClick(symbol)}
                            >
                                <span className="ticker-symbol">{symbol}</span>
                                <button
                                    className="watchlist-btn remove"
                                    onClick={(e) => toggleWatchlist(symbol, e)}
                                    title={t('datasource.remove_from_watchlist')}
                                >
                                    <StarFilled />
                                </button>
                            </button>
                        ))}
                    </div>
                </section>
            )}

            {/* Recent Searches */}
            {recentSearches.length > 0 && (
                <section className="quick-picks-section">
                    <div className="section-header">
                        <h3>
                            <HistoryOutlined /> {t('datasource.recent_searches')}
                        </h3>
                        <button className="clear-btn" onClick={clearHistory}>
                            {t('datasource.clear_history')}
                        </button>
                    </div>
                    <div className="recent-searches-list">
                        {recentSearches.map(symbol => (
                            <button
                                key={symbol}
                                className={`recent-chip ${currentTicker === symbol ? 'active' : ''}`}
                                onClick={() => handleTickerClick(symbol)}
                            >
                                {symbol}
                            </button>
                        ))}
                    </div>
                </section>
            )}
        </div>
    );
}

QuickPicks.propTypes = {
    onSelectTicker: PropTypes.func.isRequired,
    currentTicker: PropTypes.string
};

export default QuickPicks;
