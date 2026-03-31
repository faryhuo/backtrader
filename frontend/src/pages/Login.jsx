import { Alert, Button, Card, Form, Input, Space, Typography, message } from 'antd'
import { useState } from 'react'
import { useTranslation } from 'react-i18next'
import { Navigate, useLocation, useNavigate } from 'react-router-dom'
import { useAuth } from '../hooks/useAuth'
import './Login.css'

const { Paragraph, Title } = Typography

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
            <Card className="login-card" bordered={false}>
                <Space direction="vertical" size="large" style={{ width: '100%' }}>
                    <div>
                        <Title level={2}>Backtrader Pro</Title>
                        <Paragraph type="secondary">
                            {authProvider === 'system'
                                ? t('auth.systemLoginDesc', 'Use your email and password to access the platform.')
                                : t('auth.logtoLoginDesc', 'Sign in with Logto to continue.')}
                        </Paragraph>
                    </div>

                    {authProvider === 'system' ? (
                        <>
                            <Space>
                                <Button type={mode === 'login' ? 'primary' : 'default'} onClick={() => setMode('login')}>
                                    {t('auth.login', 'Login')}
                                </Button>
                                {registrationEnabled && (
                                    <Button type={mode === 'register' ? 'primary' : 'default'} onClick={() => setMode('register')}>
                                        {t('auth.register', 'Register')}
                                    </Button>
                                )}
                            </Space>

                            <Form layout="vertical" onFinish={handleSystemSubmit} disabled={submitting || isLoading}>
                                {mode === 'register' && (
                                    <Form.Item label={t('auth.displayName', 'Display name')} name="display_name">
                                        <Input placeholder={t('auth.displayNamePlaceholder', 'Optional name')} />
                                    </Form.Item>
                                )}
                                <Form.Item
                                    label={t('auth.email', 'Email')}
                                    name="email"
                                    rules={[{ required: true, message: t('auth.emailRequired', 'Email is required') }]}
                                >
                                    <Input placeholder="name@example.com" autoComplete="email" />
                                </Form.Item>
                                <Form.Item
                                    label={t('auth.password', 'Password')}
                                    name="password"
                                    rules={[{ required: true, message: t('auth.passwordRequired', 'Password is required') }]}
                                >
                                    <Input.Password placeholder={t('auth.passwordPlaceholder', 'At least 8 characters')} autoComplete="current-password" />
                                </Form.Item>
                                <Button type="primary" htmlType="submit" block loading={submitting}>
                                    {mode === 'register'
                                        ? t('auth.createAccount', 'Create account')
                                        : t('auth.login', 'Login')}
                                </Button>
                            </Form>

                            {!registrationEnabled && (
                                <Alert
                                    type="info"
                                    showIcon
                                    message={t('auth.registrationDisabled', 'Registration is disabled. Ask an administrator to create the first account.')}
                                />
                            )}
                        </>
                    ) : (
                        <Button type="primary" block loading={submitting} onClick={handleLogtoLogin}>
                            {t('auth.continueWithLogto', 'Continue with Logto')}
                        </Button>
                    )}
                </Space>
            </Card>
        </div>
    )
}
