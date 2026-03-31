import { useMemo } from 'react'
import {
    Alert,
    Card,
    Col,
    Divider,
    Row,
    Space,
    Tag,
    Typography
} from 'antd'

const { Title, Text } = Typography

const SECTION_ORDER = ['security', 'storage', 'ai', 'trading', 'brand', 'other']
const SENSITIVE_KEYS = new Set(['encryption_key', 'password', 'api_key', 'secret', 'report_share_secret'])

function areValuesEqual(left, right) {
    return JSON.stringify(left ?? null) === JSON.stringify(right ?? null)
}

function isPlainObject(value) {
    return Boolean(value) && typeof value === 'object' && !Array.isArray(value)
}

function lastPathSegment(path) {
    return path.split('.').at(-1) || ''
}

function shouldIgnorePath(path) {
    const segment = lastPathSegment(path)
    return segment === 'configured' || segment.endsWith('_configured')
}

function isSensitivePath(path) {
    return SENSITIVE_KEYS.has(lastPathSegment(path))
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
    if (isPlainObject(value)) {
        return JSON.stringify(value)
    }
    return String(value)
}

function formatDeploymentMode(value, t) {
    if (value === 'public') {
        return t('onboarding.deployment.public', 'Public deployment with stricter auth expectations')
    }
    if (value === 'local') {
        return t('onboarding.deployment.local', 'Local development or single-machine install')
    }
    return formatReviewValue(value, t)
}

function summarizeSensitiveState(currentValue, baselineValue, t) {
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

function formatPathValue(path, value, baselineValue, t) {
    if (path === 'deployment_mode') {
        return formatDeploymentMode(value, t)
    }
    if (isSensitivePath(path)) {
        return summarizeSensitiveState(value, baselineValue, t)
    }
    return formatReviewValue(value, t)
}

function buildPreviewValue(path, value, baselineValue, t) {
    if (path === 'deployment_mode') {
        return value
    }
    if (isSensitivePath(path)) {
        return summarizeSensitiveState(value, baselineValue, t)
    }
    return value
}

function sectionTitle(sectionKey, t) {
    switch (sectionKey) {
        case 'security':
            return t('onboarding.review.sections.security', 'Security & access')
        case 'storage':
            return t('onboarding.review.sections.storage', 'Storage & data')
        case 'ai':
            return t('onboarding.review.sections.ai', 'AI')
        case 'trading':
            return t('onboarding.review.sections.trading', 'Trading')
        case 'brand':
            return t('onboarding.review.sections.brand', 'Brand & report')
        default:
            return t('onboarding.review.sections.other', 'Other overrides')
    }
}

function resolveSectionKey(path) {
    const root = path.split('.')[0]
    if (root === 'deployment_mode' || root === 'security' || root === 'auth') {
        return 'security'
    }
    if (root === 'database' || root === 'data_source') {
        return 'storage'
    }
    if (root === 'ai') {
        return 'ai'
    }
    if (root === 'trading') {
        return 'trading'
    }
    if (root === 'site' || root === 'report' || root === 'network') {
        return 'brand'
    }
    return 'other'
}

function collectOverrideItems(baselineValue, currentValue, path = '', collected = []) {
    if (!path && (isPlainObject(baselineValue) || isPlainObject(currentValue))) {
        const keys = new Set([
            ...Object.keys(baselineValue || {}),
            ...Object.keys(currentValue || {})
        ])
        keys.forEach((key) => {
            collectOverrideItems(baselineValue?.[key], currentValue?.[key], key, collected)
        })
        return collected
    }

    if (shouldIgnorePath(path)) {
        return collected
    }

    if (isPlainObject(baselineValue) || isPlainObject(currentValue)) {
        const keys = new Set([
            ...Object.keys(baselineValue || {}),
            ...Object.keys(currentValue || {})
        ])
        keys.forEach((key) => {
            const nextPath = path ? `${path}.${key}` : key
            collectOverrideItems(baselineValue?.[key], currentValue?.[key], nextPath, collected)
        })
        return collected
    }

    if (!areValuesEqual(baselineValue, currentValue)) {
        collected.push({
            path,
            sectionKey: resolveSectionKey(path),
            before: baselineValue,
            after: currentValue
        })
    }

    return collected
}

function buildReviewSections(baselineConfig, currentConfig, t) {
    const items = collectOverrideItems(baselineConfig, currentConfig)
        .map((item) => ({
            ...item,
            beforeDisplay: formatPathValue(item.path, item.before, item.before, t),
            afterDisplay: formatPathValue(item.path, item.after, item.before, t),
            previewValue: buildPreviewValue(item.path, item.after, item.before, t)
        }))

    return SECTION_ORDER
        .map((sectionKey) => {
            const sectionItems = items.filter((item) => item.sectionKey === sectionKey)
            return {
                key: sectionKey,
                title: sectionTitle(sectionKey, t),
                items: sectionItems
            }
        })
        .filter((section) => section.items.length > 0)
}

function setDeepValue(target, path, value) {
    const segments = path.split('.')
    let cursor = target
    for (let index = 0; index < segments.length - 1; index += 1) {
        const segment = segments[index]
        cursor[segment] = cursor[segment] ?? {}
        cursor = cursor[segment]
    }
    cursor[segments[segments.length - 1]] = value
}

function buildOverridePreview(reviewSections) {
    const preview = {}
    reviewSections.forEach((section) => {
        section.items.forEach((item) => {
            setDeepValue(preview, item.path, item.previewValue)
        })
    })
    return preview
}

function deriveLoginEnabled(config) {
    return config?.deployment_mode === 'public'
}

function deriveAuthProvider(config) {
    if (!deriveLoginEnabled(config)) {
        return 'none'
    }
    return config?.auth?.auth_provider || 'system'
}

export default function ReviewSummary({ initialConfig, config, t }) {
    const reviewSections = useMemo(() => buildReviewSections(initialConfig, config, t), [config, initialConfig, t])
    const changedItemCount = useMemo(() => reviewSections.reduce((total, section) => total + section.items.length, 0), [reviewSections])
    const overridePreview = useMemo(() => buildOverridePreview(reviewSections), [reviewSections])
    const enabledProviders = config?.ai?.provider_priority || []
    const requiresLogin = deriveLoginEnabled(config)
    const authProvider = deriveAuthProvider(config)

    return (
        <Card className="onboarding-card">
            <Alert
                type="info"
                showIcon
                message={t('onboarding.review_title', 'Review before saving')}
                description={t('onboarding.review_desc', 'This page summarizes the effective overrides that will be saved so you can confirm what actually changed before applying them.')}
            />
            <Divider />
            <Row gutter={[16, 16]} className="onboarding-review-stats">
                <Col xs={24} md={12}>
                    <Card size="small" className="onboarding-nested-card onboarding-review-stat-card">
                        <Text type="secondary">{t('onboarding.review.metrics.override_groups', 'Override groups')}</Text>
                        <Title level={3} style={{ margin: 0 }}>{reviewSections.length}</Title>
                    </Card>
                </Col>
                <Col xs={24} md={12}>
                    <Card size="small" className="onboarding-nested-card onboarding-review-stat-card">
                        <Text type="secondary">{t('onboarding.review.metrics.override_items', 'Override items')}</Text>
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
                    <Card
                        size="small"
                        className="onboarding-nested-card"
                        title={t('onboarding.review.override_preview_title', 'Effective override preview')}
                    >
                        <Text type="secondary">
                            {t('onboarding.review.override_preview_desc', 'Only values that differ from the currently saved bootstrap configuration are shown here.')}
                        </Text>
                        <pre style={{
                            margin: '12px 0 0',
                            padding: 16,
                            borderRadius: 12,
                            background: 'rgba(15, 23, 42, 0.04)',
                            overflowX: 'auto',
                            whiteSpace: 'pre-wrap',
                            wordBreak: 'break-word'
                        }}
                        >
                            {JSON.stringify(overridePreview, null, 2)}
                        </pre>
                    </Card>
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
                                    <div key={item.path} className="onboarding-review-item">
                                        <Space direction="vertical" size={4} style={{ width: '100%' }}>
                                            <Text code>{item.path}</Text>
                                            <Text strong>{item.afterDisplay}</Text>
                                            <Text type="secondary">
                                                {t('onboarding.review.previous_value', 'Previous')}: {item.beforeDisplay}
                                            </Text>
                                        </Space>
                                    </div>
                                ))}
                            </div>
                        </Card>
                    ))}
                </Space>
            )}
            <Space wrap>
                <Tag color={requiresLogin ? 'processing' : 'default'}>
                    {requiresLogin
                        ? t('onboarding.review.badges.login_enabled', 'Login: {{provider}}', { provider: authProvider })
                        : t('onboarding.review.badges.login_disabled', 'Login disabled')}
                </Tag>
                <Tag color={config.ai.enabled ? 'success' : 'default'}>
                    {config.ai.enabled
                        ? t('onboarding.review.badges.ai_enabled', 'AI: {{providers}}', { providers: enabledProviders.join(' > ') })
                        : t('onboarding.review.badges.ai_skipped', 'AI skipped')}
                </Tag>
                <Tag color={config.trading.live_trading_enabled ? 'warning' : 'default'}>
                    {config.trading.live_trading_enabled
                        ? t('onboarding.review.badges.live_enabled', 'Binance live enabled')
                        : t('onboarding.review.badges.live_skipped', 'Binance live skipped')}
                </Tag>
                <Tag color={config.report.enable_public_share ? 'processing' : 'default'}>
                    {config.report.enable_public_share
                        ? t('onboarding.review.badges.reports_enabled', 'Public reports enabled')
                        : t('onboarding.review.badges.reports_skipped', 'Public reports skipped')}
                </Tag>
            </Space>
        </Card>
    )
}
