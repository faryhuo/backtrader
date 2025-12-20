import { useState, useEffect } from 'react';
import { useTranslation } from 'react-i18next';
import { SettingOutlined, ApiOutlined, SafetyOutlined, CloudOutlined, DollarOutlined } from '@ant-design/icons';
import { Layout, Menu } from 'antd';
import { useSettings } from '../hooks/useSettings';
import { useCredentials } from '../hooks/useCredentials';
import {
    AISettingsSection,
    OpenAISettingsSection,
    AuthSettingsSection,
    ProxySettingsSection,
    ExchangeSettingsSection
} from '../components/Settings';
import './Settings.css';

const { Sider, Content } = Layout;

function Settings() {
    const { t } = useTranslation();
    const [activeSection, setActiveSection] = useState('ai');

    // Use custom hooks for state management
    const {
        settings,
        loading: settingsLoading,
        saved,
        loadSettings,
        handleChange,
        handleModelChange,
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

    // Load data on mount
    useEffect(() => {
        loadSettings();
        loadCredentials();
    }, [loadSettings, loadCredentials]);

    // Combined loading state
    const loading = settingsLoading || credentialsLoading;

    // Menu items for sidebar navigation
    const menuItems = [
        {
            key: 'ai',
            icon: <SettingOutlined />,
            label: t('settings.ai_configuration', 'AI Configuration')
        },
        {
            key: 'openai',
            icon: <ApiOutlined />,
            label: t('settings.openai_credentials', 'OpenAI Credentials')
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
        }
    ];

    // Render the active section content
    const renderContent = () => {
        switch (activeSection) {
            case 'ai':
                return (
                    <AISettingsSection
                        settings={settings}
                        loading={loading}
                        saved={saved}
                        onModelChange={handleModelChange}
                        onChange={handleChange}
                        onSave={handleSave}
                        onReset={handleReset}
                    />
                );
            case 'openai':
                return (
                    <OpenAISettingsSection
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
            default:
                return (
                    <AISettingsSection
                        settings={settings}
                        loading={loading}
                        saved={saved}
                        onModelChange={handleModelChange}
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
