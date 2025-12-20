import { Card, Space, Input, Switch } from 'antd';
import { useTranslation } from 'react-i18next';
import CredentialSourceTag from './CredentialSourceTag';
import CredentialActions from './CredentialActions';

/**
 * Logto Authentication settings section
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
        <Card title={t('settings.auth_configuration', 'Logto Authentication Configuration')} bordered={false}>
            <Space direction="vertical" style={{ width: '100%' }} size="large">
                <div>
                    <label>{t('settings.enable_login', 'Enable Login')}</label>
                    <div>
                        <Switch
                            checked={credentials.enable_login}
                            onChange={(checked) => onCredentialChange('enable_login', checked)}
                            disabled={loading}
                        />
                    </div>
                </div>
                <div>
                    <label>
                        {t('settings.issuer_url', 'Issuer URL')}
                        <CredentialSourceTag source={sources.logto_issuer || 'env'} />
                    </label>
                    <Input
                        value={credentials.logto_issuer}
                        onChange={(e) => onCredentialChange('logto_issuer', e.target.value)}
                        placeholder="https://your-logto-instance.com"
                        disabled={loading}
                    />
                </div>
                <div>
                    <label>
                        {t('settings.jwks_uri', 'JWKS URI')}
                        <CredentialSourceTag source={sources.logto_jwks_uri || 'env'} />
                    </label>
                    <Input
                        value={credentials.logto_jwks_uri}
                        onChange={(e) => onCredentialChange('logto_jwks_uri', e.target.value)}
                        placeholder="https://your-logto-instance.com/oidc/jwks"
                        disabled={loading}
                    />
                </div>
                <div>
                    <label>{t('settings.audience', 'Audience')}</label>
                    <Input
                        value={credentials.logto_audience}
                        onChange={(e) => onCredentialChange('logto_audience', e.target.value)}
                        placeholder="https://api.your-app.com"
                        disabled={loading}
                    />
                </div>
                <div>
                    <label>{t('settings.required_scopes', 'Required Scopes')}</label>
                    <Input
                        value={credentials.logto_required_scopes}
                        onChange={(e) => onCredentialChange('logto_required_scopes', e.target.value)}
                        placeholder="openid profile email"
                        disabled={loading}
                    />
                </div>
                <CredentialActions
                    onSave={() => onSave('logto')}
                    onTest={() => onTest('logto')}
                    onReset={() => onReset('logto_issuer')}
                    loading={loading}
                    testing={testing === 'logto'}
                />
            </Space>
        </Card>
    );
}

export default AuthSettingsSection;
