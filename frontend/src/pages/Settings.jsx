import { useState, useEffect, useCallback } from 'react';
import { useTranslation } from 'react-i18next';
import { SettingOutlined, ApiOutlined, SafetyOutlined, CloudOutlined, DollarOutlined, GlobalOutlined, DatabaseOutlined } from '@ant-design/icons';
import { Layout, Menu, message } from 'antd';
import { useSettings } from '../hooks/useSettings';
import { useCredentials } from '../hooks/useCredentials';
import { useSiteConfig } from '../hooks/useSiteConfig';
import { useAuth } from '../hooks/useAuth';
import { api } from '../services/api';
import {
    AISettingsSection,
    AIModelSettingsSection,
    AuthSettingsSection,
    ProxySettingsSection,
    ExchangeSettingsSection,
    SiteSettingsSection,
    DataSourceSettingsSection,
    SystemUsersSection
} from '../components/Settings';
import './Settings.css';

const { Sider, Content } = Layout;

function Settings() {
    const { t } = useTranslation();
    const [activeSection, setActiveSection] = useState('ai');
    const [systemUsers, setSystemUsers] = useState([]);
    const [systemUsersLoading, setSystemUsersLoading] = useState(false);
    const { authProvider, user } = useAuth();
    const showSystemUsers = authProvider === 'system' && Boolean(user?.is_superuser);

    // Use custom hooks for state management
    const {
        settings,
        loading: settingsLoading,
        saved,
        loadSettings,
        handleChange,
        handleSave,
        handleReset
    } = useSettings();

    const {
        credentials,
        credentialSources,
        testingCredential,
        loading: credentialsLoading,
        loadCredentials,
        handleCredentialChange,
        handleCCXTCredentialChange,
        handleSaveCredentials,
        handleTestCredential,
        handleResetCredential
    } = useCredentials();

    const {
        config: siteConfig,
        sources: siteConfigSources,
        loading: siteConfigLoading,
        saved: siteConfigSaved,
        loadConfig: loadSiteConfig,
        handleChange: handleSiteConfigChange,
        handleSave: handleSaveSiteConfig,
        handleReset: handleResetSiteConfig
    } = useSiteConfig();

    // Data source settings state
    const [dataSourceSettings, setDataSourceSettings] = useState({
        data_source_priority: ['yahoo', 'database'],
        eodhd_api_key: null,
        eodhd_api_key_source: 'none'
    });
    const [dataSourceLoading, setDataSourceLoading] = useState(false);
    const [dataSourceSaved, setDataSourceSaved] = useState(false);

    const loadDataSourceSettings = useCallback(async () => {
        try {
            setDataSourceLoading(true);
            const response = await api.getDataSourceSettings();
            if (response.settings) {
                setDataSourceSettings(response.settings);
            }
        } catch (err) {
            console.error('Failed to load data source settings:', err);
        } finally {
            setDataSourceLoading(false);
        }
    }, []);

    const handleDataSourceChange = useCallback((changes) => {
        setDataSourceSettings(prev => ({ ...prev, ...changes }));
        setDataSourceSaved(false);
    }, []);

    const handleDataSourceSave = useCallback(async (data) => {
        try {
            setDataSourceLoading(true);
            await api.updateDataSourceSettings(data);
            message.success(t('settings.saved'));
            setDataSourceSaved(true);
            await loadDataSourceSettings();
        } catch (err) {
            message.error(t('settings.save_error'));
            console.error('Failed to save data source settings:', err);
        } finally {
            setDataSourceLoading(false);
        }
    }, [t, loadDataSourceSettings]);

    const handleDataSourceReset = useCallback(async () => {
        try {
            setDataSourceLoading(true);
            await api.resetDataSourceSettings();
            message.success(t('settings.reset_success'));
            await loadDataSourceSettings();
        } catch (err) {
            message.error(t('settings.reset_error'));
            console.error('Failed to reset data source settings:', err);
        } finally {
            setDataSourceLoading(false);
        }
    }, [t, loadDataSourceSettings]);

    const loadSystemUsers = useCallback(async () => {
        if (!showSystemUsers) {
            setSystemUsers([]);
            return;
        }

        try {
            setSystemUsersLoading(true);
            const response = await api.getSystemUsers();
            setSystemUsers(response.users || []);
        } catch (err) {
            message.error(err.message || t('settings.system_users.load_failed', 'Failed to load system users'));
            console.error('Failed to load system users:', err);
        } finally {
            setSystemUsersLoading(false);
        }
    }, [showSystemUsers, t]);

    // Load data on mount
    useEffect(() => {
        loadSettings();
        loadCredentials();
        loadSiteConfig();
        loadDataSourceSettings();
    }, [loadSettings, loadCredentials, loadSiteConfig, loadDataSourceSettings]);

    useEffect(() => {
        if (showSystemUsers) {
            loadSystemUsers();
        }
    }, [loadSystemUsers, showSystemUsers]);

    useEffect(() => {
        if (!showSystemUsers && activeSection === 'systemUsers') {
            setActiveSection('auth');
        }
    }, [activeSection, showSystemUsers]);

    // Combined loading state
    const loading = settingsLoading || credentialsLoading || siteConfigLoading;

    // Menu items for sidebar navigation
    const menuItems = [
        {
            key: 'ai',
            icon: <SettingOutlined />,
            label: t('settings.ai_prompts', 'AI Prompts')
        },
        {
            key: 'aiModel',
            icon: <ApiOutlined />,
            label: t('settings.ai_model_credentials', 'AI Model')
        },
        {
            key: 'datasource',
            icon: <DatabaseOutlined />,
            label: t('settings.datasource_configuration', 'Data Source')
        },
        {
            key: 'auth',
            icon: <SafetyOutlined />,
            label: t('settings.auth_configuration', 'Authentication')
        },
        {
            key: 'proxy',
            icon: <CloudOutlined />,
            label: t('settings.proxy_configuration', 'Proxy')
        },
        {
            key: 'exchange',
            icon: <DollarOutlined />,
            label: t('settings.exchange_credentials', 'Exchange Credentials')
        },
        {
            key: 'site',
            icon: <GlobalOutlined />,
            label: t('settings.site_configuration', 'Site Configuration')
        }
    ];

    if (showSystemUsers) {
        menuItems.splice(4, 0, {
            key: 'systemUsers',
            icon: <SafetyOutlined />,
            label: t('settings.system_users.menu', 'System Users')
        });
    }

    // Render the active section content
    const renderContent = () => {
        switch (activeSection) {
            case 'ai':
                return (
                    <AISettingsSection
                        settings={settings}
                        loading={loading}
                        saved={saved}
                        onChange={handleChange}
                        onSave={handleSave}
                        onReset={handleReset}
                    />
                );
            case 'aiModel':
                return (
                    <AIModelSettingsSection
                        credentials={credentials}
                        sources={credentialSources}
                        loading={loading}
                        testing={testingCredential}
                        onCredentialChange={handleCredentialChange}
                        onSave={handleSaveCredentials}
                        onTest={handleTestCredential}
                        onReset={handleResetCredential}
                    />
                );
            case 'datasource':
                return (
                    <DataSourceSettingsSection
                        settings={dataSourceSettings}
                        loading={dataSourceLoading}
                        saved={dataSourceSaved}
                        onChange={handleDataSourceChange}
                        onSave={handleDataSourceSave}
                        onReset={handleDataSourceReset}
                    />
                );
            case 'auth':
                return (
                    <AuthSettingsSection
                        credentials={credentials}
                        sources={credentialSources}
                        loading={loading}
                        testing={testingCredential}
                        onCredentialChange={handleCredentialChange}
                        onSave={handleSaveCredentials}
                        onTest={handleTestCredential}
                        onReset={handleResetCredential}
                    />
                );
            case 'proxy':
                return (
                    <ProxySettingsSection
                        credentials={credentials}
                        sources={credentialSources}
                        loading={loading}
                        onCredentialChange={handleCredentialChange}
                        onSave={handleSaveCredentials}
                        onReset={handleResetCredential}
                    />
                );
            case 'systemUsers':
                return (
                    <SystemUsersSection
                        currentUserId={user?.id ?? null}
                        loading={systemUsersLoading}
                        users={systemUsers}
                        onReload={loadSystemUsers}
                    />
                );
            case 'exchange':
                return (
                    <ExchangeSettingsSection
                        credentials={credentials}
                        loading={loading}
                        testing={testingCredential}
                        onCCXTCredentialChange={handleCCXTCredentialChange}
                        onSave={handleSaveCredentials}
                        onTest={handleTestCredential}
                    />
                );
            case 'site':
                return (
                    <SiteSettingsSection
                        config={siteConfig}
                        sources={siteConfigSources}
                        loading={siteConfigLoading}
                        saved={siteConfigSaved}
                        onChange={handleSiteConfigChange}
                        onSave={handleSaveSiteConfig}
                        onReset={handleResetSiteConfig}
                    />
                );
            default:
                return (
                    <AISettingsSection
                        settings={settings}
                        loading={loading}
                        saved={saved}
                        onChange={handleChange}
                        onSave={handleSave}
                        onReset={handleReset}
                    />
                );
        }
    };

    return (
        <div className="settings-page">
            <div className="settings-header">
                <h1>{t('settings.title', 'Settings')}</h1>
            </div>
            <Layout className="settings-layout">
                <Sider width={250} className="settings-sider">
                    <Menu
                        mode="inline"
                        selectedKeys={[activeSection]}
                        items={menuItems}
                        onClick={({ key }) => setActiveSection(key)}
                    />
                </Sider>
                <Content className="settings-content">
                    {renderContent()}
                </Content>
            </Layout>
        </div>
    );
}

export default Settings;
