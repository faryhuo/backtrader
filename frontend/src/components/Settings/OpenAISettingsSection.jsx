import { Card, Space, Input } from 'antd';
import { useTranslation } from 'react-i18next';
import CredentialSourceTag from './CredentialSourceTag';
import CredentialActions from './CredentialActions';

/**
 * OpenAI Credentials settings section
 */
export function OpenAISettingsSection({
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
        <Card title={t('settings.openai_credentials', 'OpenAI Credentials')} bordered={false}>
            <p style={{ color: '#888', marginBottom: '1.5rem' }}>
                {t('settings.credentials_note', 'Configure API credentials. Values saved here take precedence over .env file.')}
            </p>
            <Space direction="vertical" style={{ width: '100%' }} size="large">
                <div>
                    <label>
                        {t('settings.api_key', 'API Key')}
                        <CredentialSourceTag source={sources.openai_api_key || 'env'} />
                    </label>
                    <Input.Password
                        value={credentials.openai_api_key}
                        onChange={(e) => onCredentialChange('openai_api_key', e.target.value)}
                        placeholder="sk-..."
                        disabled={loading}
                    />
                </div>
                <div>
                    <label>{t('settings.base_url', 'Base URL')}</label>
                    <Input
                        value={credentials.openai_base_url}
                        onChange={(e) => onCredentialChange('openai_base_url', e.target.value)}
                        placeholder="https://api.openai.com/v1"
                        disabled={loading}
                    />
                </div>
                <CredentialActions
                    onSave={() => onSave('openai')}
                    onTest={() => onTest('openai')}
                    onReset={() => onReset('openai_api_key')}
                    loading={loading}
                    testing={testing === 'openai'}
                />
            </Space>
        </Card>
    );
}

export default OpenAISettingsSection;
