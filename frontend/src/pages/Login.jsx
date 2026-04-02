import {
    ArrowRightOutlined,
    LockOutlined,
    SafetyCertificateOutlined,
    StockOutlined,
    UserOutlined,
} from '@ant-design/icons'
import {
    Alert,
    Button,
    Card,
    Form,
    Input,
    Space,
    Tag,
    Typography,
    message,
} from 'antd'
import { useState } from 'react'
import { useTranslation } from 'react-i18next'
import { Navigate, useLocation, useNavigate } from 'react-router-dom'
import { useAuth } from '../hooks/useAuth'
import './Login.css'

const { Paragraph, Text, Title } = Typography

const marketSnapshots = [
    { label: 'Alpha Model', value: '+18.4%', tone: 'up' },
    { label: 'Drawdown Control', value: '2.1%', tone: 'neutral' },
    { label: 'Signal Latency', value: '12ms', tone: 'up' },
]

const platformHighlights = [
    'Multi-asset strategy lab',
    'Risk monitoring and execution controls',
    'Institutional-grade research workflow',
]

export default function Login() {
    const { t } = useTranslation()
    const navigate = useNavigate()
    const location = useLocation()
    const {
        authProvider,
        loginEnabled,
        registrationEnabled,
        isAuthenticated,
        isLoading,
        signIn,
        signInWithPassword,
        registerWithPassword,
    } = useAuth()
    const [submitting, setSubmitting] = useState(false)
    const [mode, setMode] = useState('login')

    if (!loginEnabled) {
        return <Navigate to="/" replace />
    }

    if (isAuthenticated) {
        const target = location.state?.from?.pathname || '/strategy'
        return <Navigate to={target} replace />
    }

    const handleLogtoLogin = async () => {
        setSubmitting(true)
        try {
            const redirectUri = window.location.origin + '/callback'
            await signIn(redirectUri)
        } finally {
            setSubmitting(false)
        }
    }

    const handleSystemSubmit = async (values) => {
        setSubmitting(true)
        try {
            if (mode === 'register') {
                await registerWithPassword(values)
            } else {
                await signInWithPassword(values)
            }
            const target = location.state?.from?.pathname || '/strategy'
            navigate(target, { replace: true })
        } catch (error) {
            message.error(error.message || t('auth.loginFailed', 'Authentication failed'))
        } finally {
            setSubmitting(false)
        }
    }

    return (
        <div className="login-page">
            <div className="login-shell">
                <section className="login-hero">
                    <div className="login-hero__badge">
                        <StockOutlined />
                        <span>{t('auth.appTitle', 'Backtrader Platform')}</span>
                    </div>

                    <div className="login-hero__copy">
                        <Title level={1} className="login-hero__title">
                            Quant research and execution, in one trading workspace.
                        </Title>
                        <Paragraph className="login-hero__description">
                            Connect strategy design, portfolio replay, live monitoring, and
                            risk controls through a single platform built for systematic
                            traders.
                        </Paragraph>
                    </div>

                    <div className="login-market-grid">
                        {marketSnapshots.map((item) => (
                            <div key={item.label} className="login-market-card">
                                <Text className="login-market-card__label">{item.label}</Text>
                                <Text
                                    className={`login-market-card__value login-market-card__value--${item.tone}`}
                                >
                                    {item.value}
                                </Text>
                            </div>
                        ))}
                    </div>

                    <div className="login-hero__panel">
                        <div className="login-hero__panel-header">
                            <Text className="login-panel__eyebrow">Execution Stack</Text>
                            <Text className="login-panel__status">Live</Text>
                        </div>
                        <div className="login-hero__signal">
                            <span className="login-hero__signal-line login-hero__signal-line--strong" />
                            <span className="login-hero__signal-line login-hero__signal-line--mid" />
                            <span className="login-hero__signal-line login-hero__signal-line--soft" />
                        </div>
                        <div className="login-hero__highlights">
                            {platformHighlights.map((item) => (
                                <div key={item} className="login-hero__highlight">
                                    <ArrowRightOutlined />
                                    <span>{item}</span>
                                </div>
                            ))}
                        </div>
                    </div>
                </section>

                <Card className="login-card" bordered={false}>
                    <Space direction="vertical" size="large" style={{ width: '100%' }}>
                        <div className="login-card__header">
                            <Tag className="login-card__tag" bordered={false}>
                                Secure Access
                            </Tag>
                            <Title level={2} className="login-card__title">
                                Backtrader Pro
                            </Title>
                            <Paragraph className="login-card__description">
                                {authProvider === 'system'
                                    ? t(
                                        'auth.systemLoginDesc',
                                        'Use your email and password to access the platform.',
                                    )
                                    : t(
                                        'auth.logtoLoginDesc',
                                        'Sign in with Logto to continue.',
                                    )}
                            </Paragraph>
                        </div>

                        <div className="login-card__meta">
                            <div className="login-card__meta-item">
                                <SafetyCertificateOutlined />
                                <span>Protected research environment</span>
                            </div>
                            <div className="login-card__meta-item">
                                <LockOutlined />
                                <span>Encrypted authentication flow</span>
                            </div>
                        </div>

                        {authProvider === 'system' ? (
                            <>
                                <div className="login-mode-switch">
                                    <Button
                                        type={mode === 'login' ? 'primary' : 'default'}
                                        onClick={() => setMode('login')}
                                    >
                                        {t('auth.login', 'Login')}
                                    </Button>
                                    {registrationEnabled && (
                                        <Button
                                            type={mode === 'register' ? 'primary' : 'default'}
                                            onClick={() => setMode('register')}
                                        >
                                            {t('auth.register', 'Register')}
                                        </Button>
                                    )}
                                </div>

                                <Form
                                    layout="vertical"
                                    onFinish={handleSystemSubmit}
                                    disabled={submitting || isLoading}
                                    className="login-form"
                                >
                                    {mode === 'register' && (
                                        <Form.Item
                                            label={t('auth.displayName', 'Display name')}
                                            name="display_name"
                                        >
                                            <Input
                                                prefix={<UserOutlined />}
                                                placeholder={t(
                                                    'auth.displayNamePlaceholder',
                                                    'Optional name',
                                                )}
                                            />
                                        </Form.Item>
                                    )}
                                    <Form.Item
                                        label={t('auth.email', 'Email')}
                                        name="email"
                                        rules={[
                                            {
                                                required: true,
                                                message: t(
                                                    'auth.emailRequired',
                                                    'Email is required',
                                                ),
                                            },
                                        ]}
                                    >
                                        <Input
                                            prefix={<UserOutlined />}
                                            placeholder="name@example.com"
                                            autoComplete="email"
                                        />
                                    </Form.Item>
                                    <Form.Item
                                        label={t('auth.password', 'Password')}
                                        name="password"
                                        rules={[
                                            {
                                                required: true,
                                                message: t(
                                                    'auth.passwordRequired',
                                                    'Password is required',
                                                ),
                                            },
                                        ]}
                                    >
                                        <Input.Password
                                            prefix={<LockOutlined />}
                                            placeholder={t(
                                                'auth.passwordPlaceholder',
                                                'At least 8 characters',
                                            )}
                                            autoComplete="current-password"
                                        />
                                    </Form.Item>
                                    <Button
                                        type="primary"
                                        htmlType="submit"
                                        block
                                        loading={submitting}
                                        className="login-submit"
                                    >
                                        {mode === 'register'
                                            ? t('auth.createAccount', 'Create account')
                                            : t('auth.login', 'Login')}
                                    </Button>
                                </Form>

                                {!registrationEnabled && (
                                    <Alert
                                        type="info"
                                        showIcon
                                        message={t(
                                            'auth.registrationDisabled',
                                            'Registration is disabled. Ask an administrator to create the first account.',
                                        )}
                                    />
                                )}
                            </>
                        ) : (
                            <Button
                                type="primary"
                                block
                                loading={submitting}
                                onClick={handleLogtoLogin}
                                className="login-submit"
                            >
                                {t('auth.continueWithLogto', 'Continue with Logto')}
                            </Button>
                        )}
                    </Space>
                </Card>
            </div>
        </div>
    )
}
