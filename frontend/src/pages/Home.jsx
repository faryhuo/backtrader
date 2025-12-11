import { useEffect } from 'react';
import { useNavigate } from 'react-router-dom';
import { Button, Typography, Space, Tag, Divider, Dropdown } from 'antd';
import { 
    LoginOutlined, 
    RocketOutlined, 
    GlobalOutlined,
    SwapOutlined,
    DashboardOutlined,
    PieChartOutlined,
    SafetyCertificateOutlined,
    TeamOutlined,
    FieldTimeOutlined,
    CheckCircleFilled
} from '@ant-design/icons';
import { useTranslation } from 'react-i18next';
import { useAuth } from '../hooks/useAuth';
import TradingDashboardImg from '../assets/illustrations/trading-dashboard.svg';
import './Home.css';

const { Title, Paragraph, Text } = Typography;

const CustomLogo = () => (
    <svg width="120" height="120" viewBox="0 0 120 120" fill="none" xmlns="http://www.w3.org/2000/svg" className="brand-logo">
        <defs>
            <linearGradient id="logoGradient" x1="0" y1="0" x2="120" y2="120" gradientUnits="userSpaceOnUse">
                <stop offset="0%" stopColor="#38bdf8" />
                <stop offset="100%" stopColor="#818cf8" />
            </linearGradient>
            <filter id="glow" x="-20%" y="-20%" width="140%" height="140%">
                <feGaussianBlur stdDeviation="5" result="coloredBlur" />
                <feMerge>
                    <feMergeNode in="coloredBlur" />
                    <feMergeNode in="SourceGraphic" />
                </feMerge>
            </filter>
        </defs>
        
        {/* Abstract Chart Bars */}
        <rect x="25" y="60" width="12" height="30" rx="2" fill="url(#logoGradient)" opacity="0.6" />
        <rect x="45" y="40" width="12" height="50" rx="2" fill="url(#logoGradient)" opacity="0.8" />
        <rect x="65" y="25" width="12" height="65" rx="2" fill="url(#logoGradient)" />
        <rect x="85" y="45" width="12" height="45" rx="2" fill="url(#logoGradient)" opacity="0.7" />
        
        {/* Connecting Trend Line */}
        <path d="M20 75 C 35 75, 40 45, 55 45 C 70 45, 75 20, 95 20" stroke="#38bdf8" strokeWidth="4" strokeLinecap="round" filter="url(#glow)" />
        
        {/* Circle Ring */}
        <circle cx="60" cy="60" r="56" stroke="url(#logoGradient)" strokeWidth="2" strokeDasharray="10 5" opacity="0.3" />
    </svg>
);

/**
 * Login Page
 *
 * Login page for unauthenticated users.
 * Provides login button to initiate Logto authentication flow.
 * Automatically redirects authenticated users to the app.
 */
export function Home() {
    const { signIn, isAuthenticated, loginEnabled } = useAuth();
    const navigate = useNavigate();
    const { t, i18n } = useTranslation();

    // Redirect to main app if already authenticated
    useEffect(() => {
        if (loginEnabled && isAuthenticated) {
            navigate('/strategy');
        }
    }, [isAuthenticated, loginEnabled, navigate]);

    // Handle sign-in click
    const handleSignIn = () => {
        if (!loginEnabled) {
            navigate('/strategy');
            return;
        }
        const redirectUri = import.meta.env.VITE_LOGTO_REDIRECT_URI;
        signIn(redirectUri);
    };

    const handleLanguageChange = ({ key }) => {
        i18n.changeLanguage(key);
    };

    const languageItems = [
        { key: 'en', label: 'English' },
        { key: 'zh', label: '中文' }
    ];

    const roadmapItems = [
        { icon: <SwapOutlined />, title: t('home.live_trading'), desc: t('home.live_trading_desc') },
        { icon: <DashboardOutlined />, title: t('home.monitoring'), desc: t('home.monitoring_desc') },
        { icon: <PieChartOutlined />, title: t('home.multi_asset'), desc: t('home.multi_asset_desc') },
        { icon: <SafetyCertificateOutlined />, title: t('home.risk_control'), desc: t('home.risk_control_desc') },
        { icon: <TeamOutlined />, title: t('home.team_collab'), desc: t('home.team_collab_desc') },
        { icon: <FieldTimeOutlined />, title: t('home.walk_forward'), desc: t('home.walk_forward_desc') },
    ];

    return (
        <div className="home-page">
            {/* Animated Background Layers */}
            <div className="bg-grid"></div>
            <div className="bg-gradient-orb orb-1"></div>
            <div className="bg-gradient-orb orb-2"></div>
            
            <div className="lang-switch-container">
                <Dropdown menu={{ items: languageItems, onClick: handleLanguageChange }} placement="bottomRight" arrow>
                    <Button 
                        type="text" 
                        icon={<GlobalOutlined />} 
                        className="lang-switch-btn"
                    />
                </Dropdown>
            </div>

            <div className="home-content-wrapper">
                <div className="home-card glass-panel">
                    
                    {/* Left Column: Hero Section */}
                    <div className="hero-section">
                        <div className="logo-container">
                            <CustomLogo />
                        </div>

                        <div className="title-section">
                            <Title level={1} className="home-title">
                                {t('app.title', 'Backtrader')} <span className="highlight">Pro</span>
                            </Title>
                            
                            <Paragraph className="home-subtitle">
                                {t('home.subtitle', 'Next-generation algorithmic trading platform powered by AI analysis.')}
                            </Paragraph>
                        </div>

                        <Button
                            type="primary"
                            size="large"
                            icon={loginEnabled ? <LoginOutlined /> : <RocketOutlined />}
                            onClick={handleSignIn}
                            className="signin-button glowing-btn"
                        >
                            {loginEnabled ? t('home.access_platform', 'Access Platform') : t('home.enter_platform', 'Enter Platform')}
                        </Button>

                        <div className="hero-benefits">
                            <Text className="benefits-title">{t('home.benefits_title')}</Text>
                            <div className="benefits-list">
                                <div className="benefit-item">
                                    <CheckCircleFilled className="benefit-icon" />
                                    <div className="benefit-text">
                                        <Text strong className="benefit-head">{t('home.benefit_privacy')}</Text>
                                        <Text className="benefit-desc">{t('home.benefit_privacy_desc')}</Text>
                                    </div>
                                </div>
                                <div className="benefit-item">
                                    <CheckCircleFilled className="benefit-icon" />
                                    <div className="benefit-text">
                                        <Text strong className="benefit-head">{t('home.benefit_engine')}</Text>
                                        <Text className="benefit-desc">{t('home.benefit_engine_desc')}</Text>
                                    </div>
                                </div>
                                <div className="benefit-item">
                                    <CheckCircleFilled className="benefit-icon" />
                                    <div className="benefit-text">
                                        <Text strong className="benefit-head">{t('home.benefit_ai')}</Text>
                                        <Text className="benefit-desc">{t('home.benefit_ai_desc')}</Text>
                                    </div>
                                </div>
                            </div>
                        </div>
                    </div>

                    {/* Right Column: Content Section */}
                    <div className="content-section">
                        <div className="hero-image-container">
                            <img src={TradingDashboardImg} alt="Trading Dashboard" className="hero-dashboard-img" />
                        </div>

                        <div className="features-grid">
                            <div className="feature-item">
                                <span className="feature-icon">⚡</span>
                                <Text strong>{t('home.fast_backtesting', 'Fast Backtesting')}</Text>
                            </div>
                            <div className="feature-item">
                                <span className="feature-icon">🧠</span>
                                <Text strong>{t('home.ai_analysis', 'AI Analysis')}</Text>
                            </div>
                            <div className="feature-item">
                                <span className="feature-icon">📊</span>
                                <Text strong>{t('home.interactive_charts', 'Interactive Charts')}</Text>
                            </div>
                        </div>

                        <Divider orientation="left" style={{ borderColor: 'rgba(255,255,255,0.1)', margin: '0' }}>
                            <span style={{ color: '#94a3b8', fontSize: '0.9rem' }}>{t('home.future_features')}</span>
                        </Divider>

                        <div className="roadmap-grid">
                            {roadmapItems.map((item, index) => (
                                <div key={index} className="roadmap-item">
                                    <div className="roadmap-icon">{item.icon}</div>
                                    <div className="roadmap-content">
                                        <Text strong className="roadmap-title">{item.title}</Text>
                                        <Text type="secondary" className="roadmap-desc">{item.desc}</Text>
                                    </div>
                                </div>
                            ))}
                        </div>
                    </div>

                </div>
            </div>
        </div>
    );
}