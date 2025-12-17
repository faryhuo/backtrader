import { useState, useEffect } from 'react';
import { useTranslation } from 'react-i18next';
import { SaveOutlined, UndoOutlined, CheckCircleOutlined, ReloadOutlined } from '@ant-design/icons';
import { Select, message, Card, Input, Button, Space, Tabs, Tag, Switch } from 'antd';
import { api } from '../services/api';
import './Settings.css';

const DEFAULT_SETTINGS = {
    selectedModels: ['gpt-5.1', 'deepseek-v3.1'],
    codeAnalysisPrompt: 'Please analyze the following Backtrader strategy code. Explain its logic, potential pitfalls, and suggest improvements:\n\n{code}',
    codeRewritePrompt: 'Please rewrite and optimize the following Backtrader strategy code to follow best practices and fix potential issues. Return ONLY the python code, no markdown formatting or explanation:\n\n{code}',
    fullStrategyAnalysisPrompt: 'Please analyze the trading strategy based on the following configurations, source code, performance metrics, the attached equity curve chart, and the recent trading logs.\n\n{contextText}\n\n{metricsText}\n\n{logsText}\n\nProvide a comprehensive assessment including:\n1. Overall Performance: Is it profitable and consistent?\n2. Risk Profile: analysis of drawdowns and volatility.\n3. Strengths & Weaknesses: What is working well and what isn\'t?\n4. Suggestions: Recommendations for improvement.\n5. Code Analysis: Comments on the strategy logic.\n6. Always return with Chinese.\n7. 不需要对策略代码逻辑进行点评'
};

const AVAILABLE_MODELS = [
    { value: 'gpt-5.1', label: 'GPT-5.1' },
    { value: 'gpt-4o', label: 'GPT-4o' },
    { value: 'gpt-4-turbo', label: 'GPT-4 Turbo' },
    { value: 'gpt-3.5-turbo', label: 'GPT-3.5 Turbo' },
    { value: 'deepseek-v3.1', label: 'DeepSeek V3.1' },
    { value: 'gemini-3-pro', label: 'Gemini 3 Pro' }
];

function Settings() {
    const { t } = useTranslation();
    const [settings, setSettings] = useState(DEFAULT_SETTINGS);
    const [saved, setSaved] = useState(false);
    const [loading, setLoading] = useState(false);

    // Credential state
    const [credentials, setCredentials] = useState({
        openai_api_key: '',
        openai_base_url: '',
        logto_issuer: '',
        logto_jwks_uri: '',
        logto_audience: '',
        logto_required_scopes: '',
        enable_login: false,
        http_proxy: '',
        https_proxy: '',
        ccxt: {} // { binance: { paper: {api_key, secret}, live: {...} }, okx: {...}, bybit: {...} }
    });
    const [credentialSources, setCredentialSources] = useState({});
    const [testingCredential, setTestingCredential] = useState(null);

    useEffect(() => {
        loadSettings();
        loadCredentials();
    }, []);

    const loadSettings = async () => {
        try {
            setLoading(true);

            // Try to load from database
            const response = await api.getSettings();

            if (response.status === 'ok' && response.settings) {
                // Map backend field names to frontend
                const dbSettings = {
                    selectedModels: response.settings.selected_models || DEFAULT_SETTINGS.selectedModels,
                    codeAnalysisPrompt: response.settings.code_analysis_prompt || DEFAULT_SETTINGS.codeAnalysisPrompt,
                    codeRewritePrompt: response.settings.code_rewrite_prompt || DEFAULT_SETTINGS.codeRewritePrompt,
                    fullStrategyAnalysisPrompt: response.settings.full_strategy_analysis_prompt || DEFAULT_SETTINGS.fullStrategyAnalysisPrompt
                };
                setSettings(dbSettings);

                // Check if settings are defaults (not saved yet), try localStorage migration
                const isDefaults = JSON.stringify(dbSettings.selectedModels) === JSON.stringify(DEFAULT_SETTINGS.selectedModels) &&
                    dbSettings.codeAnalysisPrompt === DEFAULT_SETTINGS.codeAnalysisPrompt;

                if (isDefaults) {
                    await migrateFromLocalStorage();
                }
            } else {
                // Fallback: try localStorage migration
                await migrateFromLocalStorage();
            }
        } catch (error) {
            console.error('Failed to load settings from database:', error);
            // Fallback to localStorage
            await migrateFromLocalStorage();
        } finally {
            setLoading(false);
        }
    };

    const migrateFromLocalStorage = async () => {
        const storedSettings = localStorage.getItem('userSettings');
        if (storedSettings) {
            try {
                const parsed = JSON.parse(storedSettings);

                // Migration: old aiModel -> selectedModels
                if (parsed.aiModel && !parsed.selectedModels) {
                    parsed.selectedModels = [parsed.aiModel];
                    delete parsed.aiModel;
                }

                const migratedSettings = { ...DEFAULT_SETTINGS, ...parsed };
                setSettings(migratedSettings);

                // Auto-save to database (silent migration)
                try {
                    await saveToDatabase(migratedSettings, false);
                    console.log('Successfully migrated settings from localStorage to database');
                } catch (e) {
                    console.warn('Failed to auto-migrate settings to database:', e);
                }
            } catch (e) {
                console.error('Failed to parse localStorage settings:', e);
                setSettings(DEFAULT_SETTINGS);
            }
        }
    };

    const handleChange = (key, value) => {
        setSettings(prev => ({ ...prev, [key]: value }));
        setSaved(false);
    };

    const handleModelChange = (value) => {
        setSettings(prev => ({ ...prev, selectedModels: value }));
        setSaved(false);
    };

    const saveToDatabase = async (settingsToSave, showMessage = true) => {
        const payload = {
            selected_models: settingsToSave.selectedModels,
            code_analysis_prompt: settingsToSave.codeAnalysisPrompt,
            code_rewrite_prompt: settingsToSave.codeRewritePrompt,
            full_strategy_analysis_prompt: settingsToSave.fullStrategyAnalysisPrompt
        };

        const response = await api.updateSettings(payload);

        if (response.status === 'ok') {
            if (showMessage) {
                message.success(t('settings.saved', 'Settings saved!'));
            }
            return true;
        }
        return false;
    };

    const handleSave = async () => {
        try {
            setLoading(true);

            // Validate at least one model selected
            if (!settings.selectedModels || settings.selectedModels.length === 0) {
                message.error(t('settings.select_at_least_one', 'Please select at least one model.'));
                return;
            }

            // Try to save to database
            try {
                await saveToDatabase(settings, true);
                setSaved(true);
                setTimeout(() => setSaved(false), 3000);

                // Clear localStorage after successful DB save (optional)
                // localStorage.removeItem('userSettings');
            } catch (error) {
                console.error('Database save failed, falling back to localStorage:', error);
                message.warning('Saved to local storage (database unavailable)');

                // Fallback to localStorage
                localStorage.setItem('userSettings', JSON.stringify(settings));
                setSaved(true);
                setTimeout(() => setSaved(false), 3000);
            }
        } finally {
            setLoading(false);
        }
    };

    const handleReset = async () => {
        if (window.confirm(t('settings.confirm_reset', 'Are you sure you want to reset all settings to default?'))) {
            try {
                setLoading(true);

                // Try to reset in database
                try {
                    const response = await api.resetSettings();
                    if (response.status === 'ok') {
                        setSettings(DEFAULT_SETTINGS);
                        message.success(t('settings.reset_success', 'Settings reset to defaults'));
                        setSaved(true);
                        setTimeout(() => setSaved(false), 3000);
                    }
                } catch (error) {
                    console.error('Database reset failed, using localStorage:', error);

                    // Fallback to localStorage
                    setSettings(DEFAULT_SETTINGS);
                    localStorage.removeItem('userSettings');
                    message.success(t('settings.reset_success', 'Settings reset to defaults'));
                    setSaved(true);
                    setTimeout(() => setSaved(false), 3000);
                }
            } finally {
                setLoading(false);
            }
        }
    };

    // Credential management functions
    const loadCredentials = async () => {
        try {
            const response = await api.getCredentials();
            if (response.credentials) {
                setCredentials(response.credentials);
                setCredentialSources(response.sources || {});
            }
        } catch (error) {
            console.error('Failed to load credentials:', error);
            message.error('Failed to load credentials');
        }
    };

    const handleCredentialChange = (key, value) => {
        setCredentials(prev => ({ ...prev, [key]: value }));
    };

    const handleCCXTCredentialChange = (exchange, mode, field, value) => {
        setCredentials(prev => ({
            ...prev,
            ccxt: {
                ...prev.ccxt,
                [exchange]: {
                    ...prev.ccxt[exchange],
                    [mode]: {
                        ...prev.ccxt[exchange]?.[mode],
                        [field]: value
                    }
                }
            }
        }));
    };

    const handleSaveCredentials = async (credentialType) => {
        try {
            setLoading(true);
            let response;

            if (credentialType === 'openai') {
                response = await api.updateCredentials({
                    openai_api_key: credentials.openai_api_key,
                    openai_base_url: credentials.openai_base_url
                });
            } else if (credentialType === 'logto') {
                response = await api.updateCredentials({
                    logto_issuer: credentials.logto_issuer,
                    logto_jwks_uri: credentials.logto_jwks_uri,
                    logto_audience: credentials.logto_audience,
                    logto_required_scopes: credentials.logto_required_scopes,
                    enable_login: credentials.enable_login
                });
            } else if (credentialType === 'proxy') {
                response = await api.updateCredentials({
                    http_proxy: credentials.http_proxy,
                    https_proxy: credentials.https_proxy
                });
            } else if (credentialType.startsWith('ccxt-')) {
                const [, exchange, mode] = credentialType.split('-');
                const creds = credentials.ccxt[exchange]?.[mode] || {};
                response = await api.updateCCXTCredentials(exchange, mode, creds);
            }

            if (response.status === 'ok') {
                message.success('Credentials saved successfully');
                await loadCredentials(); // Reload to get masked values
            }
        } catch (error) {
            console.error('Failed to save credentials:', error);
            message.error(error.message || 'Failed to save credentials');
        } finally {
            setLoading(false);
        }
    };

    const handleTestCredential = async (credentialType) => {
        try {
            setTestingCredential(credentialType);
            let params = {};

            if (credentialType === 'openai') {
                params = {
                    credential_type: 'openai',
                    api_key: credentials.openai_api_key,
                    base_url: credentials.openai_base_url
                };
            } else if (credentialType === 'logto') {
                params = {
                    credential_type: 'logto',
                    issuer: credentials.logto_issuer,
                    jwks_uri: credentials.logto_jwks_uri
                };
            } else if (credentialType.startsWith('ccxt-')) {
                const [, exchange, mode] = credentialType.split('-');
                const creds = credentials.ccxt[exchange]?.[mode] || {};
                params = {
                    credential_type: 'ccxt',
                    exchange,
                    mode,
                    api_key: creds.api_key,
                    secret: creds.secret,
                    passphrase: creds.passphrase
                };
            }

            const response = await api.testCredential(params.credential_type, params);

            if (response.valid) {
                message.success(response.message || 'Credentials are valid');
            } else {
                message.error(response.message || 'Credentials are invalid');
            }
        } catch (error) {
            console.error('Failed to test credentials:', error);
            message.error(error.message || 'Failed to test credentials');
        } finally {
            setTestingCredential(null);
        }
    };

    const handleResetCredential = async (credentialKey) => {
        try {
            setLoading(true);
            const response = await api.resetCredential(credentialKey);

            if (response.status === 'ok') {
                message.success(`Reset ${credentialKey} to .env value`);
                await loadCredentials(); // Reload to get .env values
            }
        } catch (error) {
            console.error('Failed to reset credential:', error);
            message.error(error.message || 'Failed to reset credential');
        } finally {
            setLoading(false);
        }
    };

    const renderSourceTag = (key) => {
        const source = credentialSources[key] || 'env';
        return (
            <Tag color={source === 'database' ? 'green' : 'blue'} style={{ marginLeft: 8 }}>
                {source === 'database' ? 'Database' : '.env'}
            </Tag>
        );
    };

    return (
        <div className="page-container settings-page">
            <div className="settings-header">
                <h1>{t('settings.title', 'Settings')}</h1>
            </div>

            <div className="settings-section">
                <h2>{t('settings.ai_configuration', 'AI Configuration')}</h2>

                <div className="settings-form-group">
                    <label>{t('settings.default_model', 'Enabled AI Models (Select or Type to Add)')}</label>
                    <Select
                        mode="tags"
                        style={{ width: '100%' }}
                        placeholder="Select or type model names"
                        value={settings.selectedModels}
                        onChange={handleModelChange}
                        options={AVAILABLE_MODELS}
                        loading={loading}
                    />
                    {(!settings.selectedModels || settings.selectedModels.length === 0) && (
                        <p style={{ color: 'var(--error-color)', fontSize: '0.9rem', marginTop: '0.5rem' }}>
                            {t('settings.select_at_least_one', 'Please select at least one model.')}
                        </p>
                    )}
                </div>

                <div className="settings-form-group">
                    <label>{t('settings.code_analysis_prompt', 'Code Analysis Prompt')}</label>
                    <textarea
                        className="settings-textarea"
                        value={settings.codeAnalysisPrompt}
                        onChange={(e) => handleChange('codeAnalysisPrompt', e.target.value)}
                        placeholder="Use {code} as placeholder"
                        disabled={loading}
                    />
                </div>

                <div className="settings-form-group">
                    <label>{t('settings.full_strategy_analysis_prompt', 'Full Strategy Analysis Prompt')}</label>
                    <textarea
                        className="settings-textarea"
                        rows={6}
                        value={settings.fullStrategyAnalysisPrompt}
                        onChange={(e) => handleChange('fullStrategyAnalysisPrompt', e.target.value)}
                        placeholder="Use {contextText}, {metricsText}, {logsText} as placeholders"
                        disabled={loading}
                    />
                </div>

                <div className="settings-form-group">
                    <label>{t('settings.code_rewrite_prompt', 'Code Rewrite Prompt')}</label>
                    <textarea
                        className="settings-textarea"
                        value={settings.codeRewritePrompt}
                        onChange={(e) => handleChange('codeRewritePrompt', e.target.value)}
                        placeholder="Use {code} as placeholder"
                        disabled={loading}
                    />
                </div>

                <div className="settings-actions">
                    <span className={`save-success ${saved ? 'visible' : ''}`}>
                        {t('settings.saved', 'Settings saved!')}
                    </span>
                    <button className="btn-secondary" onClick={handleReset} disabled={loading}>
                        <UndoOutlined /> {t('settings.reset', 'Reset Defaults')}
                    </button>
                    <button className="primary-btn" onClick={handleSave} disabled={loading}>
                        <SaveOutlined /> {t('settings.save', 'Save Changes')}
                    </button>
                </div>
            </div>

            {/* Credential Configuration Section */}
            <div className="settings-section">
                <h2>Credentials Configuration</h2>
                <p style={{ color: '#888', marginBottom: '1rem' }}>
                    Configure API credentials. Values saved here take precedence over .env file.
                </p>

                {/* OpenAI Configuration */}
                <Card title="OpenAI Configuration" style={{ marginBottom: '1rem' }}>
                    <Space direction="vertical" style={{ width: '100%' }} size="large">
                        <div>
                            <label>
                                API Key {renderSourceTag('openai_api_key')}
                            </label>
                            <Input.Password
                                value={credentials.openai_api_key}
                                onChange={(e) => handleCredentialChange('openai_api_key', e.target.value)}
                                placeholder="sk-..."
                                disabled={loading}
                            />
                        </div>
                        <div>
                            <label>Base URL</label>
                            <Input
                                value={credentials.openai_base_url}
                                onChange={(e) => handleCredentialChange('openai_base_url', e.target.value)}
                                placeholder="https://api.openai.com/v1"
                                disabled={loading}
                            />
                        </div>
                        <Space>
                            <Button
                                type="primary"
                                icon={<SaveOutlined />}
                                onClick={() => handleSaveCredentials('openai')}
                                loading={loading}
                            >
                                Save
                            </Button>
                            <Button
                                icon={<CheckCircleOutlined />}
                                onClick={() => handleTestCredential('openai')}
                                loading={testingCredential === 'openai'}
                            >
                                Test
                            </Button>
                            <Button
                                icon={<ReloadOutlined />}
                                onClick={() => handleResetCredential('openai_api_key')}
                                loading={loading}
                            >
                                Reset to .env
                            </Button>
                        </Space>
                    </Space>
                </Card>

                {/* Logto Configuration */}
                <Card title="Logto Authentication Configuration" style={{ marginBottom: '1rem' }}>
                    <Space direction="vertical" style={{ width: '100%' }} size="large">
                        <div>
                            <label>Enable Login</label>
                            <div>
                                <Switch
                                    checked={credentials.enable_login}
                                    onChange={(checked) => handleCredentialChange('enable_login', checked)}
                                    disabled={loading}
                                />
                            </div>
                        </div>
                        <div>
                            <label>Issuer URL {renderSourceTag('logto_issuer')}</label>
                            <Input
                                value={credentials.logto_issuer}
                                onChange={(e) => handleCredentialChange('logto_issuer', e.target.value)}
                                placeholder="https://your-logto-instance.com"
                                disabled={loading}
                            />
                        </div>
                        <div>
                            <label>JWKS URI {renderSourceTag('logto_jwks_uri')}</label>
                            <Input
                                value={credentials.logto_jwks_uri}
                                onChange={(e) => handleCredentialChange('logto_jwks_uri', e.target.value)}
                                placeholder="https://your-logto-instance.com/oidc/jwks"
                                disabled={loading}
                            />
                        </div>
                        <div>
                            <label>Audience</label>
                            <Input
                                value={credentials.logto_audience}
                                onChange={(e) => handleCredentialChange('logto_audience', e.target.value)}
                                placeholder="https://api.your-app.com"
                                disabled={loading}
                            />
                        </div>
                        <div>
                            <label>Required Scopes</label>
                            <Input
                                value={credentials.logto_required_scopes}
                                onChange={(e) => handleCredentialChange('logto_required_scopes', e.target.value)}
                                placeholder="openid profile email"
                                disabled={loading}
                            />
                        </div>
                        <Space>
                            <Button
                                type="primary"
                                icon={<SaveOutlined />}
                                onClick={() => handleSaveCredentials('logto')}
                                loading={loading}
                            >
                                Save
                            </Button>
                            <Button
                                icon={<CheckCircleOutlined />}
                                onClick={() => handleTestCredential('logto')}
                                loading={testingCredential === 'logto'}
                            >
                                Test
                            </Button>
                            <Button
                                icon={<ReloadOutlined />}
                                onClick={() => handleResetCredential('logto_issuer')}
                                loading={loading}
                            >
                                Reset to .env
                            </Button>
                        </Space>
                    </Space>
                </Card>

                {/* Proxy Configuration */}
                <Card title="Proxy Configuration" style={{ marginBottom: '1rem' }}>
                    <Space direction="vertical" style={{ width: '100%' }} size="large">
                        <div>
                            <label>HTTP Proxy {renderSourceTag('http_proxy')}</label>
                            <Input
                                value={credentials.http_proxy}
                                onChange={(e) => handleCredentialChange('http_proxy', e.target.value)}
                                placeholder="http://proxy.example.com:8080"
                                disabled={loading}
                            />
                        </div>
                        <div>
                            <label>HTTPS Proxy {renderSourceTag('https_proxy')}</label>
                            <Input
                                value={credentials.https_proxy}
                                onChange={(e) => handleCredentialChange('https_proxy', e.target.value)}
                                placeholder="http://proxy.example.com:8080"
                                disabled={loading}
                            />
                        </div>
                        <Space>
                            <Button
                                type="primary"
                                icon={<SaveOutlined />}
                                onClick={() => handleSaveCredentials('proxy')}
                                loading={loading}
                            >
                                Save
                            </Button>
                            <Button
                                icon={<ReloadOutlined />}
                                onClick={() => handleResetCredential('http_proxy')}
                                loading={loading}
                            >
                                Reset to .env
                            </Button>
                        </Space>
                    </Space>
                </Card>

                {/* Exchange Credentials */}
                <Card title="Exchange Credentials" style={{ marginBottom: '1rem' }}>
                    <Tabs
                        items={[
                            {
                                key: 'binance',
                                label: 'Binance',
                                children: (
                                    <Tabs
                                        items={[
                                            {
                                                key: 'paper',
                                                label: 'Paper (Testnet)',
                                                children: (
                                                    <Space direction="vertical" style={{ width: '100%' }} size="large">
                                                        <div>
                                                            <label>API Key</label>
                                                            <Input.Password
                                                                value={credentials.ccxt?.binance?.paper?.api_key || ''}
                                                                onChange={(e) => handleCCXTCredentialChange('binance', 'paper', 'api_key', e.target.value)}
                                                                placeholder="API Key"
                                                                disabled={loading}
                                                            />
                                                        </div>
                                                        <div>
                                                            <label>Secret</label>
                                                            <Input.Password
                                                                value={credentials.ccxt?.binance?.paper?.secret || ''}
                                                                onChange={(e) => handleCCXTCredentialChange('binance', 'paper', 'secret', e.target.value)}
                                                                placeholder="Secret"
                                                                disabled={loading}
                                                            />
                                                        </div>
                                                        <Space>
                                                            <Button
                                                                type="primary"
                                                                icon={<SaveOutlined />}
                                                                onClick={() => handleSaveCredentials('ccxt-binance-paper')}
                                                                loading={loading}
                                                            >
                                                                Save
                                                            </Button>
                                                            <Button
                                                                icon={<CheckCircleOutlined />}
                                                                onClick={() => handleTestCredential('ccxt-binance-paper')}
                                                                loading={testingCredential === 'ccxt-binance-paper'}
                                                            >
                                                                Test
                                                            </Button>
                                                        </Space>
                                                    </Space>
                                                )
                                            },
                                            {
                                                key: 'live',
                                                label: 'Live (Production)',
                                                children: (
                                                    <Space direction="vertical" style={{ width: '100%' }} size="large">
                                                        <div>
                                                            <label>API Key</label>
                                                            <Input.Password
                                                                value={credentials.ccxt?.binance?.live?.api_key || ''}
                                                                onChange={(e) => handleCCXTCredentialChange('binance', 'live', 'api_key', e.target.value)}
                                                                placeholder="API Key"
                                                                disabled={loading}
                                                            />
                                                        </div>
                                                        <div>
                                                            <label>Secret</label>
                                                            <Input.Password
                                                                value={credentials.ccxt?.binance?.live?.secret || ''}
                                                                onChange={(e) => handleCCXTCredentialChange('binance', 'live', 'secret', e.target.value)}
                                                                placeholder="Secret"
                                                                disabled={loading}
                                                            />
                                                        </div>
                                                        <Space>
                                                            <Button
                                                                type="primary"
                                                                icon={<SaveOutlined />}
                                                                onClick={() => handleSaveCredentials('ccxt-binance-live')}
                                                                loading={loading}
                                                            >
                                                                Save
                                                            </Button>
                                                            <Button
                                                                icon={<CheckCircleOutlined />}
                                                                onClick={() => handleTestCredential('ccxt-binance-live')}
                                                                loading={testingCredential === 'ccxt-binance-live'}
                                                            >
                                                                Test
                                                            </Button>
                                                        </Space>
                                                    </Space>
                                                )
                                            }
                                        ]}
                                    />
                                )
                            },
                            {
                                key: 'okx',
                                label: 'OKX',
                                children: (
                                    <Tabs
                                        items={[
                                            {
                                                key: 'paper',
                                                label: 'Paper (Testnet)',
                                                children: (
                                                    <Space direction="vertical" style={{ width: '100%' }} size="large">
                                                        <div>
                                                            <label>API Key</label>
                                                            <Input.Password
                                                                value={credentials.ccxt?.okx?.paper?.api_key || ''}
                                                                onChange={(e) => handleCCXTCredentialChange('okx', 'paper', 'api_key', e.target.value)}
                                                                placeholder="API Key"
                                                                disabled={loading}
                                                            />
                                                        </div>
                                                        <div>
                                                            <label>Secret</label>
                                                            <Input.Password
                                                                value={credentials.ccxt?.okx?.paper?.secret || ''}
                                                                onChange={(e) => handleCCXTCredentialChange('okx', 'paper', 'secret', e.target.value)}
                                                                placeholder="Secret"
                                                                disabled={loading}
                                                            />
                                                        </div>
                                                        <div>
                                                            <label>Passphrase</label>
                                                            <Input.Password
                                                                value={credentials.ccxt?.okx?.paper?.passphrase || ''}
                                                                onChange={(e) => handleCCXTCredentialChange('okx', 'paper', 'passphrase', e.target.value)}
                                                                placeholder="Passphrase"
                                                                disabled={loading}
                                                            />
                                                        </div>
                                                        <Space>
                                                            <Button
                                                                type="primary"
                                                                icon={<SaveOutlined />}
                                                                onClick={() => handleSaveCredentials('ccxt-okx-paper')}
                                                                loading={loading}
                                                            >
                                                                Save
                                                            </Button>
                                                            <Button
                                                                icon={<CheckCircleOutlined />}
                                                                onClick={() => handleTestCredential('ccxt-okx-paper')}
                                                                loading={testingCredential === 'ccxt-okx-paper'}
                                                            >
                                                                Test
                                                            </Button>
                                                        </Space>
                                                    </Space>
                                                )
                                            },
                                            {
                                                key: 'live',
                                                label: 'Live (Production)',
                                                children: (
                                                    <Space direction="vertical" style={{ width: '100%' }} size="large">
                                                        <div>
                                                            <label>API Key</label>
                                                            <Input.Password
                                                                value={credentials.ccxt?.okx?.live?.api_key || ''}
                                                                onChange={(e) => handleCCXTCredentialChange('okx', 'live', 'api_key', e.target.value)}
                                                                placeholder="API Key"
                                                                disabled={loading}
                                                            />
                                                        </div>
                                                        <div>
                                                            <label>Secret</label>
                                                            <Input.Password
                                                                value={credentials.ccxt?.okx?.live?.secret || ''}
                                                                onChange={(e) => handleCCXTCredentialChange('okx', 'live', 'secret', e.target.value)}
                                                                placeholder="Secret"
                                                                disabled={loading}
                                                            />
                                                        </div>
                                                        <div>
                                                            <label>Passphrase</label>
                                                            <Input.Password
                                                                value={credentials.ccxt?.okx?.live?.passphrase || ''}
                                                                onChange={(e) => handleCCXTCredentialChange('okx', 'live', 'passphrase', e.target.value)}
                                                                placeholder="Passphrase"
                                                                disabled={loading}
                                                            />
                                                        </div>
                                                        <Space>
                                                            <Button
                                                                type="primary"
                                                                icon={<SaveOutlined />}
                                                                onClick={() => handleSaveCredentials('ccxt-okx-live')}
                                                                loading={loading}
                                                            >
                                                                Save
                                                            </Button>
                                                            <Button
                                                                icon={<CheckCircleOutlined />}
                                                                onClick={() => handleTestCredential('ccxt-okx-live')}
                                                                loading={testingCredential === 'ccxt-okx-live'}
                                                            >
                                                                Test
                                                            </Button>
                                                        </Space>
                                                    </Space>
                                                )
                                            }
                                        ]}
                                    />
                                )
                            },
                            {
                                key: 'bybit',
                                label: 'Bybit',
                                children: (
                                    <Tabs
                                        items={[
                                            {
                                                key: 'paper',
                                                label: 'Paper (Testnet)',
                                                children: (
                                                    <Space direction="vertical" style={{ width: '100%' }} size="large">
                                                        <div>
                                                            <label>API Key</label>
                                                            <Input.Password
                                                                value={credentials.ccxt?.bybit?.paper?.api_key || ''}
                                                                onChange={(e) => handleCCXTCredentialChange('bybit', 'paper', 'api_key', e.target.value)}
                                                                placeholder="API Key"
                                                                disabled={loading}
                                                            />
                                                        </div>
                                                        <div>
                                                            <label>Secret</label>
                                                            <Input.Password
                                                                value={credentials.ccxt?.bybit?.paper?.secret || ''}
                                                                onChange={(e) => handleCCXTCredentialChange('bybit', 'paper', 'secret', e.target.value)}
                                                                placeholder="Secret"
                                                                disabled={loading}
                                                            />
                                                        </div>
                                                        <Space>
                                                            <Button
                                                                type="primary"
                                                                icon={<SaveOutlined />}
                                                                onClick={() => handleSaveCredentials('ccxt-bybit-paper')}
                                                                loading={loading}
                                                            >
                                                                Save
                                                            </Button>
                                                            <Button
                                                                icon={<CheckCircleOutlined />}
                                                                onClick={() => handleTestCredential('ccxt-bybit-paper')}
                                                                loading={testingCredential === 'ccxt-bybit-paper'}
                                                            >
                                                                Test
                                                            </Button>
                                                        </Space>
                                                    </Space>
                                                )
                                            },
                                            {
                                                key: 'live',
                                                label: 'Live (Production)',
                                                children: (
                                                    <Space direction="vertical" style={{ width: '100%' }} size="large">
                                                        <div>
                                                            <label>API Key</label>
                                                            <Input.Password
                                                                value={credentials.ccxt?.bybit?.live?.api_key || ''}
                                                                onChange={(e) => handleCCXTCredentialChange('bybit', 'live', 'api_key', e.target.value)}
                                                                placeholder="API Key"
                                                                disabled={loading}
                                                            />
                                                        </div>
                                                        <div>
                                                            <label>Secret</label>
                                                            <Input.Password
                                                                value={credentials.ccxt?.bybit?.live?.secret || ''}
                                                                onChange={(e) => handleCCXTCredentialChange('bybit', 'live', 'secret', e.target.value)}
                                                                placeholder="Secret"
                                                                disabled={loading}
                                                            />
                                                        </div>
                                                        <Space>
                                                            <Button
                                                                type="primary"
                                                                icon={<SaveOutlined />}
                                                                onClick={() => handleSaveCredentials('ccxt-bybit-live')}
                                                                loading={loading}
                                                            >
                                                                Save
                                                            </Button>
                                                            <Button
                                                                icon={<CheckCircleOutlined />}
                                                                onClick={() => handleTestCredential('ccxt-bybit-live')}
                                                                loading={testingCredential === 'ccxt-bybit-live'}
                                                            >
                                                                Test
                                                            </Button>
                                                        </Space>
                                                    </Space>
                                                )
                                            }
                                        ]}
                                    />
                                )
                            }
                        ]}
                    />
                </Card>
            </div>
        </div>
    );
}

export default Settings;
