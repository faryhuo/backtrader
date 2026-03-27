import {
    Alert,
    Card,
    Input,
    List,
    Space,
    Switch,
    Tooltip,
    Typography,
    message
} from 'antd'
import {
    CloudOutlined,
    DatabaseOutlined,
    HolderOutlined,
    InfoCircleOutlined
} from '@ant-design/icons'
import {
    DndContext,
    KeyboardSensor,
    PointerSensor,
    closestCenter,
    useSensor,
    useSensors
} from '@dnd-kit/core'
import {
    SortableContext,
    arrayMove,
    sortableKeyboardCoordinates,
    useSortable,
    verticalListSortingStrategy
} from '@dnd-kit/sortable'
import { CSS } from '@dnd-kit/utilities'

import SettingRow from './SettingRow'

const { Text } = Typography

const DATA_SOURCE_OPTIONS = [
    { id: 'yahoo', icon: <CloudOutlined /> },
    { id: 'eodhd', icon: <CloudOutlined /> },
    { id: 'database', icon: <DatabaseOutlined /> }
]

function SortableSourceItem({ sourceId, t }) {
    const source = DATA_SOURCE_OPTIONS.find((item) => item.id === sourceId)
    const {
        attributes,
        listeners,
        setNodeRef,
        transform,
        transition,
        isDragging
    } = useSortable({ id: sourceId })

    const style = {
        transform: CSS.Transform.toString(transform),
        transition,
        opacity: isDragging ? 0.6 : 1
    }

    return (
        <div ref={setNodeRef} style={style} {...attributes} {...listeners}>
            <List.Item className={`onboarding-datasource-item${isDragging ? ' is-dragging' : ''}`}>
                <List.Item.Meta
                    avatar={<HolderOutlined className="onboarding-datasource-drag-handle" />}
                    title={(
                        <Space size={8}>
                            {source?.icon}
                            <span>{t(`onboarding.datasource.sources.${sourceId}`, sourceId)}</span>
                        </Space>
                    )}
                    description={t(`onboarding.datasource.sources.${sourceId}_desc`, '')}
                />
            </List.Item>
        </div>
    )
}

export default function DataSourceSetupSection({ config, updateConfig, t }) {
    const priority = config.data_source?.priority || []
    const sensors = useSensors(
        useSensor(PointerSensor),
        useSensor(KeyboardSensor, {
            coordinateGetter: sortableKeyboardCoordinates
        })
    )

    const isSourceEnabled = (sourceId) => priority.includes(sourceId)

    const handleToggleSource = (sourceId, enabled) => {
        if (enabled) {
            if (!priority.includes(sourceId)) {
                updateConfig(['data_source', 'priority'], [...priority, sourceId])
            }
            return
        }

        if (priority.length <= 1) {
            message.warning(t('onboarding.datasource.min_source_warning', 'At least one data source is required.'))
            return
        }

        updateConfig(['data_source', 'priority'], priority.filter((item) => item !== sourceId))
    }

    const handleDragEnd = (event) => {
        const { active, over } = event
        if (!over || active.id === over.id) {
            return
        }

        const oldIndex = priority.indexOf(active.id)
        const newIndex = priority.indexOf(over.id)
        if (oldIndex < 0 || newIndex < 0) {
            return
        }

        updateConfig(['data_source', 'priority'], arrayMove(priority, oldIndex, newIndex))
    }

    return (
        <Card
            className="onboarding-card"
            title={t('onboarding.datasource.title', 'Data Source Priority')}
        >
            <Alert
                type="info"
                showIcon
                icon={<InfoCircleOutlined />}
                message={t('onboarding.datasource.priority_help', 'Drag to reorder. Data will be fetched from sources in order until successful.')}
                style={{ marginBottom: 20 }}
            />

            <Card
                size="small"
                className="onboarding-nested-card"
                title={t('onboarding.datasource.enabled_sources', 'Enabled Sources')}
            >
                <Space direction="vertical" size="middle" style={{ width: '100%' }}>
                    {DATA_SOURCE_OPTIONS.map((source) => (
                        <div key={source.id} className="onboarding-source-toggle-row">
                            <Switch
                                checked={isSourceEnabled(source.id)}
                                onChange={(checked) => handleToggleSource(source.id, checked)}
                            />
                            <Space size={8}>
                                {source.icon}
                                <Text>{t(`onboarding.datasource.sources.${source.id}`, source.id)}</Text>
                                {source.id === 'eodhd' ? (
                                    <Tooltip title={t('onboarding.datasource.eodhd_requires_key', 'Requires API key')}>
                                        <InfoCircleOutlined style={{ color: '#faad14' }} />
                                    </Tooltip>
                                ) : null}
                            </Space>
                        </div>
                    ))}
                </Space>
            </Card>

            <Card
                size="small"
                className="onboarding-nested-card"
                title={t('onboarding.datasource.priority_order', 'Priority Order')}
            >
                <DndContext
                    sensors={sensors}
                    collisionDetection={closestCenter}
                    onDragEnd={handleDragEnd}
                >
                    <SortableContext items={priority} strategy={verticalListSortingStrategy}>
                        <List
                            bordered
                            className="onboarding-datasource-list"
                            dataSource={priority}
                            locale={{
                                emptyText: t('onboarding.datasource.empty_priority', 'Enable at least one source to define priority.')
                            }}
                            renderItem={(sourceId) => (
                                <SortableSourceItem key={sourceId} sourceId={sourceId} t={t} />
                            )}
                        />
                    </SortableContext>
                </DndContext>
            </Card>

            {isSourceEnabled('eodhd') ? (
                <Card
                    size="small"
                    className="onboarding-nested-card"
                    title={t('onboarding.datasource.eodhd_api_key', 'EODHD API Key')}
                >
                    <SettingRow
                        label="EODHD_API_KEY"
                        hint={t('onboarding.datasource.eodhd_requires_key', 'Requires API key')}
                    >
                        <Input.Password
                            value={config.data_source?.eodhd_api_key || ''}
                            placeholder={t('onboarding.datasource.enter_api_key', 'Enter EODHD API Key')}
                            onChange={(event) => updateConfig(['data_source', 'eodhd_api_key'], event.target.value)}
                        />
                    </SettingRow>
                </Card>
            ) : null}
        </Card>
    )
}
