import { useCallback, useEffect, useState } from 'react'
import { Navigate } from 'react-router-dom'
import { Alert, Spin, message } from 'antd'
import { useTranslation } from 'react-i18next'
import { SystemUsersSection } from '../components/Settings'
import { useAuth } from '../hooks/useAuth'
import { authApi } from '../services/authApi'
import './UserManagement.css'

function UserManagement() {
    const { t } = useTranslation()
    const { authProvider, loginEnabled, user, isLoading: authLoading } = useAuth()
    const [users, setUsers] = useState([])
    const [loading, setLoading] = useState(false)

    const supportsUserManagement = loginEnabled && authProvider !== 'logto'
    const isSystemAdmin = supportsUserManagement && Boolean(user?.is_superuser)

    const loadUsers = useCallback(async () => {
        if (!isSystemAdmin) {
            setUsers([])
            return
        }

        try {
            setLoading(true)
            const response = await authApi.getSystemUsers()
            setUsers(response.users || [])
        } catch (error) {
            message.error(error.message || t('settings.system_users.load_failed', 'Failed to load system users'))
        } finally {
            setLoading(false)
        }
    }, [isSystemAdmin, t])

    useEffect(() => {
        if (isSystemAdmin) {
            loadUsers()
        }
    }, [isSystemAdmin, loadUsers])

    if (authLoading) {
        return (
            <div className="user-management-loading">
                <Spin size="large" />
            </div>
        )
    }

    if (!isSystemAdmin) {
        return <Navigate to="/settings" replace />
    }

    return (
        <div className="user-management-page">
            <div className="user-management-header">
                <h1>{t('settings.system_users.title', 'System Users')}</h1>
                <p>{t('settings.system_users.page_desc', 'Administrators can create, disable, and maintain built-in email/password accounts here.')}</p>
            </div>

            <Alert
                className="user-management-alert"
                type="info"
                showIcon
                message={t('settings.system_users.page_notice_title', 'Administrator access only')}
                description={t('settings.system_users.page_notice_desc', 'This page is only available when built-in system authentication is enabled and the current account has administrator privileges.')}
            />

            <SystemUsersSection
                currentUserId={user?.id ?? null}
                loading={loading}
                users={users}
                onReload={loadUsers}
            />
        </div>
    )
}

export default UserManagement
