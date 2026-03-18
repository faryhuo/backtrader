import { Layout, Row, Col, Card, Statistic, Space, Typography, Badge } from 'antd';
import { DollarOutlined, RiseOutlined, FallOutlined, ThunderboltOutlined, DashboardOutlined } from '@ant-design/icons';
import { useTranslation } from 'react-i18next';
import LiveConfigForm from '../components/LiveTrading/LiveConfigForm';
import SessionControls from '../components/LiveTrading/SessionControls';
import PositionTable from '../components/LiveTrading/PositionTable';
import OrderLog from '../components/LiveTrading/OrderLog';
import PnLChart from '../components/LiveTrading/PnLChart';
import PriceChart from '../components/LiveTrading/PriceChart';
import StrategyLog from '../components/LiveTrading/StrategyLog';
import { useLiveTrading } from '../hooks/useLiveTrading';
import './LiveTradingDashboard.css';

const { Content } = Layout;
const { Title, Text } = Typography;

/**
 * Binance Spot Trading Dashboard
 * Full rewrite with ticker display, order cancellation, and improved layout
 */
const LiveTradingDashboard = () => {
  const { t } = useTranslation();
  const {
    session,
    loading,
    positions,
    orders,
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
    wsConnected,
    handleStartSession,
    handleStopSession,
    handleRefreshSession,
    handleCancelOrder,
  } = useLiveTrading();

  // Calculate price change (vs opening price)
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

  const isSessionActive = session && !['stopped', 'error'].includes(session.status);

  return (
    <Layout>
      <Content className="dashboard-container">
        {/* Header */}
        <div className="dashboard-header">
          <Space align="center">
            <DashboardOutlined style={{ fontSize: '24px', color: '#38bdf8' }} />
            <Title level={2} className="dashboard-title" style={{ margin: 0 }}>
              {t('live.dashboard_title', 'Binance Spot Trading')}
            </Title>
          </Space>
          <div style={{ marginTop: 8 }}>
            <Text className="dashboard-subtitle">
              {t('live.dashboard_subtitle', 'Real-time trading with strategy automation')}
            </Text>
          </div>
        </div>

        {!isSessionActive ? (
          /* ──── Config Form (no active session) ──── */
          <Row justify="center" style={{ marginTop: 40 }}>
            <Col xs={24} lg={16} xl={12}>
              <Card className="dashboard-card" title={t('live.start_new_session', 'Start New Session')} bordered={false}>
                <LiveConfigForm onSubmit={handleStartSession} loading={loading} />
              </Card>
            </Col>
          </Row>
        ) : (
          /* ──── Active Trading Dashboard ──── */
          <>
            {/* Controls + Connection + Ticker */}
            <Card className="dashboard-card" bodyStyle={{ padding: '16px 24px' }}>
              <Row justify="space-between" align="middle">
                <Col>
                  <SessionControls
                    session={session}
                    ticker={ticker}
                    onStop={handleStopSession}
                    onRefresh={handleRefreshSession}
                    loading={loading}
                  />
                </Col>
                <Col>
                  <Space size="large">
                    {/* Ticker price with change */}
                    {ticker && ticker.last && (
                      <Space direction="vertical" size={0} style={{ textAlign: 'right' }}>
                        <Text strong style={{ fontSize: 18, color: '#facc15' }}>
                          {session.symbol}: ${Number(ticker.last).toLocaleString(undefined, { minimumFractionDigits: 2, maximumFractionDigits: 2 })}
                        </Text>
                        {priceChange !== 0 && (
                          <Text strong style={{ fontSize: 14, color: isPriceUp ? '#4ade80' : '#f87171' }}>
                            {isPriceUp ? '+' : ''}{priceChange.toFixed(2)} ({isPriceUp ? '+' : ''}{priceChangePercent.toFixed(2)}%)
                            {isPriceUp ? <RiseOutlined style={{ marginLeft: 4 }} /> : <FallOutlined style={{ marginLeft: 4 }} />}
                          </Text>
                        )}
                        <Text type="secondary" style={{ fontSize: 12 }}>
                          Bid: ${Number(ticker.bid || 0).toFixed(2)} | Ask: ${Number(ticker.ask || 0).toFixed(2)}
                        </Text>
                      </Space>
                    )}
                    {/* WS status */}
                    <Space>
                      <Badge status={wsConnected ? 'success' : 'error'} />
                      <Text type="secondary" style={{ color: wsConnected ? '#4ade80' : '#f87171' }}>
                        {wsConnected ? t('live.connected', 'Connected') : t('live.disconnected', 'Disconnected')}
                      </Text>
                    </Space>
                  </Space>
                </Col>
              </Row>
            </Card>

            {/* Statistics Cards */}
            <Row gutter={[16, 16]}>
              <Col xs={24} sm={12} lg={6}>
                <Card className="dashboard-card">
                  <Statistic
                    title={t('live.portfolio_value', 'Portfolio Value')}
                    value={portfolioValue}
                    precision={2}
                    prefix={<DollarOutlined />}
                    valueStyle={{ color: '#38bdf8' }}
                  />
                </Card>
              </Col>
              <Col xs={24} sm={12} lg={6}>
                <Card className="dashboard-card">
                  <Statistic
                    title={t('live.cash_balance', 'Cash Balance')}
                    value={cash}
                    precision={2}
                    prefix={<DollarOutlined />}
                  />
                </Card>
              </Col>
              <Col xs={24} sm={12} lg={6}>
                <Card className="dashboard-card">
                  <Statistic
                    title={t('live.unrealized_pnl', 'Unrealized P&L')}
                    value={currentPnl}
                    precision={2}
                    prefix={currentPnl >= 0 ? <RiseOutlined /> : <FallOutlined />}
                    valueStyle={{ color: currentPnl >= 0 ? '#4ade80' : '#f87171' }}
                  />
                </Card>
              </Col>
              <Col xs={24} sm={12} lg={6}>
                <Card className="dashboard-card">
                  <Statistic
                    title={t('live.total_trades', 'Total Trades')}
                    value={stats.totalTrades}
                    prefix={<ThunderboltOutlined />}
                    suffix={
                      stats.totalTrades > 0 && (
                        <Text type="secondary" style={{ fontSize: 14, marginLeft: 8 }}>
                          ({stats.winRate.toFixed(1)}% {t('live.win_rate', 'win')})
                        </Text>
                      )
                    }
                  />
                </Card>
              </Col>
            </Row>

            {/* Chart + Positions + Orders */}
            <Row gutter={[16, 16]}>
              <Col xs={24} xl={16}>
                <Card className="dashboard-card" title={t('live.price_chart', 'Price Chart')}>
                  <PriceChart
                    priceHistory={priceHistory}
                    currentPrice={ticker?.last}
                    symbol={session?.symbol}
                  />
                </Card>

                <Card className="dashboard-card" title={t('live.performance', 'Performance')}>
                  <PnLChart pnlHistory={pnlHistory} currentPnl={currentPnl} />
                </Card>

                <Card className="dashboard-card" title={t('live.open_positions', 'Open Positions')}>
                  <PositionTable positions={positions} ticker={ticker} />
                </Card>
              </Col>

              <Col xs={24} xl={8}>
                <Card
                  className="dashboard-card"
                  title={t('live.order_history', 'Orders')}
                  bodyStyle={{ padding: 0 }}
                >
                  <div style={{ height: '600px', overflowY: 'auto' }}>
                    <OrderLog
                      orders={orders}
                      onCancelOrder={handleCancelOrder}
                    />
                  </div>
                </Card>

                {/* Strategy Log Panel */}
                <Card
                  size="small"
                  title={t('live.strategy_log', '策略日志')}
                  style={{ marginTop: 16 }}
                >
                  <StrategyLog logs={logs} />
                </Card>
              </Col>
            </Row>
          </>
        )}
      </Content>
    </Layout>
  );
};

export default LiveTradingDashboard;
