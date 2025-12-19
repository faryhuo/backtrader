import { Button, Space } from 'antd';
import { SaveOutlined, CheckCircleOutlined, ReloadOutlined } from '@ant-design/icons';
import { useTranslation } from 'react-i18next';

/**
 * Reusable action buttons for credential sections
 */
export function CredentialActions({
    onSave,
    onTest,
    onReset,
    loading = false,
    testing = false,
    showTest = true,
    showReset = true
}) {
    const { t } = useTranslation();

    return (
        <Space>
            <Button
                type="primary"
                icon={<SaveOutlined />}
                onClick={onSave}
                loading={loading}
            >
                {t('settings.save', 'Save')}
            </Button>
            {showTest && onTest && (
                <Button
                    icon={<CheckCircleOutlined />}
                    onClick={onTest}
                    loading={testing}
                >
                    {t('settings.test', 'Test')}
                </Button>
            )}
            {showReset && onReset && (
                <Button
                    icon={<ReloadOutlined />}
                    onClick={onReset}
                    loading={loading}
                >
                    {t('settings.reset_env', 'Reset to .env')}
                </Button>
            )}
        </Space>
    );
}

export default CredentialActions;
