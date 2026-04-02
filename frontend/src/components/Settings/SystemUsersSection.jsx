import { useCallback, useMemo, useState } from 'react'
import {
    Alert,
    Button,
    Card,
    Form,
    Input,
    Modal,
    Space,
    Switch,
    Table,
    Tag,
    Typography,
    message
} from 'antd'
import PropTypes from 'prop-types'
import { useTranslation } from 'react-i18next'
import { authApi } from '../../services/authApi'

const { Paragraph, Text } = Typography

export function SystemUsersSection({ loading, users, onReload, currentUserId }) {
    const { t } = useTranslation()
    const [form] = Form.useForm()
    const [passwordForm] = Form.useForm()
    const [submitting, setSubmitting] = useState(false)
    const [passwordSubmitting, setPasswordSubmitting] = useState(false)
    const [passwordModalState, setPasswordModalState] = useState({
        open: false,
        user: null,
    })

    const handleToggleActive = useCallback(async (record, isActive) => {
        try {
            await authApi.setSystemUserActive(record.id, isActive)
            message.success(
                isActive
                    ? t('settings.system_users.messages.activate_success', 'User activated')
                    : t('settings.system_users.messages.deactivate_success', 'User deactivated')
            )
            await onReload()
        } catch (error) {
            message.error(error.message || t('settings.system_users.messages.update_failed', 'Failed to update user'))
        }
    }, [onReload, t])

    const columns = useMemo(() => ([
        {
            title: t('settings.system_users.columns.email', 'Email'),
            dataIndex: 'email',
            key: 'email',
        },
        {
            title: t('settings.system_users.columns.name', 'Name'),
            dataIndex: 'name',
            key: 'name',
            render: (_, record) => record.name || '-',
        },
        {
            title: t('settings.system_users.columns.role', 'Role'),
            dataIndex: 'is_superuser',
            key: 'is_superuser',
            render: (value) => value
                ? <Tag color="processing">{t('settings.system_users.roles.admin', 'Admin')}</Tag>
                : <Tag>{t('settings.system_users.roles.user', 'User')}</Tag>,
        },
        {
            title: t('settings.system_users.columns.status', 'Status'),
            dataIndex: 'is_active',
            key: 'is_active',
            render: (value) => value
                ? <Tag color="success">{t('settings.system_users.status.active', 'Active')}</Tag>
                : <Tag color="default">{t('settings.system_users.status.disabled', 'Disabled')}</Tag>,
        },
        {
            title: t('settings.system_users.columns.actions', 'Actions'),
            key: 'actions',
            render: (_, record) => (
                <Space wrap>
                    <Switch
                        checked={record.is_active}
                        checkedChildren={t('settings.system_users.status.active', 'Active')}
                        unCheckedChildren={t('settings.system_users.status.disabled', 'Disabled')}
                        disabled={loading || record.id === currentUserId}
                        onChange={(checked) => handleToggleActive(record, checked)}
                    />
                    <Button
                        onClick={() => {
                            passwordForm.resetFields()
                            setPasswordModalState({ open: true, user: record })
                        }}
                    >
                        {t('settings.system_users.actions.reset_password', 'Reset Password')}
                    </Button>
                </Space>
            ),
        },
    ]), [currentUserId, handleToggleActive, loading, passwordForm, t])

    const handleCreateUser = async (values) => {
        setSubmitting(true)
        try {
            await authApi.createSystemUser(values)
            message.success(t('settings.system_users.messages.create_success', 'User created'))
            form.resetFields()
            await onReload()
        } catch (error) {
            message.error(error.message || t('settings.system_users.messages.create_failed', 'Failed to create user'))
        } finally {
            setSubmitting(false)
        }
    }

    const handleResetPassword = async (values) => {
        if (!passwordModalState.user) {
            return
        }
        setPasswordSubmitting(true)
        try {
            await authApi.resetSystemUserPassword(passwordModalState.user.id, values.password)
            message.success(t('settings.system_users.messages.password_success', 'Password updated'))
            setPasswordModalState({ open: false, user: null })
            passwordForm.resetFields()
        } catch (error) {
            message.error(error.message || t('settings.system_users.messages.password_failed', 'Failed to update password'))
        } finally {
            setPasswordSubmitting(false)
        }
    }

    return (
        <>
            <Card title={t('settings.system_users.title', 'System Users')} bordered={false}>
                <Space direction="vertical" size="large" style={{ width: '100%' }}>
                    <Alert
                        type="info"
                        showIcon
                        message={t('settings.system_users.info_title', 'Built-in user management')}
                        description={t('settings.system_users.info_desc', 'Create email/password accounts, disable access, and rotate passwords without leaving the Settings page.')}
                    />

                    <div>
                        <Text strong>{t('settings.system_users.create_title', 'Create user')}</Text>
                        <Paragraph type="secondary" style={{ marginBottom: 16 }}>
                            {t('settings.system_users.create_desc', 'The first account should usually stay as an administrator. Use regular users for day-to-day access.')}
                        </Paragraph>
                        <Form
                            form={form}
                            layout="vertical"
                            onFinish={handleCreateUser}
                            disabled={loading || submitting}
                        >
                            <Form.Item
                                label={t('settings.system_users.fields.email', 'Email')}
                                name="email"
                                rules={[
                                    { required: true, message: t('settings.system_users.validation.email_required', 'Email is required') },
                                    { type: 'email', message: t('settings.system_users.validation.email_invalid', 'Enter a valid email address') },
                                ]}
                            >
                                <Input placeholder="user@example.com" autoComplete="email" />
                            </Form.Item>
                            <Form.Item label={t('settings.system_users.fields.display_name', 'Display name')} name="display_name">
                                <Input placeholder={t('settings.system_users.fields.display_name_placeholder', 'Optional name')} />
                            </Form.Item>
                            <Form.Item
                                label={t('settings.system_users.fields.password', 'Password')}
                                name="password"
                                rules={[
                                    { required: true, message: t('settings.system_users.validation.password_required', 'Password is required') },
                                    { min: 8, message: t('settings.system_users.validation.password_min', 'Password must be at least 8 characters') },
                                ]}
                            >
                                <Input.Password
                                    placeholder={t('settings.system_users.fields.password_placeholder', 'At least 8 characters')}
                                    autoComplete="new-password"
                                />
                            </Form.Item>
                            <Form.Item label={t('settings.system_users.fields.is_superuser', 'Administrator')} name="is_superuser" valuePropName="checked">
                                <Switch />
                            </Form.Item>
                            <Button type="primary" htmlType="submit" loading={submitting}>
                                {t('settings.system_users.actions.create', 'Create User')}
                            </Button>
                        </Form>
                    </div>

                    <Table
                        rowKey="id"
                        columns={columns}
                        dataSource={users}
                        loading={loading}
                        pagination={false}
                    />
                </Space>
            </Card>

            <Modal
                title={passwordModalState.user
                    ? t('settings.system_users.reset_modal_title_with_email', 'Reset Password: {{email}}', { email: passwordModalState.user.email })
                    : t('settings.system_users.actions.reset_password', 'Reset Password')}
                open={passwordModalState.open}
                onCancel={() => {
                    if (!passwordSubmitting) {
                        setPasswordModalState({ open: false, user: null })
                        passwordForm.resetFields()
                    }
                }}
                onOk={() => passwordForm.submit()}
                okText={t('settings.system_users.actions.update_password', 'Update Password')}
                confirmLoading={passwordSubmitting}
            >
                <Form
                    form={passwordForm}
                    layout="vertical"
                    onFinish={handleResetPassword}
                >
                    <Form.Item
                        label={t('settings.system_users.fields.new_password', 'New password')}
                        name="password"
                        rules={[
                            { required: true, message: t('settings.system_users.validation.password_required', 'Password is required') },
                            { min: 8, message: t('settings.system_users.validation.password_min', 'Password must be at least 8 characters') },
                        ]}
                    >
                        <Input.Password autoComplete="new-password" />
                    </Form.Item>
                </Form>
            </Modal>
        </>
    )
}

SystemUsersSection.propTypes = {
    currentUserId: PropTypes.number,
    loading: PropTypes.bool,
    onReload: PropTypes.func.isRequired,
    users: PropTypes.arrayOf(PropTypes.shape({
        email: PropTypes.string,
        id: PropTypes.number,
        is_active: PropTypes.bool,
        is_superuser: PropTypes.bool,
        name: PropTypes.string,
    })),
}

SystemUsersSection.defaultProps = {
    currentUserId: null,
    loading: false,
    users: [],
}

export default SystemUsersSection
