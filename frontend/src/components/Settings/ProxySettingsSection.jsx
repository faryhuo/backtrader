import { Card, Space, Input } from 'antd';
import { useTranslation } from 'react-i18next';
import CredentialSourceTag from './CredentialSourceTag';
import CredentialActions from './CredentialActions';

/**
 * Proxy Configuration settings section
 */
export function ProxySettingsSection({
    credentials,
    sources,
    loading,
    onCredentialChange,
    onSave,
    onReset
}) {
    const { t } = useTranslation();

    return (
        <Card title={t('settings.proxy_configuration', 'Proxy Configuration')} bordered={false}>
            <Space direction="vertical" style={{ width: '100%' }} size="large">
                <div>
                    <label>
                        {t('settings.http_proxy', 'HTTP Proxy')}
                        <CredentialSourceTag source={sources.http_proxy || 'env'} />
                    </label>
                    <Input
                        value={credentials.http_proxy}
                        onChange={(e) => onCredentialChange('http_proxy', e.target.value)}
                        placeholder="http://proxy.example.com:8080"
                        disabled={loading}
                    />
                </div>
                <div>
                    <label>
                        {t('settings.https_proxy', 'HTTPS Proxy')}
                        <CredentialSourceTag source={sources.https_proxy || 'env'} />
                    </label>
                    <Input
                        value={credentials.https_proxy}
                        onChange={(e) => onCredentialChange('https_proxy', e.target.value)}
                        placeholder="http://proxy.example.com:8080"
                        disabled={loading}
                    />
                </div>
                <CredentialActions
                    onSave={() => onSave('proxy')}
                    onReset={() => onReset('http_proxy')}
                    loading={loading}
                    showTest={false}
                />
            </Space>
        </Card>
    );
}

export default ProxySettingsSection;
