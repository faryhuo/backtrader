import { useCallback, useEffect, useMemo, useState } from 'react'
import { useNavigate } from 'react-router-dom'
import { useTranslation } from 'react-i18next'
import {
    Alert,
    Button,
    Card,
    Checkbox,
    Col,
    Divider,
    Input,
    InputNumber,
    Radio,
    Row,
    Select,
    Space,
    Spin,
    Steps,
    Switch,
    Tag,
    Tabs,
    Typography,
    message
} from 'antd'
import {
    ArrowDownOutlined,
    ArrowUpOutlined,
    CheckCircleOutlined,
    LoadingOutlined,
    RocketOutlined,
    SafetyOutlined
} from '@ant-design/icons'
import { AI_PROVIDERS } from '../constants/settingsConstants'
import { setupApi } from '../services/setupApi'
import './OnboardingSetup.css'

const { Title, Paragraph, Text } = Typography

const DATA_SOURCES = ['yahoo', 'eodhd', 'database']
const BINANCE_LIVE_API_MANAGEMENT_URL = 'https://www.binance.com/en/my/settings/api-management'
const BINANCE_SPOT_TESTNET_URL = 'https://testnet.binance.vision/'
const BINANCE_API_SECURITY_GUIDE_URL = 'https://www.binance.com/en/academy/articles/what-are-api-keys-and-security-types'

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
        accumulator[provider.key] = { api_key: '', base_url: '', configured: false }
        return accumulator
    }, {})
}

function normalizeWizardConfig(rawConfig) {
    const providerDefaults = createProviderDefaults()
    const mergedProviders = {
        ...providerDefaults,
        ...(rawConfig?.ai?.providers || {})
    }

    return {
        ...rawConfig,
        ai: {
            enabled: rawConfig?.ai?.enabled ?? false,
            provider_priority: rawConfig?.ai?.provider_priority ?? ['openai'],
            providers: mergedProviders
        },
        trading: {
            ...rawConfig?.trading,
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

function SettingRow({ label, hint, children }) {
    return (
        <div className="onboarding-field">
            <div className="onboarding-field-header">
                <Text strong>{label}</Text>
                {hint ? <Text type="secondary">{hint}</Text> : null}
            </div>
            {children}
        </div>
    )
}

function ProviderPriorityItem({ provider, index, total, onMove }) {
    const label = AI_PROVIDERS.find((item) => item.key === provider)?.label || provider

    return (
        <div className="onboarding-priority-item">
            <Space>
                <Tag color="processing">{index + 1}</Tag>
                <Text>{label}</Text>
            </Space>
            <Space>
                <Button
                    size="small"
                    icon={<ArrowUpOutlined />}
                    disabled={index === 0}
                    onClick={() => onMove(provider, 'up')}
                />
                <Button
                    size="small"
                    icon={<ArrowDownOutlined />}
                    disabled={index === total - 1}
                    onClick={() => onMove(provider, 'down')}
                />
            </Space>
        </div>
    )
}

function BinanceApiGuide({ t, mode }) {
    const isPaper = mode === 'paper'
    const title = isPaper
        ? t('onboarding.sections.paper_api_guide', 'Binance paper guide')
        : t('onboarding.sections.live_api_guide', 'Binance live guide')
    const intro = isPaper
        ? t('onboarding.guide.paper_intro', 'Use Binance Spot Test Network to generate sandbox credentials for paper mode, then keep the sandbox URL and credentials in the paper configuration below.')
        : t('onboarding.guide.live_intro', 'Create the key from Binance API Management, enable only the permissions you actually need, then lock it down with IP restrictions before pasting it back here.')
    const steps = isPaper
        ? [
            t('onboarding.guide.paper_step_1', 'Open Binance Spot Test Network and sign in with a supported account to access the sandbox environment.'),
            t('onboarding.guide.paper_step_2', 'Generate a sandbox API key and secret from the testnet page, then copy both values immediately.'),
            t('onboarding.guide.paper_step_3', 'Keep the sandbox URL set to https://testnet.binance.vision and use these credentials only for paper mode.'),
            t('onboarding.guide.paper_step_4', 'Do not reuse live exchange keys here. Paper mode should stay isolated from your real trading account.'),
            t('onboarding.guide.paper_step_5', 'Paste the sandbox key pair into the paper tab below and run the paper test against testnet.')
        ]
        : [
            t('onboarding.guide.live_step_1', 'Open Binance API Management and click Create API, then choose a system-generated key.'),
            t('onboarding.guide.live_step_2', 'Complete Binance security verification and copy the API Key and Secret Key immediately.'),
            t('onboarding.guide.live_step_3', 'Enable only the permissions you need. For this app, keep Enable Reading on; enable Spot & Margin Trading only if you plan to place live orders.'),
            t('onboarding.guide.live_step_4', 'In API restrictions, set Restrict access to trusted IPs only and add the server public IP that will run this platform.'),
            t('onboarding.guide.live_step_5', 'Use separate keys for separate environments when possible, then paste the key pair here and run the live test button.')
        ]
    const primaryHref = isPaper ? BINANCE_SPOT_TESTNET_URL : BINANCE_LIVE_API_MANAGEMENT_URL
    const primaryLabel = isPaper
        ? t('onboarding.actions.open_binance_testnet', 'Open Binance Spot Test Network')
        : t('onboarding.actions.create_binance_api', 'Create Binance API Key')
    const warningTitle = isPaper
        ? t('onboarding.guide.paper_warning_title', 'Paper mode checklist')
        : t('onboarding.guide.live_warning_title', 'Security checklist')
    const warningDescription = isPaper
        ? t('onboarding.guide.paper_warning', 'Sandbox credentials are for paper mode only. Keep live credentials out of the paper tab, and leave the sandbox URL pointed at Binance Spot Test Network.')
        : t('onboarding.guide.live_warning', 'Binance recommends enabling only required permissions, storing secrets outside source control, rotating keys regularly, and deleting or replacing a key immediately if it may have been exposed.')

    return (
        <Card size="small" className="onboarding-nested-card" title={title}>
            <Space direction="vertical" style={{ width: '100%' }} size="middle">
                <Paragraph style={{ marginBottom: 0 }}>
                    {intro}
                </Paragraph>
                <Space wrap>
                    <Button type="primary" href={primaryHref} target="_blank" rel="noreferrer">
                        {primaryLabel}
                    </Button>
                    <Button href={BINANCE_API_SECURITY_GUIDE_URL} target="_blank" rel="noreferrer">
                        {t('onboarding.actions.open_binance_security_guide', 'Open Binance permissions guide')}
                    </Button>
                </Space>
                <ol className="onboarding-guide-list">
                    {steps.map((step) => <li key={step}>{step}</li>)}
                </ol>
                <Alert
                    type="warning"
                    showIcon
                    message={warningTitle}
                    description={warningDescription}
                />
            </Space>
        </Card>
    )
}

function areValuesEqual(left, right) {
    return JSON.stringify(left ?? null) === JSON.stringify(right ?? null)
}

function formatReviewValue(value, t) {
    if (value === true) {
        return t('onboarding.review.values.enabled', 'Enabled')
    }
    if (value === false) {
        return t('onboarding.review.values.disabled', 'Disabled')
    }
    if (value === null || value === undefined || value === '') {
        return t('onboarding.review.values.not_set', 'Not set')
    }
    if (Array.isArray(value)) {
        return value.length > 0 ? value.join(' > ') : t('onboarding.review.values.none', 'None')
    }
    return String(value)
}

function summarizeEncryptionState(currentValue, baselineValue, t) {
    if (!currentValue) {
        return t('onboarding.review.values.not_set', 'Not set')
    }
    if (!baselineValue) {
        return t('onboarding.review.values.configured', 'Configured')
    }
    if (currentValue === baselineValue) {
        return t('onboarding.review.values.configured', 'Configured')
    }
    return t('onboarding.review.values.updated', 'Updated')
}

function summarizeCredentialState(credentials, t) {
    if (credentials?.api_key && credentials?.secret) {
        return t('onboarding.review.values.configured', 'Configured')
    }
    return t('onboarding.review.values.not_configured', 'Not configured')
}

function summarizeDatabaseTarget(databaseConfig, t) {
    if (databaseConfig?.mode === 'postgresql') {
        const host = databaseConfig?.postgresql?.host || t('onboarding.review.values.not_set', 'Not set')
        const port = databaseConfig?.postgresql?.port || 5432
        const database = databaseConfig?.postgresql?.database || t('onboarding.review.values.not_set', 'Not set')
        return `${host}:${port}/${database}`
    }
    return databaseConfig?.sqlite_path || t('onboarding.review.values.not_set', 'Not set')
}

function summarizeAiPriority(aiConfig, t) {
    if (!aiConfig?.enabled) {
        return t('onboarding.review.values.disabled', 'Disabled')
    }
    const providers = aiConfig?.provider_priority || []
    if (providers.length === 0) {
        return t('onboarding.review.values.none', 'None')
    }
    return providers.map((providerKey) => AI_PROVIDERS.find((item) => item.key === providerKey)?.label || providerKey).join(' > ')
}

function summarizeConfiguredAiProviders(aiConfig, t) {
    if (!aiConfig?.enabled) {
        return t('onboarding.review.values.disabled', 'Disabled')
    }
    const configuredProviders = AI_PROVIDERS
        .filter((provider) => Boolean(aiConfig?.providers?.[provider.key]?.api_key))
        .map((provider) => provider.label)
    if (configuredProviders.length === 0) {
        return t('onboarding.review.values.none', 'None')
    }
    return configuredProviders.join(', ')
}

function summarizeProxyState(networkConfig, t) {
    if (networkConfig?.http_proxy || networkConfig?.https_proxy) {
        return t('onboarding.review.values.configured', 'Configured')
    }
    return t('onboarding.review.values.not_configured', 'Not configured')
}

function createReviewItem({ label, before, after, changed }) {
    return { label, before, after, changed }
}

function buildReviewSections(baselineConfig, currentConfig, t) {
    if (!baselineConfig || !currentConfig) {
        return []
    }

    const sections = [
        {
            key: 'security',
            title: t('onboarding.review.sections.security', 'Security & access'),
            items: [
                createReviewItem({
                    label: t('onboarding.review.fields.deployment_mode', 'Deployment mode'),
                    before: formatReviewValue(baselineConfig.deployment_mode, t),
                    after: formatReviewValue(currentConfig.deployment_mode, t),
                    changed: !areValuesEqual(baselineConfig.deployment_mode, currentConfig.deployment_mode)
                }),
                createReviewItem({
                    label: t('onboarding.review.fields.encryption_key', 'Encryption key'),
                    before: summarizeEncryptionState(baselineConfig?.security?.encryption_key, baselineConfig?.security?.encryption_key, t),
                    after: summarizeEncryptionState(currentConfig?.security?.encryption_key, baselineConfig?.security?.encryption_key, t),
                    changed: !areValuesEqual(baselineConfig?.security?.encryption_key, currentConfig?.security?.encryption_key)
                }),
                createReviewItem({
                    label: t('onboarding.fields.enable_login', 'Enable login'),
                    before: formatReviewValue(baselineConfig?.security?.enable_login, t),
                    after: formatReviewValue(currentConfig?.security?.enable_login, t),
                    changed: !areValuesEqual(baselineConfig?.security?.enable_login, currentConfig?.security?.enable_login)
                }),
                createReviewItem({
                    label: t('onboarding.review.fields.logto_issuer', 'Logto issuer'),
                    before: formatReviewValue(baselineConfig?.auth?.logto_issuer, t),
                    after: formatReviewValue(currentConfig?.auth?.logto_issuer, t),
                    changed: !areValuesEqual(baselineConfig?.auth?.logto_issuer, currentConfig?.auth?.logto_issuer)
                }),
                createReviewItem({
                    label: t('onboarding.review.fields.logto_app_id', 'Logto app ID'),
                    before: formatReviewValue(baselineConfig?.auth?.logto_app_id, t),
                    after: formatReviewValue(currentConfig?.auth?.logto_app_id, t),
                    changed: !areValuesEqual(baselineConfig?.auth?.logto_app_id, currentConfig?.auth?.logto_app_id)
                })
            ].filter((item) => item.changed)
        },
        {
            key: 'storage',
            title: t('onboarding.review.sections.storage', 'Storage & data'),
            items: [
                createReviewItem({
                    label: t('onboarding.fields.database_mode', 'Database mode'),
                    before: formatReviewValue(baselineConfig?.database?.mode, t),
                    after: formatReviewValue(currentConfig?.database?.mode, t),
                    changed: !areValuesEqual(baselineConfig?.database?.mode, currentConfig?.database?.mode)
                }),
                createReviewItem({
                    label: t('onboarding.review.fields.database_target', 'Database target'),
                    before: summarizeDatabaseTarget(baselineConfig?.database, t),
                    after: summarizeDatabaseTarget(currentConfig?.database, t),
                    changed: !areValuesEqual(baselineConfig?.database, currentConfig?.database)
                }),
                createReviewItem({
                    label: t('onboarding.review.fields.data_sources', 'Data sources'),
                    before: formatReviewValue(baselineConfig?.data_source?.priority, t),
                    after: formatReviewValue(currentConfig?.data_source?.priority, t),
                    changed: !areValuesEqual(baselineConfig?.data_source?.priority, currentConfig?.data_source?.priority)
                }),
                createReviewItem({
                    label: t('onboarding.review.fields.eodhd_key', 'EODHD API key'),
                    before: summarizeEncryptionState(baselineConfig?.data_source?.eodhd_api_key, baselineConfig?.data_source?.eodhd_api_key, t),
                    after: summarizeEncryptionState(currentConfig?.data_source?.eodhd_api_key, baselineConfig?.data_source?.eodhd_api_key, t),
                    changed: !areValuesEqual(baselineConfig?.data_source?.eodhd_api_key, currentConfig?.data_source?.eodhd_api_key)
                })
            ].filter((item) => item.changed)
        },
        {
            key: 'ai',
            title: t('onboarding.review.sections.ai', 'AI'),
            items: [
                createReviewItem({
                    label: t('onboarding.fields.enable_ai', 'Enable AI analysis'),
                    before: formatReviewValue(baselineConfig?.ai?.enabled, t),
                    after: formatReviewValue(currentConfig?.ai?.enabled, t),
                    changed: !areValuesEqual(baselineConfig?.ai?.enabled, currentConfig?.ai?.enabled)
                }),
                createReviewItem({
                    label: t('onboarding.review.fields.ai_priority', 'Provider priority'),
                    before: summarizeAiPriority(baselineConfig?.ai, t),
                    after: summarizeAiPriority(currentConfig?.ai, t),
                    changed: !areValuesEqual(baselineConfig?.ai?.provider_priority, currentConfig?.ai?.provider_priority)
                }),
                createReviewItem({
                    label: t('onboarding.review.fields.ai_credentials', 'Configured providers'),
                    before: summarizeConfiguredAiProviders(baselineConfig?.ai, t),
                    after: summarizeConfiguredAiProviders(currentConfig?.ai, t),
                    changed: !areValuesEqual(
                        AI_PROVIDERS.map((provider) => Boolean(baselineConfig?.ai?.providers?.[provider.key]?.api_key)),
                        AI_PROVIDERS.map((provider) => Boolean(currentConfig?.ai?.providers?.[provider.key]?.api_key))
                    )
                })
            ].filter((item) => item.changed)
        },
        {
            key: 'trading',
            title: t('onboarding.review.sections.trading', 'Trading'),
            items: [
                createReviewItem({
                    label: t('onboarding.review.fields.live_entry', 'Live trading entry'),
                    before: formatReviewValue(baselineConfig?.trading?.live_trading_enabled, t),
                    after: formatReviewValue(currentConfig?.trading?.live_trading_enabled, t),
                    changed: !areValuesEqual(baselineConfig?.trading?.live_trading_enabled, currentConfig?.trading?.live_trading_enabled)
                }),
                createReviewItem({
                    label: t('onboarding.fields.default_trade_mode', 'Default trade mode'),
                    before: formatReviewValue(baselineConfig?.trading?.default_trade_mode, t),
                    after: formatReviewValue(currentConfig?.trading?.default_trade_mode, t),
                    changed: !areValuesEqual(baselineConfig?.trading?.default_trade_mode, currentConfig?.trading?.default_trade_mode)
                }),
                createReviewItem({
                    label: t('onboarding.fields.default_market', 'Default market'),
                    before: formatReviewValue(baselineConfig?.trading?.binance?.default_market, t),
                    after: formatReviewValue(currentConfig?.trading?.binance?.default_market, t),
                    changed: !areValuesEqual(baselineConfig?.trading?.binance?.default_market, currentConfig?.trading?.binance?.default_market)
                }),
                createReviewItem({
                    label: t('onboarding.review.fields.paper_credentials', 'Binance paper credentials'),
                    before: summarizeCredentialState(baselineConfig?.trading?.credentials?.paper, t),
                    after: summarizeCredentialState(currentConfig?.trading?.credentials?.paper, t),
                    changed: !areValuesEqual(baselineConfig?.trading?.credentials?.paper, currentConfig?.trading?.credentials?.paper)
                }),
                createReviewItem({
                    label: t('onboarding.review.fields.live_credentials', 'Binance live credentials'),
                    before: summarizeCredentialState(baselineConfig?.trading?.credentials?.live, t),
                    after: summarizeCredentialState(currentConfig?.trading?.credentials?.live, t),
                    changed: !areValuesEqual(baselineConfig?.trading?.credentials?.live, currentConfig?.trading?.credentials?.live)
                }),
                createReviewItem({
                    label: t('onboarding.review.fields.risk_acknowledgement', 'Live risk acknowledgement'),
                    before: formatReviewValue(baselineConfig?.trading?.live_risk_acknowledged, t),
                    after: formatReviewValue(currentConfig?.trading?.live_risk_acknowledged, t),
                    changed: !areValuesEqual(baselineConfig?.trading?.live_risk_acknowledged, currentConfig?.trading?.live_risk_acknowledged)
                })
            ].filter((item) => item.changed)
        },
        {
            key: 'brand',
            title: t('onboarding.review.sections.brand', 'Brand & report'),
            items: [
                createReviewItem({
                    label: t('onboarding.fields.site_title', 'Site title'),
                    before: formatReviewValue(baselineConfig?.site?.site_title, t),
                    after: formatReviewValue(currentConfig?.site?.site_title, t),
                    changed: !areValuesEqual(baselineConfig?.site?.site_title, currentConfig?.site?.site_title)
                }),
                createReviewItem({
                    label: t('onboarding.fields.enable_share', 'Enable public report sharing'),
                    before: formatReviewValue(baselineConfig?.report?.enable_public_share, t),
                    after: formatReviewValue(currentConfig?.report?.enable_public_share, t),
                    changed: !areValuesEqual(baselineConfig?.report?.enable_public_share, currentConfig?.report?.enable_public_share)
                }),
                createReviewItem({
                    label: t('onboarding.fields.report_max_age_days', 'Report max age (days)'),
                    before: formatReviewValue(baselineConfig?.report?.report_max_age_days, t),
                    after: formatReviewValue(currentConfig?.report?.report_max_age_days, t),
                    changed: !areValuesEqual(baselineConfig?.report?.report_max_age_days, currentConfig?.report?.report_max_age_days)
                }),
                createReviewItem({
                    label: t('onboarding.fields.output_directory', 'Report output directory'),
                    before: formatReviewValue(baselineConfig?.report?.output_directory, t),
                    after: formatReviewValue(currentConfig?.report?.output_directory, t),
                    changed: !areValuesEqual(baselineConfig?.report?.output_directory, currentConfig?.report?.output_directory)
                }),
                createReviewItem({
                    label: t('onboarding.review.fields.proxy', 'Proxy'),
                    before: summarizeProxyState(baselineConfig?.network, t),
                    after: summarizeProxyState(currentConfig?.network, t),
                    changed: !areValuesEqual(
                        [baselineConfig?.network?.http_proxy, baselineConfig?.network?.https_proxy],
                        [currentConfig?.network?.http_proxy, currentConfig?.network?.https_proxy]
                    )
                })
            ].filter((item) => item.changed)
        }
    ]

    return sections.filter((section) => section.items.length > 0)
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
    const [activeTradingTab, setActiveTradingTab] = useState('paper')

    const loadWizard = useCallback(async () => {
        setLoading(true)
        try {
            const response = await setupApi.getSetupWizard()
            const normalizedConfig = normalizeWizardConfig(response.config)
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

    const steps = useMemo(() => {
        const base = [
            { key: 'welcome', title: t('onboarding.steps.welcome', 'Welcome') },
            { key: 'security', title: t('onboarding.steps.security', 'Security') },
            { key: 'database', title: t('onboarding.steps.database', 'Database') }
        ]
        if (config?.security?.enable_login) {
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
    }, [config?.security?.enable_login, t])

    useEffect(() => {
        setStepIndex((current) => Math.min(current, Math.max(steps.length - 1, 0)))
    }, [steps.length])

    const currentStep = steps[stepIndex]?.key

    const updateConfig = (path, value) => {
        setConfig((previous) => setValueAtPath(previous, path, value))
    }

    const enabledProviders = config?.ai?.provider_priority || []
    const reviewSections = useMemo(() => buildReviewSections(initialConfig, config, t), [config, initialConfig, t])
    const changedItemCount = reviewSections.reduce((total, section) => total + section.items.length, 0)

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
        if (currentStep === 'security' && !config.security.encryption_key) {
            message.warning(t('onboarding.validation.encryption_key', 'Encryption key is required.'))
            return false
        }
        if (currentStep === 'database' && config.database.mode === 'sqlite' && !config.database.sqlite_path) {
            message.warning(t('onboarding.validation.sqlite_path', 'SQLite path is required.'))
            return false
        }
        if (currentStep === 'auth' && config.security.enable_login) {
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
        if (currentStep === 'data' && config.data_source.priority.includes('eodhd') && !config.data_source.eodhd_api_key) {
            message.warning(t('onboarding.validation.eodhd', 'EODHD API key is required when EODHD is enabled.'))
            return false
        }
        if (currentStep === 'ai' && config.ai.enabled) {
            if (enabledProviders.length === 0) {
                message.warning(t('onboarding.validation.ai_provider', 'Enable at least one AI provider.'))
                return false
            }
            const missingProviders = enabledProviders.filter((provider) => {
                return !config.ai.providers?.[provider]?.api_key
            })
            if (missingProviders.length > 0) {
                message.warning(
                    t('onboarding.validation.ai_provider_keys', 'API key is required for all enabled AI providers.')
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
            if (config.trading.default_trade_mode === 'live' && !config.trading.live_trading_enabled) {
                message.warning(t('onboarding.validation.live_mode', 'Enable live trading before selecting live as the default mode.'))
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
            await setupApi.saveSetupWizard(config)
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
                    description={t('onboarding.milestone_desc', 'This wizard focuses on backend bootstrap settings: security, storage, data source, AI, Binance trading, branding, and review.')}
                />
            </Space>
        </Card>
    )

    const renderSecurity = () => (
        <Card className="onboarding-card">
            <SettingRow
                label={t('onboarding.fields.encryption_key', 'ENCRYPTION_KEY')}
                hint={t('onboarding.hints.encryption_key', 'Changing this later can make previously encrypted credentials unreadable.')}
            >
                <Space.Compact style={{ width: '100%' }}>
                    <Input.Password
                        value={config.security.encryption_key}
                        onChange={(event) => updateConfig(['security', 'encryption_key'], event.target.value)}
                    />
                    <Button onClick={() => updateConfig(['security', 'encryption_key'], wizardState.meta.generated_encryption_key)}>
                        {t('onboarding.actions.generate', 'Generate')}
                    </Button>
                </Space.Compact>
            </SettingRow>
            <SettingRow
                label={t('onboarding.fields.enable_login', 'Enable login')}
                hint={t('onboarding.hints.enable_login', 'When disabled, the app stays accessible without authentication.')}
            >
                <Switch
                    checked={config.security.enable_login}
                    onChange={(checked) => updateConfig(['security', 'enable_login'], checked)}
                />
            </SettingRow>
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
        <Card className="onboarding-card">
            <SettingRow label={t('onboarding.fields.data_priority', 'Enabled data sources')}>
                <Checkbox.Group
                    value={config.data_source.priority}
                    options={DATA_SOURCES}
                    onChange={(values) => updateConfig(['data_source', 'priority'], values)}
                />
            </SettingRow>
            {config.data_source.priority.includes('eodhd') ? (
                <SettingRow label="EODHD_API_KEY">
                    <Input.Password value={config.data_source.eodhd_api_key} onChange={(event) => updateConfig(['data_source', 'eodhd_api_key'], event.target.value)} />
                </SettingRow>
            ) : null}
        </Card>
    )

    const renderAI = () => (
        <Card className="onboarding-card">
            <SettingRow
                label={t('onboarding.fields.enable_ai', 'Enable AI analysis')}
                hint={t('onboarding.hints.enable_ai', 'AI is optional. Leaving it disabled keeps analysis features unavailable.')}
            >
                <Switch checked={config.ai.enabled} onChange={(checked) => updateConfig(['ai', 'enabled'], checked)} />
            </SettingRow>
            <Alert
                type="info"
                showIcon
                message={t('onboarding.ai_note', 'The wizard stores provider credentials and fallback priority. Runtime model names can be configured later in Settings.')}
                style={{ marginBottom: 20 }}
            />
            {config.ai.enabled ? (
                <>
                    <Card size="small" className="onboarding-nested-card" title={t('onboarding.sections.ai_priority', 'Provider priority')}>
                        <Space direction="vertical" style={{ width: '100%' }}>
                            {enabledProviders.length === 0 ? (
                                <Text type="secondary">{t('onboarding.ai_empty', 'Enable at least one provider to define fallback order.')}</Text>
                            ) : enabledProviders.map((provider, index) => (
                                <ProviderPriorityItem
                                    key={provider}
                                    provider={provider}
                                    index={index}
                                    total={enabledProviders.length}
                                    onMove={reorderProvider}
                                />
                            ))}
                        </Space>
                    </Card>
                    {AI_PROVIDERS.map((provider) => {
                        const providerConfig = config.ai.providers?.[provider.key] || {}
                        const providerEnabled = enabledProviders.includes(provider.key)
                        const testKey = `ai:${provider.key}`
                        return (
                            <Card key={provider.key} size="small" className="onboarding-nested-card" title={provider.label}>
                                <Space direction="vertical" style={{ width: '100%' }}>
                                    <Switch
                                        checked={providerEnabled}
                                        onChange={(checked) => toggleProvider(provider.key, checked)}
                                        checkedChildren={t('onboarding.enabled', 'Enabled')}
                                        unCheckedChildren={t('onboarding.disabled', 'Disabled')}
                                    />
                                    <SettingRow label={t('onboarding.fields.api_key', 'API key')}>
                                        <Input.Password
                                            value={providerConfig.api_key}
                                            onChange={(event) => updateConfig(['ai', 'providers', provider.key, 'api_key'], event.target.value)}
                                        />
                                    </SettingRow>
                                    <SettingRow label={t('onboarding.fields.base_url', 'Base URL')}>
                                        <Input
                                            value={providerConfig.base_url}
                                            onChange={(event) => updateConfig(['ai', 'providers', provider.key, 'base_url'], event.target.value)}
                                        />
                                    </SettingRow>
                                    <Button
                                        onClick={() => testConnection('ai_model', {
                                            provider: provider.key,
                                            api_key: providerConfig.api_key,
                                            base_url: providerConfig.base_url
                                        }, testKey)}
                                        loading={testing === testKey}
                                    >
                                        {t('onboarding.actions.test_provider', 'Test provider')}
                                    </Button>
                                </Space>
                            </Card>
                        )
                    })}
                </>
            ) : null}
        </Card>
    )

    const renderTrading = () => (
        <Card className="onboarding-card">
            <Alert
                type="warning"
                showIcon
                message={t('onboarding.trading_note', 'The onboarding flow only supports Binance and lets you configure paper and live credentials together.')}
                style={{ marginBottom: 20 }}
            />
            <Row gutter={16}>
                <Col span={12}>
                    <SettingRow
                        label={t('onboarding.fields.enabled', 'Enabled')}
                    >
                        <Switch
                            checked={config.trading.binance.enabled}
                            onChange={(checked) => updateConfig(['trading', 'binance', 'enabled'], checked)}
                        />
                    </SettingRow>
                </Col>
                <Col span={12}>
                    <SettingRow label={t('onboarding.fields.default_trade_mode', 'Default trade mode')}>
                        <Select
                            value={config.trading.default_trade_mode}
                            options={[
                                { value: 'paper', label: 'paper' },
                                { value: 'live', label: 'live' }
                            ]}
                            onChange={(value) => updateConfig(['trading', 'default_trade_mode'], value)}
                        />
                    </SettingRow>
                </Col>
            </Row>
            <Card size="small" className="onboarding-nested-card" title="Binance">
                <Row gutter={16}>
                    <Col span={12}><SettingRow label={t('onboarding.fields.default_market', 'Default market')}><Input value={config.trading.binance.default_market} onChange={(event) => updateConfig(['trading', 'binance', 'default_market'], event.target.value)} /></SettingRow></Col>
                    <Col span={12}><SettingRow label={t('onboarding.fields.default_exchange', 'Default exchange')}><Input value="binance" disabled /></SettingRow></Col>
                </Row>
            </Card>
            <Divider>{t('onboarding.sections.trading_modes', 'Paper and live setup')}</Divider>
            <Tabs
                className="onboarding-mode-tabs"
                activeKey={activeTradingTab}
                onChange={setActiveTradingTab}
                items={[
                    {
                        key: 'paper',
                        label: t('onboarding.tabs.paper', 'Paper'),
                        children: (
                            <Space direction="vertical" style={{ width: '100%' }} size="middle">
                                <BinanceApiGuide t={t} mode="paper" />
                                <Card size="small" className="onboarding-nested-card" title={t('onboarding.sections.paper_config', 'Paper configuration')}>
                                    <Row gutter={16}>
                                        <Col xs={24} md={12}><SettingRow label={t('onboarding.fields.paper_enabled', 'Paper mode enabled')}><Switch checked={config.trading.binance.paper_enabled} onChange={(checked) => updateConfig(['trading', 'binance', 'paper_enabled'], checked)} /></SettingRow></Col>
                                        <Col xs={24} md={12}><SettingRow label={t('onboarding.fields.paper_balance', 'Paper balance (USDT)')}><InputNumber style={{ width: '100%' }} value={config.trading.binance.initial_balance_usdt} onChange={(value) => updateConfig(['trading', 'binance', 'initial_balance_usdt'], value ?? 10000)} /></SettingRow></Col>
                                        <Col span={24}><SettingRow label={t('onboarding.fields.sandbox_url', 'Sandbox URL')}><Input value={config.trading.binance.sandbox_url} onChange={(event) => updateConfig(['trading', 'binance', 'sandbox_url'], event.target.value)} /></SettingRow></Col>
                                    </Row>
                                </Card>
                                <Card size="small" className="onboarding-nested-card" title={t('onboarding.sections.paper_credentials', 'Binance paper')}>
                                    <Space direction="vertical" style={{ width: '100%' }}>
                                        <SettingRow label={t('onboarding.fields.api_key', 'API key')}>
                                            <Input.Password value={config.trading.credentials.paper.api_key} onChange={(event) => updateConfig(['trading', 'credentials', 'paper', 'api_key'], event.target.value)} />
                                        </SettingRow>
                                        <SettingRow label={t('onboarding.fields.secret', 'Secret')}>
                                            <Input.Password value={config.trading.credentials.paper.secret} onChange={(event) => updateConfig(['trading', 'credentials', 'paper', 'secret'], event.target.value)} />
                                        </SettingRow>
                                        <Button
                                            onClick={() => testConnection('ccxt', {
                                                exchange: 'binance',
                                                mode: 'paper',
                                                api_key: config.trading.credentials.paper.api_key,
                                                secret: config.trading.credentials.paper.secret,
                                                use_testnet: true
                                            }, 'ccxt:paper')}
                                            loading={testing === 'ccxt:paper'}
                                        >
                                            {t('onboarding.actions.test_paper', 'Test paper')}
                                        </Button>
                                    </Space>
                                </Card>
                            </Space>
                        )
                    },
                    {
                        key: 'live',
                        label: t('onboarding.tabs.live', 'Live'),
                        children: (
                            <Space direction="vertical" style={{ width: '100%' }} size="middle">
                                <BinanceApiGuide t={t} mode="live" />
                                <Card size="small" className="onboarding-nested-card" title={t('onboarding.sections.live_config', 'Live configuration')}>
                                    <Row gutter={16}>
                                        <Col xs={24} md={12}>
                                            <SettingRow
                                                label={t('onboarding.fields.enable_trading', 'Enable live trading entry')}
                                                hint={t('onboarding.hints.enable_trading', 'Prefer paper mode first. Live mode requires explicit acknowledgement and full credentials.')}
                                            >
                                                <Switch
                                                    checked={config.trading.live_trading_enabled}
                                                    onChange={(checked) => updateConfig(['trading', 'live_trading_enabled'], checked)}
                                                />
                                            </SettingRow>
                                        </Col>
                                    </Row>
                                    {(config.trading.live_trading_enabled || config.trading.default_trade_mode === 'live') ? (
                                        <Checkbox checked={config.trading.live_risk_acknowledged} onChange={(event) => updateConfig(['trading', 'live_risk_acknowledged'], event.target.checked)}>
                                            {t('onboarding.live_ack', 'I understand live trading can place real orders and accept that risk.')}
                                        </Checkbox>
                                    ) : null}
                                </Card>
                                <Card size="small" className="onboarding-nested-card" title={t('onboarding.sections.live_credentials', 'Binance live')}>
                                    <Space direction="vertical" style={{ width: '100%' }}>
                                        <SettingRow label={t('onboarding.fields.api_key', 'API key')}>
                                            <Input.Password value={config.trading.credentials.live.api_key} onChange={(event) => updateConfig(['trading', 'credentials', 'live', 'api_key'], event.target.value)} />
                                        </SettingRow>
                                        <SettingRow label={t('onboarding.fields.secret', 'Secret')}>
                                            <Input.Password value={config.trading.credentials.live.secret} onChange={(event) => updateConfig(['trading', 'credentials', 'live', 'secret'], event.target.value)} />
                                        </SettingRow>
                                        <Button
                                            onClick={() => testConnection('ccxt', {
                                                exchange: 'binance',
                                                mode: 'live',
                                                api_key: config.trading.credentials.live.api_key,
                                                secret: config.trading.credentials.live.secret,
                                                use_testnet: false
                                            }, 'ccxt:live')}
                                            loading={testing === 'ccxt:live'}
                                        >
                                            {t('onboarding.actions.test_live', 'Test live')}
                                        </Button>
                                    </Space>
                                </Card>
                            </Space>
                        )
                    }
                ]}
            />
        </Card>
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

    const renderReview = () => (
        <Card className="onboarding-card">
            <Alert
                type="info"
                showIcon
                message={t('onboarding.review_title', 'Review before saving')}
                description={t('onboarding.review_desc', 'This page summarizes what changed in your setup so you can confirm the effective configuration before saving.')}
            />
            <Divider />
            <Row gutter={[16, 16]} className="onboarding-review-stats">
                <Col xs={24} md={12}>
                    <Card size="small" className="onboarding-nested-card onboarding-review-stat-card">
                        <Text type="secondary">{t('onboarding.review.metrics.changed_areas', 'Changed areas')}</Text>
                        <Title level={3} style={{ margin: 0 }}>{reviewSections.length}</Title>
                    </Card>
                </Col>
                <Col xs={24} md={12}>
                    <Card size="small" className="onboarding-nested-card onboarding-review-stat-card">
                        <Text type="secondary">{t('onboarding.review.metrics.changed_items', 'Changed items')}</Text>
                        <Title level={3} style={{ margin: 0 }}>{changedItemCount}</Title>
                    </Card>
                </Col>
            </Row>
            <Divider />
            {reviewSections.length === 0 ? (
                <Alert
                    type="success"
                    showIcon
                    message={t('onboarding.review.no_changes_title', 'No unsaved setup changes')}
                    description={t('onboarding.review.no_changes_desc', 'Your current selections match the saved bootstrap configuration.')}
                    style={{ marginBottom: 20 }}
                />
            ) : (
                <Space direction="vertical" size="middle" style={{ width: '100%', marginBottom: 20 }}>
                    {reviewSections.map((section) => (
                        <Card
                            key={section.key}
                            size="small"
                            className="onboarding-nested-card"
                            title={section.title}
                            extra={<Tag color="processing">{`${section.items.length} ${t('onboarding.review.metrics.items_label', 'items')}`}</Tag>}
                        >
                            <div className="onboarding-review-items">
                                {section.items.map((item) => (
                                    <div key={`${section.key}-${item.label}`} className="onboarding-review-item">
                                        <Text strong>{item.label}</Text>
                                        <div className="onboarding-review-item-values">
                                            <Tag>{item.before}</Tag>
                                            <Text type="secondary">to</Text>
                                            <Tag color="processing">{item.after}</Tag>
                                        </div>
                                    </div>
                                ))}
                            </div>
                        </Card>
                    ))}
                </Space>
            )}
            <Space wrap>
                <Tag color={config.security.enable_login ? 'processing' : 'default'}>{config.security.enable_login ? 'Logto enabled' : 'Login disabled'}</Tag>
                <Tag color={config.ai.enabled ? 'success' : 'default'}>{config.ai.enabled ? `AI: ${enabledProviders.join(' > ')}` : 'AI skipped'}</Tag>
                <Tag color={config.trading.live_trading_enabled ? 'warning' : 'default'}>{config.trading.live_trading_enabled ? 'Binance live enabled' : 'Binance live skipped'}</Tag>
                <Tag color={config.report.enable_public_share ? 'processing' : 'default'}>{config.report.enable_public_share ? 'Public reports enabled' : 'Public reports skipped'}</Tag>
            </Space>
        </Card>
    )

    const renderStep = () => {
        switch (currentStep) {
            case 'welcome': return renderWelcome()
            case 'security': return renderSecurity()
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
