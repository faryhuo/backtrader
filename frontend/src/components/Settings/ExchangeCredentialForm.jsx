import { Space, Input } from 'antd';
import { useTranslation } from 'react-i18next';
import CredentialActions from './CredentialActions';

/**
 * Reusable form component for exchange credentials (API Key, Secret, optional Passphrase)
 */
export function ExchangeCredentialForm({
    exchange,
    mode,
    values = {},
    loading,
    testing,
    onChange,
    onSave,
    onTest,
    showPassphrase = false
}) {
    const { t } = useTranslation();
    const credentialType = `ccxt-${exchange}-${mode}`;

    return (
        <Space direction="vertical" style={{ width: '100%' }} size="large">
            <div>
                <label>{t('settings.api_key', 'API Key')}</label>
                <Input.Password
                    value={values.api_key || ''}
                    onChange={(e) => onChange(exchange, mode, 'api_key', e.target.value)}
                    placeholder="API Key"
                    disabled={loading}
                />
            </div>
            <div>
                <label>{t('settings.secret', 'Secret')}</label>
                <Input.Password
                    value={values.secret || ''}
                    onChange={(e) => onChange(exchange, mode, 'secret', e.target.value)}
                    placeholder="Secret"
                    disabled={loading}
                />
            </div>
            {showPassphrase && (
                <div>
                    <label>{t('settings.passphrase', 'Passphrase')}</label>
                    <Input.Password
                        value={values.passphrase || ''}
                        onChange={(e) => onChange(exchange, mode, 'passphrase', e.target.value)}
                        placeholder="Passphrase"
                        disabled={loading}
                    />
                </div>
            )}
            <CredentialActions
                onSave={() => onSave(credentialType)}
                onTest={() => onTest(credentialType)}
                loading={loading}
                testing={testing === credentialType}
                showReset={false}
            />
        </Space>
    );
}

export default ExchangeCredentialForm;
