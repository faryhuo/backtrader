import {
    Alert,
    Button,
    Card,
    Input,
    Space,
    Switch,
    Tag,
    Typography
} from 'antd'
import { ArrowDownOutlined, ArrowUpOutlined } from '@ant-design/icons'

import { AI_PROVIDERS } from '../../constants/settingsConstants'
import SettingRow from './SettingRow'

const { Text } = Typography

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

export default function AISetupSection({
    config,
    enabledProviders,
    updateConfig,
    toggleProvider,
    reorderProvider,
    testConnection,
    testing,
    t
}) {
    return (
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
                message={t('onboarding.ai_note', 'The wizard stores provider credentials, fallback priority, and the runtime model name used by each enabled provider.')}
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
                                    <SettingRow label={t('onboarding.fields.default_model', 'Default runtime model')}>
                                        <Input
                                            value={providerConfig.default_model}
                                            onChange={(event) => updateConfig(['ai', 'providers', provider.key, 'default_model'], event.target.value)}
                                        />
                                    </SettingRow>
                                    <Button
                                        onClick={() => testConnection('ai_model', {
                                            provider: provider.key,
                                            api_key: providerConfig.api_key,
                                            base_url: providerConfig.base_url,
                                            model: providerConfig.default_model
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
}
