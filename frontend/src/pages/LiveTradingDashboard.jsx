import React from 'react';
import { Layout, Row, Col, Card, Statistic, Space, Divider, Tabs, Typography, Badge } from 'antd';
import { DollarOutlined, RiseOutlined, FallOutlined, ThunderboltOutlined, DashboardOutlined } from '@ant-design/icons';
import { useTranslation } from 'react-i18next';
import LiveConfigForm from '../components/LiveTrading/LiveConfigForm';
import SessionControls from '../components/LiveTrading/SessionControls';
import PositionTable from '../components/LiveTrading/PositionTable';
import OrderLog from '../components/LiveTrading/OrderLog';
import PnLChart from '../components/LiveTrading/PnLChart';
import { useLiveTrading } from '../hooks/useLiveTrading';
import './LiveTradingDashboard.css';

const { Content } = Layout;
const { Title, Text } = Typography;

/**
 * Live Trading Dashboard
 * Main page for live/paper trading with real-time WebSocket updates
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
    stats,
    wsConnected,
    handleStartSession,
    handleStopSession,
    handleRefreshSession
  } = useLiveTrading();

  const isSessionActive = session && !['stopped', 'error'].includes(session.status);

  return (
    <Layout>
      <Content className="dashboard-container">
        <div className="dashboard-header">
          <Space align="center">
            <DashboardOutlined style={{ fontSize: '24px', color: '#38bdf8' }} />
            <Title level={2} className="dashboard-title" style={{ margin: 0 }}>
              {t('live.dashboard_title')}
            </Title>
          </Space>
          <div style={{ marginTop: 8 }}>
            <Text className="dashboard-subtitle">
              {t('live.dashboard_subtitle')}
            </Text>
          </div>
        </div>

        {!isSessionActive ? (
          // Configuration form when no active session
          <Row justify="center" style={{ marginTop: 40 }}>
            <Col xs={24} lg={16} xl={12}>
              <Card className="dashboard-card" title={t('live.start_new_session')} bordered={false}>
                <LiveConfigForm onSubmit={handleStartSession} loading={loading} />
              </Card>
            </Col>
          </Row>
        ) : (
          // Trading dashboard when session is active
          <>
            {/* Session Controls & Status */}
            <Card className="dashboard-card" bodyStyle={{ padding: '16px 24px' }}>
              <Row justify="space-between" align="middle">
                <Col>
                  <SessionControls
                    session={session}
                    onStart={handleStartSession}
                    onStop={handleStopSession}
                    onRefresh={handleRefreshSession}
                    loading={loading}
                  />
                </Col>
                <Col>
                  <Space>
                    <Badge status={wsConnected ? 'success' : 'error'} />
                    <Text type="secondary" style={{ color: wsConnected ? '#4ade80' : '#f87171' }}>
                      {wsConnected ? t('live.connected') : t('live.disconnected')}
                    </Text>
                  </Space>
                </Col>
              </Row>
            </Card>

            {/* Statistics Cards */}
            <Row gutter={[16, 16]}>
              <Col xs={24} sm={12} lg={6}>
                <Card className="dashboard-card">
                  <Statistic
                    title={t('live.portfolio_value')}
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
                    title={t('live.cash_balance')}
                    value={cash}
                    precision={2}
                    prefix={<DollarOutlined />}
                  />
                </Card>
              </Col>
              <Col xs={24} sm={12} lg={6}>
                <Card className="dashboard-card">
                  <Statistic
                    title={t('live.unrealized_pnl')}
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
                    title={t('live.total_trades')}
                    value={stats.totalTrades}
                    prefix={<ThunderboltOutlined />}
                    suffix={
                      stats.totalTrades > 0 && (
                        <Text type="secondary" style={{ fontSize: 14, marginLeft: 8 }}>
                          ({stats.winRate.toFixed(1)}{t('live.win_rate')})
                        </Text>
                      )
                    }
                  />
                </Card>
              </Col>
            </Row>

            <Row gutter={[16, 16]}>
              {/* Left Column: Chart & Positions */}
              <Col xs={24} xl={16}>
                <Card className="dashboard-card" title={t('live.performance')}>
                   <PnLChart pnlHistory={pnlHistory} currentPnl={currentPnl} />
                </Card>
                
                <Card className="dashboard-card" title={t('live.open_positions')}>
                  <PositionTable positions={positions} loading={false} />
                </Card>
              </Col>

              {/* Right Column: Order Log */}
              <Col xs={24} xl={8}>
                <Card className="dashboard-card" title={t('live.order_history')} bodyStyle={{ padding: 0 }}>
                  <div style={{ height: '600px', overflowY: 'auto' }}>
                     <OrderLog orders={orders} loading={false} />
                  </div>
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
