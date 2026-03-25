import { useEffect, useState } from 'react';
import { Alert, Card, Input, List, Space, Switch, Typography } from 'antd';
import { DndContext, closestCenter, KeyboardSensor, PointerSensor, useSensor, useSensors } from '@dnd-kit/core';
import { arrayMove, SortableContext, sortableKeyboardCoordinates, useSortable, verticalListSortingStrategy } from '@dnd-kit/sortable';
import { CSS } from '@dnd-kit/utilities';
import { HolderOutlined } from '@ant-design/icons';
import { useTranslation } from 'react-i18next';
import { AI_PROVIDERS } from '../../constants/settingsConstants';
import CredentialActions from './CredentialActions';
import CredentialSourceTag from './CredentialSourceTag';

const { Text } = Typography;

function SortableProviderItem({ id, disabled }) {
    const provider = AI_PROVIDERS.find(item => item.key === id);
    const {
        attributes,
        listeners,
        setNodeRef,
        transform,
        transition,
        isDragging,
    } = useSortable({ id, disabled });

    const style = {
        transform: CSS.Transform.toString(transform),
        transition,
        opacity: isDragging ? 0.5 : 1,
        cursor: disabled ? 'not-allowed' : 'grab',
    };

    return (
        <div ref={setNodeRef} style={style} {...attributes} {...listeners}>
            <List.Item>
                <List.Item.Meta
                    avatar={<HolderOutlined />}
                    title={provider?.label || id}
                />
            </List.Item>
        </div>
    );
}

export function AIModelSettingsSection({
    credentials,
    sources,
    loading,
    testing,
    onCredentialChange,
    onSave,
    onTest,
    onReset
}) {
    const { t } = useTranslation();
    const providerConfigs = credentials.ai_provider_configs || {};
    const providerSources = sources.ai_provider_configs || {};
    const [priority, setPriority] = useState(credentials.ai_provider_priority || []);

    const sensors = useSensors(
        useSensor(PointerSensor),
        useSensor(KeyboardSensor, {
            coordinateGetter: sortableKeyboardCoordinates,
        })
    );

    useEffect(() => {
        setPriority(credentials.ai_provider_priority || []);
    }, [credentials.ai_provider_priority]);

    const syncPriority = (newPriority) => {
        setPriority(newPriority);
        onCredentialChange('ai_provider_priority', newPriority);
        onCredentialChange('ai_provider', newPriority[0] || '');
    };

    const updateProviderConfig = (provider, field, value) => {
        onCredentialChange('ai_provider_configs', {
            ...providerConfigs,
            [provider]: {
                ...(providerConfigs[provider] || {}),
                [field]: value
            }
        });
    };

    const handleToggleProvider = (provider, enabled) => {
        if (enabled) {
            if (!priority.includes(provider)) {
                syncPriority([...priority, provider]);
            }
            return;
        }
        syncPriority(priority.filter(item => item !== provider));
    };

    const handleDragEnd = (event) => {
        const { active, over } = event;
        if (!over || active.id === over.id) {
            return;
        }
        const oldIndex = priority.indexOf(active.id);
        const newIndex = priority.indexOf(over.id);
        syncPriority(arrayMove(priority, oldIndex, newIndex));
    };

    return (
        <Card title={t('settings.ai_model_credentials', 'AI Model')} bordered={false}>
            <p style={{ color: '#888', marginBottom: '1.5rem' }}>
                {t('settings.credentials_note', 'Configure API credentials. Values saved here take precedence over .env file.')}
            </p>
            <Space direction="vertical" style={{ width: '100%' }} size="large">
                <Card size="small" title={t('settings.ai_provider_priority', 'AI Provider Priority')}>
                    <Alert
                        type="info"
                        showIcon
                        message={t('settings.ai_provider_priority_help', 'Enable one or more providers and drag to reorder fallback priority. The backend will try them in order.')}
                        style={{ marginBottom: 16 }}
                    />
                    <Space direction="vertical" style={{ width: '100%' }}>
                        {AI_PROVIDERS.map(({ key, label }) => (
                            <div key={key} style={{ display: 'flex', alignItems: 'center', gap: 8 }}>
                                <Switch
                                    checked={priority.includes(key)}
                                    onChange={(checked) => handleToggleProvider(key, checked)}
                                    disabled={loading}
                                />
                                <span>{label}</span>
                            </div>
                        ))}
                    </Space>
                    <div style={{ marginTop: 16 }}>
                        <CredentialSourceTag source={sources.ai_provider_priority || 'default'} />
                    </div>
                    <div style={{ marginTop: 16 }}>
                        <DndContext
                            sensors={sensors}
                            collisionDetection={closestCenter}
                            onDragEnd={handleDragEnd}
                        >
                            <SortableContext items={priority} strategy={verticalListSortingStrategy}>
                                <List
                                    bordered
                                    dataSource={priority}
                                    renderItem={(id) => <SortableProviderItem key={id} id={id} disabled={loading} />}
                                />
                            </SortableContext>
                        </DndContext>
                    </div>
                    <div style={{ marginTop: 16 }}>
                        <CredentialActions
                            onSave={() => onSave('ai_model_priority')}
                            onReset={() => onReset('ai_provider_priority')}
                            loading={loading}
                            testing={false}
                        />
                    </div>
                </Card>

                {AI_PROVIDERS.map(({ key, label }) => {
                    const providerConfig = providerConfigs[key] || {};
                    const providerSource = providerSources[key] || 'none';
                    const actionKey = `ai_model-${key}`;
                    return (
                        <Card key={key} size="small" title={label}>
                            <Space direction="vertical" style={{ width: '100%' }} size="middle">
                                <div>
                                    <label>
                                        {t('settings.api_key', 'API Key')}
                                        <CredentialSourceTag source={providerSource} />
                                    </label>
                                    <Input.Password
                                        value={providerConfig.api_key}
                                        onChange={(e) => updateProviderConfig(key, 'api_key', e.target.value)}
                                        placeholder={key === 'openai' ? 'sk-...' : ''}
                                        disabled={loading}
                                    />
                                </div>
                                <div>
                                    <label>{t('settings.base_url', 'Base URL')}</label>
                                    <Input
                                        value={providerConfig.base_url}
                                        onChange={(e) => updateProviderConfig(key, 'base_url', e.target.value)}
                                        disabled={loading}
                                    />
                                </div>
                                <div>
                                    <label>{t('settings.default_runtime_model', 'Default Runtime Model')}</label>
                                    <Input
                                        value={providerConfig.default_model}
                                        onChange={(e) => updateProviderConfig(key, 'default_model', e.target.value)}
                                        placeholder={t('settings.default_runtime_model_placeholder', 'Optional fallback model name')}
                                        disabled={loading}
                                    />
                                </div>
                                <Text type="secondary">
                                    {t('settings.provider_note', 'Each provider is stored independently. The backend will use provider priority and fallback automatically.')}
                                </Text>
                                <CredentialActions
                                    onSave={() => onSave(actionKey)}
                                    onTest={() => onTest(actionKey)}
                                    onReset={() => onReset(`ai_provider:${key}:api_key`)}
                                    loading={loading}
                                    testing={testing === actionKey}
                                />
                            </Space>
                        </Card>
                    );
                })}
            </Space>
        </Card>
    );
}

export default AIModelSettingsSection;
