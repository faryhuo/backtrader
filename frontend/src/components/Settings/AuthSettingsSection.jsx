import { Card, Input, Radio, Space, Switch, Typography } from 'antd';
import { useTranslation } from 'react-i18next';
import CredentialSourceTag from './CredentialSourceTag';
import CredentialActions from './CredentialActions';

const { Text } = Typography;

/**
 * Logto Authentication settings section
 * Unified configuration for both server-side validation and frontend OAuth flow
 */
export function AuthSettingsSection({
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

    return (
        <Card title={t('settings.auth_configuration', 'Authentication Configuration')} bordered={false}>
            <Space direction="vertical" style={{ width: '100%' }} size="large">
                {/* Enable Login Toggle */}
                <div>
                    <label>{t('settings.enable_login', 'Enable Login')}</label>
                    <div>
                        <Switch
                            checked={credentials.enable_login}
                            onChange={(checked) => {
                                onCredentialChange('enable_login', checked)
                                if (checked && (!credentials.auth_provider || credentials.auth_provider === 'none')) {
                                    onCredentialChange('auth_provider', 'system')
                                }
                                if (!checked) {
                                    onCredentialChange('auth_provider', 'none')
                                }
                            }}
                            disabled={loading}
                        />
                        <Text type="secondary" style={{ marginLeft: 12 }}>
                            {t('settings.enable_login_hint', 'If disabled, users can access the app without authentication')}
                        </Text>
                    </div>
                </div>

                <div>
                    <label>{t('settings.auth_provider', 'Authentication Provider')}</label>
                    <Radio.Group
                        value={credentials.auth_provider || 'none'}
                        onChange={(event) => onCredentialChange('auth_provider', event.target.value)}
                        disabled={loading || !credentials.enable_login}
                    >
                        <Space direction="vertical">
                            <Radio value="none">{t('settings.auth_provider_none', 'None')}</Radio>
                            <Radio value="system">{t('settings.auth_provider_system', 'Built-in Email Login')}</Radio>
                            <Radio value="logto">{t('settings.auth_provider_logto', 'Logto')}</Radio>
                        </Space>
                    </Radio.Group>
                    <Text type="secondary" style={{ fontSize: 12 }}>
                        {t('settings.auth_provider_hint', 'Choose which login backend this instance should use when authentication is enabled.')}
                    </Text>
                </div>

                {credentials.auth_provider === 'system' && credentials.enable_login && (
                    <div>
                        <label>{t('settings.system_auth_allow_registration', 'Allow Self Registration')}</label>
                        <div>
                            <Switch
                                checked={credentials.system_auth_allow_registration}
                                onChange={(checked) => onCredentialChange('system_auth_allow_registration', checked)}
                                disabled={loading}
                            />
                            <Text type="secondary" style={{ marginLeft: 12 }}>
                                {t('settings.system_auth_allow_registration_hint', 'Allow users to create their own email/password accounts from the login page.')}
                            </Text>
                        </div>
                    </div>
                )}

                {credentials.auth_provider === 'logto' && credentials.enable_login && (
                    <>
                        {/* Server-side JWT Validation */}
                        <div>
                            <label>
                                {t('settings.issuer_url', 'Issuer URL')}
                                <CredentialSourceTag source={sources.logto_issuer || 'env'} />
                            </label>
                            <Input
                                value={credentials.logto_issuer}
                                onChange={(e) => onCredentialChange('logto_issuer', e.target.value)}
                                placeholder="https://logto.yourdomain.com"
                                disabled={loading}
                            />
                            <Text type="secondary" style={{ fontSize: 12 }}>
                                {t('settings.issuer_url_hint', 'Logto issuer URL for server-side JWT validation')}
                            </Text>
                        </div>

                        <div>
                            <label>
                                {t('settings.jwks_uri', 'JWKS URI')}
                                <CredentialSourceTag source={sources.logto_jwks_uri || 'env'} />
                            </label>
                            <Input
                                value={credentials.logto_jwks_uri}
                                onChange={(e) => onCredentialChange('logto_jwks_uri', e.target.value)}
                                placeholder="https://logto.yourdomain.com/oidc/jwks"
                                disabled={loading}
                            />
                            <Text type="secondary" style={{ fontSize: 12 }}>
                                {t('settings.jwks_uri_hint', 'JWKS endpoint for public key verification')}
                            </Text>
                        </div>

                        <div>
                            <label>
                                {t('settings.audience', 'Audience')}
                                <CredentialSourceTag source={sources.logto_audience || 'env'} />
                            </label>
                            <Input
                                value={credentials.logto_audience}
                                onChange={(e) => onCredentialChange('logto_audience', e.target.value)}
                                placeholder="https://api.yourdomain.com"
                                disabled={loading}
                            />
                            <Text type="secondary" style={{ fontSize: 12 }}>
                                {t('settings.audience_hint', 'API audience for token validation')}
                            </Text>
                        </div>

                        <div>
                            <label>
                                {t('settings.required_scopes', 'Required Scopes')}
                                <CredentialSourceTag source={sources.logto_required_scopes || 'env'} />
                            </label>
                            <Input
                                value={credentials.logto_required_scopes}
                                onChange={(e) => onCredentialChange('logto_required_scopes', e.target.value)}
                                placeholder="openid profile email"
                                disabled={loading}
                            />
                            <Text type="secondary" style={{ fontSize: 12 }}>
                                {t('settings.required_scopes_hint', 'OAuth scopes required for authentication')}
                            </Text>
                        </div>

                        {/* Frontend OAuth Configuration */}
                        <div>
                            <label>
                                {t('settings.logto_endpoint', 'Logto Endpoint')}
                                <CredentialSourceTag source={sources.logto_endpoint || 'env'} />
                            </label>
                            <Input
                                value={credentials.logto_endpoint}
                                onChange={(e) => onCredentialChange('logto_endpoint', e.target.value)}
                                placeholder="https://logto.yourdomain.com"
                                disabled={loading}
                            />
                            <Text type="secondary" style={{ fontSize: 12 }}>
                                {t('settings.logto_endpoint_hint', 'Logto server endpoint for OAuth 2.0 flow (same as Issuer URL typically)')}
                            </Text>
                        </div>

                        <div>
                            <label>
                                {t('settings.logto_app_id', 'Application (Client) ID')}
                                <CredentialSourceTag source={sources.logto_app_id || 'env'} />
                            </label>
                            <Input
                                value={credentials.logto_app_id}
                                onChange={(e) => onCredentialChange('logto_app_id', e.target.value)}
                                placeholder="app_id_from_logto"
                                disabled={loading}
                            />
                            <Text type="secondary" style={{ fontSize: 12 }}>
                                {t('settings.logto_app_id_hint', 'Application (client) ID from your Logto console')}
                            </Text>
                        </div>

                        <div>
                            <label>
                                {t('settings.logto_redirect_uri', 'Redirect URI')}
                                <CredentialSourceTag source={sources.logto_redirect_uri || 'env'} />
                            </label>
                            <Input
                                value={credentials.logto_redirect_uri}
                                onChange={(e) => onCredentialChange('logto_redirect_uri', e.target.value)}
                                placeholder="http://localhost:5173/callback"
                                disabled={loading}
                            />
                            <Text type="secondary" style={{ fontSize: 12 }}>
                                {t('settings.logto_redirect_uri_hint', 'OAuth callback URL after successful login')}
                            </Text>
                        </div>

                        <div>
                            <label>
                                {t('settings.logto_post_logout_redirect_uri', 'Post-Logout Redirect URI')}
                                <CredentialSourceTag source={sources.logto_post_logout_redirect_uri || 'env'} />
                            </label>
                            <Input
                                value={credentials.logto_post_logout_redirect_uri}
                                onChange={(e) => onCredentialChange('logto_post_logout_redirect_uri', e.target.value)}
                                placeholder="http://localhost:5173/login"
                                disabled={loading}
                            />
                            <Text type="secondary" style={{ fontSize: 12 }}>
                                {t('settings.logto_post_logout_redirect_uri_hint', 'Redirect URL after user logs out')}
                            </Text>
                        </div>
                    </>
                )}

                <CredentialActions
                    onSave={() => onSave('logto')}
                    onTest={credentials.auth_provider === 'logto' ? () => onTest('logto') : null}
                    onReset={credentials.auth_provider === 'logto' ? () => onReset('logto_issuer') : null}
                    loading={loading}
                    testing={testing === 'logto'}
                    showTest={credentials.auth_provider === 'logto'}
                    showReset={credentials.auth_provider === 'logto'}
                />
            </Space>
        </Card>
    );
}

export default AuthSettingsSection;
