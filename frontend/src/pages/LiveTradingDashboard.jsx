import { Layout, Card, Space, Typography, Badge, Tag, Divider, message } from 'antd';
import { DollarOutlined, RiseOutlined, FallOutlined, DashboardOutlined, ThunderboltOutlined } from '@ant-design/icons';
import { useEffect, useMemo, useState } from 'react';
import { useTranslation } from 'react-i18next';
import LiveConfigForm from '../components/LiveTrading/LiveConfigForm';
import LiveCredentialPanel from '../components/LiveTrading/LiveCredentialPanel';
import SessionControls from '../components/LiveTrading/SessionControls';
import PositionTable from '../components/LiveTrading/PositionTable';
import OrderLog from '../components/LiveTrading/OrderLog';
import OrderBookPanel from '../components/LiveTrading/OrderBookPanel';
import PnLChart from '../components/LiveTrading/PnLChart';
import PriceChart from '../components/LiveTrading/PriceChart';
import StrategyLog from '../components/LiveTrading/StrategyLog';
import TradeErrorPanel from '../components/LiveTrading/TradeErrorPanel';
import { api } from '../services/api';
import { useLiveTrading } from '../hooks/useLiveTrading';
import './LiveTradingDashboard.css';

const { Content } = Layout;
const { Title, Text } = Typography;

function formatMoney(value) {
  const amount = Number(value ?? 0);
  return `$${amount.toLocaleString(undefined, {
    minimumFractionDigits: 2,
    maximumFractionDigits: 2,
  })}`;
}

function getPnlTone(value) {
  if (value > 0) return 'positive';
  if (value < 0) return 'negative';
  return 'neutral';
}

export default function LiveTradingDashboard() {
  const { t } = useTranslation();
  const [credentialLoading, setCredentialLoading] = useState(false);
  const [testingMode, setTestingMode] = useState(null);
  const [paperTestUrl, setPaperTestUrl] = useState('https://testnet.binance.vision');
  const [credentialState, setCredentialState] = useState({
    paper: { api_key: '', secret: '' },
    live: { api_key: '', secret: '' },
  });
  const {
    session,
    loading,
    positions,
    orders,
    orderBook,
    recentErrors,
    pnlHistory,
    currentPnl,
    portfolioValue,
    cash,
    ticker,
    prevTicker,
    openPrice,
    priceHistory,
    stats,
    logs,
    feedStatus,
    wsConnected,
    handleStartSession,
    handleStopSession,
    handleRefreshSession,
    handleCancelOrder,
    handleOrderBookDepthChange,
  } = useLiveTrading();

  useEffect(() => {
    const loadLauncherConfig = async () => {
      try {
        const [credentialsResponse, liveConfigResponse] = await Promise.all([
          api.getCredentials(),
          api.getConfig(),
        ]);
        const ccxt = credentialsResponse?.credentials?.ccxt || {};
        setCredentialState({
          paper: {
            api_key: ccxt?.binance?.paper?.api_key || '',
            secret: ccxt?.binance?.paper?.secret || '',
          },
          live: {
            api_key: ccxt?.binance?.live?.api_key || '',
            secret: ccxt?.binance?.live?.secret || '',
          },
        });
        setPaperTestUrl(liveConfigResponse?.paper_test_url || 'https://testnet.binance.vision');
      } catch (error) {
        message.error(error.message || t('live.config.load_failed', 'Failed to load trading access configuration'));
      }
    };

    loadLauncherConfig();
  }, [t]);

  const handleCredentialChange = (mode, field, value) => {
    setCredentialState((prev) => ({
      ...prev,
      [mode]: {
        ...prev[mode],
        [field]: value,
      },
    }));
  };

  const handleSaveCredentials = async (mode) => {
    try {
      setCredentialLoading(true);
      await api.updateCCXTCredentials('binance', mode, credentialState[mode]);
      message.success(t('live.config.credentials_saved', 'Trading credentials saved'));
    } catch (error) {
      message.error(error.message || t('live.config.save_failed', 'Failed to save trading access configuration'));
    } finally {
      setCredentialLoading(false);
    }
  };

  const handleTestCredentials = async (mode) => {
    try {
      setTestingMode(mode);
      const response = await api.testCredential('ccxt', {
        exchange: 'binance',
        mode,
        api_key: credentialState[mode]?.api_key,
        secret: credentialState[mode]?.secret,
        use_testnet: mode === 'paper',
      });
      if (response?.valid) {
        message.success(response.message || t('live.config.test_success', 'Connection test succeeded'));
      } else {
        message.error(response?.message || t('live.config.test_failed', 'Connection test failed'));
      }
    } catch (error) {
      message.error(error.message || t('live.config.test_failed', 'Connection test failed'));
    } finally {
      setTestingMode(null);
    }
  };

  const handleSavePaperTestUrl = async () => {
    try {
      setCredentialLoading(true);
      const response = await api.updateConfig({ paper_test_url: paperTestUrl });
      setPaperTestUrl(response?.paper_test_url || paperTestUrl);
      message.success(t('live.config.test_url_saved', 'Paper test URL saved'));
    } catch (error) {
      message.error(error.message || t('live.config.save_failed', 'Failed to save trading access configuration'));
    } finally {
      setCredentialLoading(false);
    }
  };

  const isSessionActive = session && !['stopped', 'error'].includes(session.status);

  const priceChange = ticker && openPrice
    ? ticker.last - openPrice
    : ticker && prevTicker
      ? ticker.last - prevTicker.last
      : 0;
  const priceChangePercent = ticker && openPrice && openPrice > 0
    ? ((ticker.last - openPrice) / openPrice) * 100
    : ticker && prevTicker && prevTicker.last
      ? ((ticker.last - prevTicker.last) / prevTicker.last) * 100
      : 0;
  const isPriceUp = priceChange >= 0;

  const sessionFilledOrders = useMemo(
    () => orders.filter((order) => order.status === 'filled' && order?.metadata?.in_session !== false),
    [orders],
  );

  const totalFeesByAsset = useMemo(() => {
    const feeMap = new Map();
    sessionFilledOrders.forEach((order) => {
      const fee = Number(order.fee ?? 0);
      if (!Number.isFinite(fee) || fee <= 0) return;
      const asset = order.fee_asset || 'QUOTE';
      feeMap.set(asset, (feeMap.get(asset) || 0) + fee);
    });
    return [...feeMap.entries()];
  }, [sessionFilledOrders]);

  const totalFeesDisplay = totalFeesByAsset.length > 0
    ? totalFeesByAsset.map(([asset, fee]) => `${fee.toFixed(8)} ${asset}`).join(' + ')
    : t('live.total_fees_empty', 'No fees yet');
  const sessionMarket = session?.market || 'spot';
  const pnlTone = getPnlTone(currentPnl);
  const pnlLabel = pnlTone === 'positive'
    ? t('live.session_profit', 'Session Profit')
    : pnlTone === 'negative'
      ? t('live.session_loss', 'Session Loss')
      : t('live.break_even', 'Break Even');

  const runtimeSummary = [
    {
      label: t('live.portfolio_value', 'Portfolio Value'),
      value: formatMoney(portfolioValue),
      tone: 'neutral',
      icon: <DollarOutlined />,
    },
    {
      label: t('live.cash_balance', 'Cash Balance'),
      value: formatMoney(cash),
      tone: 'neutral',
      icon: <DollarOutlined />,
    },
    {
      label: pnlLabel,
      value: formatMoney(currentPnl),
      tone: pnlTone,
      icon: pnlTone === 'positive' ? <RiseOutlined /> : pnlTone === 'negative' ? <FallOutlined /> : <DollarOutlined />,
    },
    {
      label: t('live.total_fees', 'Total Fees'),
      value: totalFeesDisplay,
      tone: 'warning',
      icon: <ThunderboltOutlined />,
      meta: `${t('live.total_trades', 'Total Trades')}: ${stats.totalTrades}${stats.totalTrades > 0 ? ` (${stats.winRate.toFixed(1)}% ${t('live.win_rate', 'win')})` : ''}`,
    },
  ];

  return (
    <Layout>
      <Content className="dashboard-shell">
        <div className="dashboard-topbar">
          <div>
            <Space align="center" size={12}>
              <div className="dashboard-brand">
                <DashboardOutlined />
              </div>
              <div>
                <Text className="dashboard-kicker">
                  {t('live.form.eyebrow', 'Session Launcher')}
                </Text>
                <Title level={2} className="dashboard-title">
                  {t('live.dashboard_title', 'Binance Trading')}
                </Title>
              </div>
            </Space>
            <Text className="dashboard-subtitle">
              {t('live.dashboard_subtitle', 'Confirm the market, execution mode, and exchange-backed capital source before the engine starts trading.')}
            </Text>
          </div>

          <div className="dashboard-statusbar">
            <div className="dashboard-connection">
              <Badge status={wsConnected ? 'success' : 'error'} />
              <span>{wsConnected ? t('live.connected', 'Connected') : t('live.disconnected', 'Disconnected')}</span>
            </div>
            {session?.mode && (
              <Tag color={session.mode === 'live' ? 'red' : 'blue'} style={{ margin: 0 }}>
                {(session.mode || '').toUpperCase()}
              </Tag>
            )}
            <Tag color={sessionMarket === 'futures' ? 'purple' : 'geekblue'} style={{ margin: 0 }}>
              {t(`live.form.market_${sessionMarket}`, sessionMarket).toUpperCase()}
            </Tag>
            {feedStatus && (
              <Tag color={feedStatus === 'live' ? 'green' : 'gold'} style={{ margin: 0 }}>
                {feedStatus === 'live' ? t('live.live_feed', 'Live Feed') : t('live.warming_up', 'Warming Up')}
              </Tag>
            )}
          </div>
        </div>

        {!isSessionActive ? (
          <div className="dashboard-launch-shell">
            <div className="dashboard-chart-stack" style={{ marginBottom: 18 }}>
              <LiveCredentialPanel
                paperCredentials={credentialState.paper}
                liveCredentials={credentialState.live}
                paperTestUrl={paperTestUrl}
                loading={credentialLoading}
                testingKey={testingMode}
                onCredentialChange={handleCredentialChange}
                onPaperTestUrlChange={setPaperTestUrl}
                onSaveCredentials={handleSaveCredentials}
                onTestCredentials={handleTestCredentials}
                onSavePaperTestUrl={handleSavePaperTestUrl}
              />
            </div>
            <Card className="dashboard-panel dashboard-launch-panel" bordered={false}>
              <LiveConfigForm onSubmit={handleStartSession} loading={loading} />
            </Card>
          </div>
        ) : (
          <div className="dashboard-layout">
            <div className="dashboard-main">
              <Card className="dashboard-panel dashboard-overview-panel" bordered={false}>
                <div className="dashboard-overview-grid">
                  <div className="dashboard-session-zone">
                    <Text className="dashboard-section-label">
                      {t('live.live_feed', 'Live Feed')}
                    </Text>
                    <SessionControls
                      session={session}
                      ticker={ticker}
                      feedStatus={feedStatus}
                      onStop={handleStopSession}
                      onRefresh={handleRefreshSession}
                      loading={loading}
                    />
                  </div>

                  <div className="dashboard-market-zone">
                    <Text className="dashboard-section-label">
                      {t('live.price_chart', 'Price Chart')}
                    </Text>
                    {ticker?.last ? (
                      <>
                        <div className="dashboard-market-price">
                          {session.symbol} {formatMoney(ticker.last)}
                        </div>
                        <div className={`dashboard-market-change ${isPriceUp ? 'positive' : 'negative'}`}>
                          {isPriceUp ? '+' : ''}{priceChange.toFixed(2)} ({isPriceUp ? '+' : ''}{priceChangePercent.toFixed(2)}%)
                        </div>
                        <Text className="dashboard-market-meta">
                          Bid {formatMoney(ticker.bid)} | Ask {formatMoney(ticker.ask)}
                        </Text>
                      </>
                    ) : (
                      <Text className="dashboard-market-meta">
                        {t('live.waiting_for_price_data', 'Waiting for price data...')}
                      </Text>
                    )}
                  </div>
                </div>
              </Card>

              <div className="dashboard-metric-grid">
                {runtimeSummary.map((item) => (
                  <Card key={item.label} className={`dashboard-panel metric-panel metric-${item.tone}`} bordered={false}>
                    <div className="metric-head">
                      <span className="metric-icon">{item.icon}</span>
                      <Text className="metric-label">{item.label}</Text>
                    </div>
                    <div className="metric-value">{item.value}</div>
                    {item.meta ? <Text className="metric-meta">{item.meta}</Text> : null}
                  </Card>
                ))}
              </div>

              <div className="dashboard-chart-stack">
                <Card className="dashboard-panel dashboard-chart-panel" title={t('live.price_chart', 'Price Chart')} bordered={false}>
                  <div className="dashboard-combined-chart">
                    <div className="dashboard-combined-price-chart">
                      <Text className="dashboard-section-label">
                        {t('live.price_chart', 'Price Chart')}
                      </Text>
                      <PriceChart
                        priceHistory={priceHistory}
                        currentPrice={ticker?.last}
                        symbol={session?.symbol}
                        timeframe={session?.timeframe}
                        ticker={ticker}
                        openPrice={openPrice}
                        prevTicker={prevTicker}
                      />
                    </div>

                    <div className="dashboard-combined-order-book">
                      <Text className="dashboard-section-label">
                        {t('live.order_book.title', 'Order Book')}
                      </Text>
                      <OrderBookPanel
                        orderBook={orderBook}
                        onDepthChange={handleOrderBookDepthChange}
                      />
                    </div>
                  </div>
                </Card>

                <Card className="dashboard-panel dashboard-chart-panel" title={t('live.performance', 'Performance')} bordered={false}>
                  <PnLChart
                    pnlHistory={pnlHistory}
                    currentPnl={currentPnl}
                    portfolioValue={portfolioValue}
                    totalFeesDisplay={totalFeesDisplay}
                  />
                </Card>
              </div>
            </div>

            <div className="dashboard-sidebar">
              <Card className="dashboard-panel dashboard-side-panel" bordered={false}>
                <Text className="dashboard-section-label">{t('live.open_positions', 'Open Positions')}</Text>
                <Divider className="dashboard-divider" />
                <PositionTable positions={positions} ticker={ticker} />
              </Card>

              <Card className="dashboard-panel dashboard-side-panel" bordered={false}>
                <Text className="dashboard-section-label">{t('live.errors.title', 'Recent Trading Errors')}</Text>
                <Divider className="dashboard-divider" />
                <TradeErrorPanel errors={recentErrors} />
              </Card>

              <Card className="dashboard-panel dashboard-side-panel dashboard-orders-panel" bordered={false}>
                <Text className="dashboard-section-label">{t('live.order_history', 'Orders')}</Text>
                <Divider className="dashboard-divider" />
                <div className="dashboard-orders-scroll">
                  <OrderLog orders={orders} onCancelOrder={handleCancelOrder} />
                </div>
              </Card>

              <Card className="dashboard-panel dashboard-side-panel" bordered={false}>
                <Text className="dashboard-section-label">{t('live.strategy_log', 'Strategy Log')}</Text>
                <Divider className="dashboard-divider" />
                <StrategyLog logs={logs} />
              </Card>
            </div>
          </div>
        )}
      </Content>
    </Layout>
  );
}
