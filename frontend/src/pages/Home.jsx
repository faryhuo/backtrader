import { useEffect } from 'react';
import { useLogto } from '@logto/react';
import { useNavigate } from 'react-router-dom';
import { Button, Typography, Space } from 'antd';
import { LoginOutlined, RocketOutlined } from '@ant-design/icons';
import { useTranslation } from 'react-i18next';
import './Home.css';

const { Title, Paragraph } = Typography;

/**
 * Login Page
 *
 * Login page for unauthenticated users.
 * Provides login button to initiate Logto authentication flow.
 * Automatically redirects authenticated users to the app.
 */
export function Home() {
  const { signIn, isAuthenticated } = useLogto();
  const navigate = useNavigate();
  const { t } = useTranslation();

  // Redirect to main app if already authenticated
  useEffect(() => {
    if (isAuthenticated) {
      navigate('/');
    }
  }, [isAuthenticated, navigate]);

  // Handle sign-in click
  const handleSignIn = () => {
    const redirectUri = import.meta.env.VITE_LOGTO_REDIRECT_URI;
    signIn(redirectUri);
  };

  return (
    <div className="home-page">
      <div className="home-content">
        <Space direction="vertical" size="large" align="center">
          <RocketOutlined className="home-icon" />

          <Title level={1} className="home-title">
            {t('auth.appTitle', 'Backtrader Platform')}
          </Title>

          <Paragraph className="home-description">
            {t('auth.homeDescription', 'Design and test algorithmic trading strategies with professional backtesting tools, AI-powered analysis, and interactive charts.')}
          </Paragraph>

          <Space direction="vertical" size="middle" className="home-features">
            <Paragraph>Strategy Editor with Monaco Code Editor</Paragraph>
            <Paragraph>Historical Backtesting on Financial Market Data</Paragraph>
            <Paragraph>AI-Powered Strategy Analysis</Paragraph>
            <Paragraph>Interactive Candlestick Charts</Paragraph>
          </Space>

          <Button
            type="primary"
            size="large"
            icon={<LoginOutlined />}
            onClick={handleSignIn}
            className="signin-button"
          >
            {t('auth.signIn', 'Sign In')}
          </Button>
        </Space>
      </div>
    </div>
  );
}
