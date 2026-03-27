import { useCallback, useEffect, useMemo, useState } from 'react'
import { useNavigate } from 'react-router-dom'
import { useTranslation } from 'react-i18next'
import {
    Alert,
    Button,
    Card,
    Col,
    Divider,
    Input,
    InputNumber,
    Radio,
    Row,
    Space,
    Spin,
    Steps,
    Switch,
    Tag,
    Typography,
    message
} from 'antd'
import {
    CheckCircleOutlined,
    LoadingOutlined,
    RocketOutlined,
    SafetyOutlined
} from '@ant-design/icons'

import AISetupSection from '../components/OnboardingSetup/AISetupSection'
import DataSourceSetupSection from '../components/OnboardingSetup/DataSourceSetupSection'
import ReviewSummary from '../components/OnboardingSetup/ReviewSummary'
import SettingRow from '../components/OnboardingSetup/SettingRow'
import TradingSetupSection from '../components/OnboardingSetup/TradingSetupSection'
import { AI_PROVIDERS } from '../constants/settingsConstants'
import { setupApi } from '../services/setupApi'
import './OnboardingSetup.css'

const { Title, Paragraph } = Typography

const DEFAULT_DATA_SOURCE_PRIORITY = ['yahoo', 'database']
const ONBOARDING_AI_PROVIDER_DEFAULTS = {
    openai: { base_url: 'https://api.openai.com/v1', default_model: 'gpt-5.1' },
    minimax: { base_url: 'https://api.minimaxi.com/anthropic', default_model: 'MiniMax-M2.7' },
    gemini: { base_url: 'https://generativelanguage.googleapis.com/v1beta', default_model: 'gemini-2.0-flash' },
    claude: { base_url: 'https://api.anthropic.com/v1', default_model: 'claude-3-5-haiku-latest' }
}

function deriveLoginEnabled(deploymentMode) {
    return deploymentMode === 'public'
}

function hasText(value) {
    return typeof value === 'string' ? value.trim().length > 0 : Boolean(value)
}

function setValueAtPath(target, path, value) {
    const next = structuredClone(target)
    let cursor = next
    for (let index = 0; index < path.length - 1; index += 1) {
        cursor[path[index]] = cursor[path[index]] ?? {}
        cursor = cursor[path[index]]
    }
    cursor[path[path.length - 1]] = value
    return next
}

function moveItem(items, item, direction) {
    const index = items.indexOf(item)
    if (index < 0) {
        return items
    }
    const nextIndex = direction === 'up' ? index - 1 : index + 1
    if (nextIndex < 0 || nextIndex >= items.length) {
        return items
    }
    const next = [...items]
    const [current] = next.splice(index, 1)
    next.splice(nextIndex, 0, current)
    return next
}

function createProviderDefaults() {
    return AI_PROVIDERS.reduce((accumulator, provider) => {
        accumulator[provider.key] = {
            api_key: '',
            base_url: ONBOARDING_AI_PROVIDER_DEFAULTS[provider.key]?.base_url || '',
            default_model: ONBOARDING_AI_PROVIDER_DEFAULTS[provider.key]?.default_model || '',
            configured: false
        }
        return accumulator
    }, {})
}

function normalizeWizardConfig(rawConfig, generatedEncryptionKey = '') {
    const providerDefaults = createProviderDefaults()
    const rawProviders = rawConfig?.ai?.providers || {}
    const mergedProviders = AI_PROVIDERS.reduce((accumulator, provider) => {
        accumulator[provider.key] = {
            ...(providerDefaults[provider.key] || {}),
            ...(rawProviders[provider.key] || {})
        }
        return accumulator
    }, {})
    const deploymentMode = rawConfig?.deployment_mode ?? 'local'

    return {
        ...rawConfig,
        deployment_mode: deploymentMode,
        security: {
            ...(rawConfig?.security || {}),
            encryption_key: rawConfig?.security?.encryption_key || generatedEncryptionKey,
            enable_login: deriveLoginEnabled(deploymentMode)
        },
        ai: {
            enabled: rawConfig?.ai?.enabled ?? false,
            provider_priority: rawConfig?.ai?.provider_priority ?? ['openai'],
            providers: mergedProviders
        },
        data_source: {
            ...(rawConfig?.data_source || {}),
            priority: rawConfig?.data_source?.priority ?? DEFAULT_DATA_SOURCE_PRIORITY,
            eodhd_api_key: rawConfig?.data_source?.eodhd_api_key ?? ''
        },
        trading: {
            ...rawConfig?.trading,
            default_trade_mode: 'paper',
            binance: {
                enabled: true,
                markets: ['spot'],
                default_market: 'spot',
                paper_enabled: true,
                sandbox_url: 'https://testnet.binance.vision',
                initial_balance_usdt: 10000,
                ...(rawConfig?.trading?.binance || {})
            },
            credentials: {
                paper: { api_key: '', secret: '', ...(rawConfig?.trading?.credentials?.paper || {}) },
                live: { api_key: '', secret: '', ...(rawConfig?.trading?.credentials?.live || {}) }
            }
        }
    }
}

export default function OnboardingSetup() {
    const { t } = useTranslation()
    const navigate = useNavigate()
    const [loading, setLoading] = useState(true)
    const [saving, setSaving] = useState(false)
    const [testing, setTesting] = useState('')
    const [wizardState, setWizardState] = useState(null)
    const [initialConfig, setInitialConfig] = useState(null)
    const [config, setConfig] = useState(null)
    const [stepIndex, setStepIndex] = useState(0)

    const loadWizard = useCallback(async () => {
        setLoading(true)
        try {
            const response = await setupApi.getSetupWizard()
            const normalizedConfig = normalizeWizardConfig(
                response.config,
                response.meta?.generated_encryption_key || ''
            )
            setWizardState(response)
            setInitialConfig(structuredClone(normalizedConfig))
            setConfig(structuredClone(normalizedConfig))
        } catch (error) {
            message.error(error.message || t('onboarding.load_failed', 'Failed to load setup wizard'))
        } finally {
            setLoading(false)
        }
    }, [t])

    useEffect(() => {
        loadWizard()
    }, [loadWizard])

    const requiresLogin = deriveLoginEnabled(config?.deployment_mode)

    const steps = useMemo(() => {
        const base = [
            { key: 'welcome', title: t('onboarding.steps.welcome', 'Welcome') },
            { key: 'database', title: t('onboarding.steps.database', 'Database') }
        ]
        if (requiresLogin) {
            base.push({ key: 'auth', title: t('onboarding.steps.auth', 'Authentication') })
        }
        return [
            ...base,
            { key: 'data', title: t('onboarding.steps.data', 'Data Source') },
            { key: 'ai', title: t('onboarding.steps.ai', 'AI') },
            { key: 'trading', title: t('onboarding.steps.trading', 'Trading') },
            { key: 'brand', title: t('onboarding.steps.brand', 'Brand & Report') },
            { key: 'review', title: t('onboarding.steps.review', 'Review') }
        ]
    }, [requiresLogin, t])

    useEffect(() => {
        setStepIndex((current) => Math.min(current, Math.max(steps.length - 1, 0)))
    }, [steps.length])

    const currentStep = steps[stepIndex]?.key
    const enabledProviders = config?.ai?.provider_priority || []

    const updateConfig = (path, value) => {
        setConfig((previous) => setValueAtPath(previous, path, value))
    }

    const toggleProvider = (providerKey, checked) => {
        const currentPriority = config.ai.provider_priority || []
        const nextPriority = checked
            ? [...currentPriority, providerKey]
            : currentPriority.filter((item) => item !== providerKey)
        updateConfig(['ai', 'provider_priority'], nextPriority)
    }

    const reorderProvider = (providerKey, direction) => {
        updateConfig(['ai', 'provider_priority'], moveItem(config.ai.provider_priority || [], providerKey, direction))
    }

    const validateStep = () => {
        if (!config) {
            return false
        }
        if (currentStep === 'database' && config.database.mode === 'sqlite' && !config.database.sqlite_path) {
            message.warning(t('onboarding.validation.sqlite_path', 'SQLite path is required.'))
            return false
        }
        if (currentStep === 'auth' && requiresLogin) {
            const required = [
                config.auth.logto_issuer,
                config.auth.logto_jwks_uri,
                config.auth.logto_audience,
                config.auth.logto_endpoint,
                config.auth.logto_app_id,
                config.auth.logto_redirect_uri,
                config.auth.logto_post_logout_redirect_uri
            ]
            if (required.some((item) => !item)) {
                message.warning(t('onboarding.validation.logto', 'All Logto fields are required when login is enabled.'))
                return false
            }
        }
        if (currentStep === 'data') {
            const dataPriority = config.data_source?.priority || []
            if (dataPriority.length === 0) {
                message.warning(t('onboarding.datasource.min_source_warning', 'At least one data source is required.'))
                return false
            }
            if (dataPriority.includes('eodhd') && !config.data_source.eodhd_api_key) {
                message.warning(t('onboarding.validation.eodhd', 'EODHD API key is required when EODHD is enabled.'))
                return false
            }
        }
        if (currentStep === 'ai' && config.ai.enabled) {
            if (enabledProviders.length === 0) {
                message.warning(t('onboarding.validation.ai_provider', 'Enable at least one AI provider.'))
                return false
            }
            const missingProviders = enabledProviders.filter((provider) => !hasText(config.ai.providers?.[provider]?.api_key))
            if (missingProviders.length > 0) {
                message.warning(
                    t('onboarding.validation.ai_provider_keys', 'API key is required for all enabled AI providers.')
                )
                return false
            }
            const missingModels = enabledProviders.filter((provider) => !hasText(config.ai.providers?.[provider]?.default_model))
            if (missingModels.length > 0) {
                message.warning(
                    t('onboarding.validation.ai_provider_models', 'Runtime model name is required for all enabled AI providers.')
                )
                return false
            }
        }
        if (currentStep === 'trading') {
            const paper = config.trading.credentials.paper
            const live = config.trading.credentials.live
            const paperPartial = Boolean(paper.api_key || paper.secret)
            const livePartial = Boolean(live.api_key || live.secret)

            if (paperPartial && (!paper.api_key || !paper.secret)) {
                message.warning(t('onboarding.validation.paper_credentials', 'Binance paper credentials require both API key and secret.'))
                return false
            }
            if (livePartial && (!live.api_key || !live.secret)) {
                message.warning(t('onboarding.validation.live_credentials', 'Binance live credentials require both API key and secret.'))
                return false
            }
            if (config.trading.live_trading_enabled) {
                if (!live.api_key || !live.secret) {
                    message.warning(t('onboarding.validation.live_credentials_required', 'Live trading requires Binance live credentials.'))
                    return false
                }
                if (!config.trading.live_risk_acknowledged) {
                    message.warning(t('onboarding.validation.live_ack', 'Live mode requires explicit risk acknowledgement.'))
                    return false
                }
            }
        }
        return true
    }

    const testConnection = async (type, payload, testKey = type) => {
        setTesting(testKey)
        try {
            const response = await setupApi.testSetupWizard(type, payload)
            if (response.valid) {
                message.success(response.message || t('onboarding.test_success', 'Connection test passed'))
            } else {
                message.error(response.message || t('onboarding.test_failed', 'Connection test failed'))
            }
        } catch (error) {
            message.error(error.message || t('onboarding.test_failed', 'Connection test failed'))
        } finally {
            setTesting('')
        }
    }

    const handleSave = async () => {
        setSaving(true)
        try {
            await setupApi.saveSetupWizard({
                ...config,
                security: {
                    ...config.security,
                    enable_login: requiresLogin
                }
            })
            message.success(t('onboarding.save_success', 'Setup configuration saved'))
            await loadWizard()
        } catch (error) {
            message.error(error.message || t('onboarding.save_failed', 'Failed to save setup configuration'))
        } finally {
            setSaving(false)
        }
    }

    if (loading || !config || !wizardState || !initialConfig) {
        return (
            <div className="onboarding-page onboarding-loading">
                <Spin indicator={<LoadingOutlined spin />} size="large" />
            </div>
        )
    }

    const renderWelcome = () => (
        <Card className="onboarding-card">
            <Space direction="vertical" size="large" style={{ width: '100%' }}>
                <div>
                    <Tag color={wizardState.status.is_ready ? 'success' : 'warning'}>
                        {wizardState.status.is_ready
                            ? t('onboarding.ready', 'Configured')
                            : t('onboarding.not_ready', 'Setup Required')}
                    </Tag>
                    <Title level={2}>{t('onboarding.title', 'First-Run Setup Wizard')}</Title>
                    <Paragraph>{t('onboarding.subtitle', 'Complete the minimum runtime configuration before handing the platform to end users.')}</Paragraph>
                </div>
                <Radio.Group
                    value={config.deployment_mode}
                    onChange={(event) => updateConfig(['deployment_mode'], event.target.value)}
                >
                    <Space direction="vertical">
                        <Radio value="local">{t('onboarding.deployment.local', 'Local development or single-machine install')}</Radio>
                        <Radio value="public">{t('onboarding.deployment.public', 'Public deployment with stricter auth expectations')}</Radio>
                    </Space>
                </Radio.Group>
                <Alert
                    type="info"
                    showIcon
                    message={t('onboarding.milestone_title', 'MVP scope')}
                    description={t('onboarding.milestone_desc', 'This wizard focuses on backend bootstrap settings: deployment, storage, data source, AI, Binance trading, branding, and review.')}
                />
                <Alert
                    type={requiresLogin ? 'warning' : 'success'}
                    showIcon
                    message={requiresLogin
                        ? t('onboarding.deployment_public_title', 'Public mode will require login')
                        : t('onboarding.deployment_local_title', 'Local mode keeps login disabled')}
                    description={requiresLogin
                        ? t('onboarding.deployment_public_desc', 'Selecting public deployment automatically enables authentication and adds the Logto step to this wizard.')
                        : t('onboarding.deployment_local_desc', 'Selecting local deployment keeps authentication disabled and skips the Logto step.')}
                />
            </Space>
        </Card>
    )

    const renderDatabase = () => (
        <Card className="onboarding-card">
            <SettingRow label={t('onboarding.fields.database_mode', 'Database mode')}>
                <Radio.Group
                    value={config.database.mode}
                    onChange={(event) => updateConfig(['database', 'mode'], event.target.value)}
                >
                    <Space>
                        <Radio value="sqlite">SQLite</Radio>
                        <Radio value="postgresql">PostgreSQL</Radio>
                    </Space>
                </Radio.Group>
            </SettingRow>
            {config.database.mode === 'sqlite' ? (
                <SettingRow label={t('onboarding.fields.sqlite_path', 'SQLite path')}>
                    <Input value={config.database.sqlite_path} onChange={(event) => updateConfig(['database', 'sqlite_path'], event.target.value)} />
                </SettingRow>
            ) : null}
            {config.database.mode === 'postgresql' ? (
                <Row gutter={16}>
                    <Col span={12}><SettingRow label={t('onboarding.fields.pg_host', 'PostgreSQL host')}><Input value={config.database.postgresql.host} onChange={(event) => updateConfig(['database', 'postgresql', 'host'], event.target.value)} /></SettingRow></Col>
                    <Col span={12}><SettingRow label={t('onboarding.fields.pg_port', 'PostgreSQL port')}><InputNumber style={{ width: '100%' }} value={config.database.postgresql.port} onChange={(value) => updateConfig(['database', 'postgresql', 'port'], value ?? 5432)} /></SettingRow></Col>
                    <Col span={12}><SettingRow label={t('onboarding.fields.pg_database', 'PostgreSQL database')}><Input value={config.database.postgresql.database} onChange={(event) => updateConfig(['database', 'postgresql', 'database'], event.target.value)} /></SettingRow></Col>
                    <Col span={12}><SettingRow label={t('onboarding.fields.pg_username', 'PostgreSQL username')}><Input value={config.database.postgresql.username} onChange={(event) => updateConfig(['database', 'postgresql', 'username'], event.target.value)} /></SettingRow></Col>
                    <Col span={24}><SettingRow label={t('onboarding.fields.pg_password', 'PostgreSQL password')}><Input.Password value={config.database.postgresql.password} onChange={(event) => updateConfig(['database', 'postgresql', 'password'], event.target.value)} /></SettingRow></Col>
                </Row>
            ) : null}
            <Alert
                type="info"
                showIcon
                message={t('onboarding.database_note', 'The onboarding flow writes database mode into backend/resources/config/database_config.json and does not manage DATABASE_URL.')}
            />
        </Card>
    )

    const renderAuth = () => (
        <Card className="onboarding-card">
            <Row gutter={16}>
                <Col span={12}><SettingRow label="LOGTO_ISSUER"><Input value={config.auth.logto_issuer} onChange={(event) => updateConfig(['auth', 'logto_issuer'], event.target.value)} /></SettingRow></Col>
                <Col span={12}><SettingRow label="LOGTO_JWKS_URI"><Input value={config.auth.logto_jwks_uri} onChange={(event) => updateConfig(['auth', 'logto_jwks_uri'], event.target.value)} /></SettingRow></Col>
                <Col span={12}><SettingRow label="LOGTO_AUDIENCE"><Input value={config.auth.logto_audience} onChange={(event) => updateConfig(['auth', 'logto_audience'], event.target.value)} /></SettingRow></Col>
                <Col span={12}><SettingRow label="LOGTO_REQUIRED_SCOPES"><Input value={config.auth.logto_required_scopes} onChange={(event) => updateConfig(['auth', 'logto_required_scopes'], event.target.value)} /></SettingRow></Col>
                <Col span={12}><SettingRow label="LOGTO_ENDPOINT"><Input value={config.auth.logto_endpoint} onChange={(event) => updateConfig(['auth', 'logto_endpoint'], event.target.value)} /></SettingRow></Col>
                <Col span={12}><SettingRow label="LOGTO_APP_ID"><Input value={config.auth.logto_app_id} onChange={(event) => updateConfig(['auth', 'logto_app_id'], event.target.value)} /></SettingRow></Col>
                <Col span={12}><SettingRow label="LOGTO_REDIRECT_URI"><Input value={config.auth.logto_redirect_uri} onChange={(event) => updateConfig(['auth', 'logto_redirect_uri'], event.target.value)} /></SettingRow></Col>
                <Col span={12}><SettingRow label="LOGTO_POST_LOGOUT_REDIRECT_URI"><Input value={config.auth.logto_post_logout_redirect_uri} onChange={(event) => updateConfig(['auth', 'logto_post_logout_redirect_uri'], event.target.value)} /></SettingRow></Col>
            </Row>
            <Button
                onClick={() => testConnection('logto', { issuer: config.auth.logto_issuer, jwks_uri: config.auth.logto_jwks_uri }, 'logto')}
                loading={testing === 'logto'}
            >
                {t('onboarding.actions.test_logto', 'Test JWKS')}
            </Button>
        </Card>
    )

    const renderData = () => (
        <DataSourceSetupSection
            config={config}
            updateConfig={updateConfig}
            t={t}
        />
    )

    const renderAI = () => (
        <AISetupSection
            config={config}
            enabledProviders={enabledProviders}
            updateConfig={updateConfig}
            toggleProvider={toggleProvider}
            reorderProvider={reorderProvider}
            testConnection={testConnection}
            testing={testing}
            t={t}
        />
    )

    const renderTrading = () => (
        <TradingSetupSection
            config={config}
            updateConfig={updateConfig}
            testConnection={testConnection}
            testing={testing}
            t={t}
        />
    )

    const renderBrand = () => (
        <Card className="onboarding-card">
            <Row gutter={16}>
                <Col span={12}><SettingRow label={t('onboarding.fields.site_title', 'Site title')}><Input value={config.site.site_title} onChange={(event) => updateConfig(['site', 'site_title'], event.target.value)} /></SettingRow></Col>
                <Col span={12}><SettingRow label={t('onboarding.fields.site_description', 'Site description')}><Input value={config.site.site_description} onChange={(event) => updateConfig(['site', 'site_description'], event.target.value)} /></SettingRow></Col>
                <Col span={12}><SettingRow label={t('onboarding.fields.docs_url', 'Documentation URL')}><Input value={config.site.site_docs_url} onChange={(event) => updateConfig(['site', 'site_docs_url'], event.target.value)} /></SettingRow></Col>
                <Col span={12}><SettingRow label={t('onboarding.fields.github_url', 'GitHub URL')}><Input value={config.site.site_github_url} onChange={(event) => updateConfig(['site', 'site_github_url'], event.target.value)} /></SettingRow></Col>
            </Row>
            <Divider>{t('onboarding.sections.report', 'Report settings')}</Divider>
            <SettingRow label={t('onboarding.fields.enable_share', 'Enable public report sharing')}>
                <Switch checked={config.report.enable_public_share} onChange={(checked) => updateConfig(['report', 'enable_public_share'], checked)} />
            </SettingRow>
            {config.report.enable_public_share ? (
                <SettingRow label="REPORT_SHARE_SECRET">
                    <Input.Password value={config.report.report_share_secret} onChange={(event) => updateConfig(['report', 'report_share_secret'], event.target.value)} />
                </SettingRow>
            ) : null}
            <Row gutter={16}>
                <Col span={12}><SettingRow label={t('onboarding.fields.report_max_age_days', 'Report max age (days)')}><InputNumber style={{ width: '100%' }} value={config.report.report_max_age_days} onChange={(value) => updateConfig(['report', 'report_max_age_days'], value ?? 30)} /></SettingRow></Col>
                <Col span={12}><SettingRow label={t('onboarding.fields.output_directory', 'Report output directory')}><Input value={config.report.output_directory} onChange={(event) => updateConfig(['report', 'output_directory'], event.target.value)} /></SettingRow></Col>
            </Row>
            <Divider>{t('onboarding.sections.network', 'Network')}</Divider>
            <Row gutter={16}>
                <Col span={12}><SettingRow label="HTTP_PROXY"><Input value={config.network.http_proxy} onChange={(event) => updateConfig(['network', 'http_proxy'], event.target.value)} /></SettingRow></Col>
                <Col span={12}><SettingRow label="HTTPS_PROXY"><Input value={config.network.https_proxy} onChange={(event) => updateConfig(['network', 'https_proxy'], event.target.value)} /></SettingRow></Col>
            </Row>
        </Card>
    )

    const renderReview = () => <ReviewSummary initialConfig={initialConfig} config={config} t={t} />

    const renderStep = () => {
        switch (currentStep) {
            case 'welcome': return renderWelcome()
            case 'database': return renderDatabase()
            case 'auth': return renderAuth()
            case 'data': return renderData()
            case 'ai': return renderAI()
            case 'trading': return renderTrading()
            case 'brand': return renderBrand()
            case 'review': return renderReview()
            default: return null
        }
    }

    return (
        <div className="onboarding-page">
            <div className="onboarding-sidebar">
                <div className="onboarding-brand">
                    <RocketOutlined />
                    <span>{t('onboarding.title', 'First-Run Setup Wizard')}</span>
                </div>
                <Steps direction="vertical" current={stepIndex} items={steps} />
            </div>
            <div className="onboarding-content">
                {renderStep()}
                <div className="onboarding-actions">
                    <Button disabled={stepIndex === 0} onClick={() => setStepIndex((value) => value - 1)}>
                        {t('onboarding.actions.previous', 'Previous')}
                    </Button>
                    <Space>
                        <Button icon={<SafetyOutlined />} onClick={() => navigate('/')}>
                            {t('onboarding.actions.exit', 'Exit')}
                        </Button>
                        {stepIndex < steps.length - 1 ? (
                            <Button type="primary" onClick={() => validateStep() && setStepIndex((value) => value + 1)}>
                                {t('onboarding.actions.next', 'Next')}
                            </Button>
                        ) : (
                            <Button type="primary" icon={<CheckCircleOutlined />} loading={saving} onClick={handleSave}>
                                {t('onboarding.actions.finish', 'Finish Setup')}
                            </Button>
                        )}
                    </Space>
                </div>
            </div>
        </div>
    )
}
