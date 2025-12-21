import { useState, useEffect } from 'react';
import { useTranslation } from 'react-i18next';
import { Form, Input, Button, Card, Alert, Space, message, List, Switch, Tooltip } from 'antd';
import { SaveOutlined, UndoOutlined, HolderOutlined, DatabaseOutlined, CloudOutlined, InfoCircleOutlined } from '@ant-design/icons';
import { DndContext, closestCenter, KeyboardSensor, PointerSensor, useSensor, useSensors } from '@dnd-kit/core';
import { arrayMove, SortableContext, sortableKeyboardCoordinates, useSortable, verticalListSortingStrategy } from '@dnd-kit/sortable';
import { CSS } from '@dnd-kit/utilities';
import { CredentialSourceTag } from './CredentialSourceTag';

const DATA_SOURCES = [
    { id: 'yahoo', name: 'Yahoo Finance', icon: <CloudOutlined />, description: 'Free, supports major global markets' },
    { id: 'eodhd', name: 'EODHD', icon: <CloudOutlined />, description: 'Premium data source, requires API key' },
    { id: 'database', name: 'Local Database', icon: <DatabaseOutlined />, description: 'Cached data from previous fetches' },
];

function SortableItem({ id, disabled }) {
    const { t } = useTranslation();
    const source = DATA_SOURCES.find(s => s.id === id);

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
            <List.Item className={`datasource-priority-item ${disabled ? 'disabled' : ''}`}>
                <List.Item.Meta
                    avatar={<HolderOutlined className="drag-handle" />}
                    title={
                        <Space>
                            {source?.icon}
                            <span>{t(`settings.datasource.sources.${id}`, source?.name)}</span>
                        </Space>
                    }
                    description={t(`settings.datasource.sources.${id}_desc`, source?.description)}
                />
            </List.Item>
        </div>
    );
}

function DataSourceSettingsSection({
    settings = {},
    loading,
    saved,
    onChange,
    onSave,
    onReset
}) {
    const { t } = useTranslation();
    const [form] = Form.useForm();
    const [priority, setPriority] = useState(['yahoo', 'database']);

    const sensors = useSensors(
        useSensor(PointerSensor),
        useSensor(KeyboardSensor, {
            coordinateGetter: sortableKeyboardCoordinates,
        })
    );

    useEffect(() => {
        if (settings.data_source_priority) {
            setPriority(settings.data_source_priority);
        }
    }, [settings.data_source_priority]);

    const handleDragEnd = (event) => {
        const { active, over } = event;

        if (active.id !== over?.id) {
            setPriority((items) => {
                const oldIndex = items.indexOf(active.id);
                const newIndex = items.indexOf(over.id);
                const newPriority = arrayMove(items, oldIndex, newIndex);
                onChange?.({ data_source_priority: newPriority });
                return newPriority;
            });
        }
    };

    const handleToggleSource = (sourceId, enabled) => {
        let newPriority;
        if (enabled) {
            // Add source to the end
            newPriority = [...priority, sourceId];
        } else {
            // Remove source (but keep at least 1)
            if (priority.length <= 1) {
                message.warning(t('settings.datasource.min_source_warning', 'At least one data source is required'));
                return;
            }
            newPriority = priority.filter(id => id !== sourceId);
        }
        setPriority(newPriority);
        onChange?.({ data_source_priority: newPriority });
    };

    const handleApiKeyChange = (e) => {
        onChange?.({ eodhd_api_key: e.target.value });
    };

    const handleSave = () => {
        onSave?.({
            data_source_priority: priority,
            eodhd_api_key: form.getFieldValue('eodhd_api_key')
        });
    };

    const isSourceEnabled = (sourceId) => priority.includes(sourceId);

    return (
        <div className="settings-section datasource-settings">
            <Card
                title={t('settings.datasource.title', 'Data Source Priority')}
                className="settings-card"
                extra={saved && <Alert type="success" message={t('settings.saved')} showIcon banner />}
            >
                <Form form={form} layout="vertical" initialValues={settings}>
                    {/* Priority Description */}
                    <Alert
                        type="info"
                        showIcon
                        icon={<InfoCircleOutlined />}
                        message={t('settings.datasource.priority_help', 'Drag to reorder. Data will be fetched from sources in order until successful.')}
                        style={{ marginBottom: 16 }}
                    />

                    {/* Source Toggle & Priority List */}
                    <Form.Item label={t('settings.datasource.enabled_sources', 'Enabled Sources')}>
                        <Space direction="vertical" style={{ width: '100%' }}>
                            {DATA_SOURCES.map((source) => (
                                <div key={source.id} className="source-toggle-row">
                                    <Switch
                                        checked={isSourceEnabled(source.id)}
                                        onChange={(checked) => handleToggleSource(source.id, checked)}
                                        disabled={loading}
                                    />
                                    <Space style={{ marginLeft: 8 }}>
                                        {source.icon}
                                        <span>{t(`settings.datasource.sources.${source.id}`, source.name)}</span>
                                        {source.id === 'eodhd' && !isSourceEnabled('eodhd') && (
                                            <Tooltip title={t('settings.datasource.eodhd_requires_key', 'Requires API key')}>
                                                <InfoCircleOutlined style={{ color: '#faad14' }} />
                                            </Tooltip>
                                        )}
                                    </Space>
                                </div>
                            ))}
                        </Space>
                    </Form.Item>

                    {/* Priority Order */}
                    <Form.Item label={t('settings.datasource.priority_order', 'Priority Order')}>
                        <DndContext
                            sensors={sensors}
                            collisionDetection={closestCenter}
                            onDragEnd={handleDragEnd}
                        >
                            <SortableContext items={priority} strategy={verticalListSortingStrategy}>
                                <List
                                    bordered
                                    className="priority-list"
                                    dataSource={priority}
                                    renderItem={(id) => (
                                        <SortableItem key={id} id={id} disabled={loading} />
                                    )}
                                />
                            </SortableContext>
                        </DndContext>
                    </Form.Item>

                    {/* EODHD API Key */}
                    {isSourceEnabled('eodhd') && (
                        <Form.Item
                            name="eodhd_api_key"
                            label={
                                <Space>
                                    {t('settings.datasource.eodhd_api_key', 'EODHD API Key')}
                                    {settings.eodhd_api_key_source && (
                                        <CredentialSourceTag source={settings.eodhd_api_key_source} />
                                    )}
                                </Space>
                            }
                        >
                            <Input.Password
                                placeholder={settings.eodhd_api_key || t('settings.datasource.enter_api_key', 'Enter EODHD API Key')}
                                onChange={handleApiKeyChange}
                                disabled={loading}
                            />
                        </Form.Item>
                    )}

                    {/* Actions */}
                    <Form.Item>
                        <Space>
                            <Button
                                type="primary"
                                icon={<SaveOutlined />}
                                onClick={handleSave}
                                loading={loading}
                            >
                                {t('settings.save', 'Save')}
                            </Button>
                            <Button
                                icon={<UndoOutlined />}
                                onClick={onReset}
                                disabled={loading}
                            >
                                {t('settings.reset', 'Reset')}
                            </Button>
                        </Space>
                    </Form.Item>
                </Form>
            </Card>
        </div>
    );
}

export default DataSourceSettingsSection;
