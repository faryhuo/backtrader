import { useTranslation } from 'react-i18next';
import { Card, Input, Space, Button, Tag, Divider } from 'antd';
import { SaveOutlined, UndoOutlined, CheckCircleOutlined } from '@ant-design/icons';

/**
 * Renders a tag showing the source of a config value
 */
function SourceTag({ source }) {
    const colors = {
        database: 'green',
        env: 'blue',
        default: 'gray'
    };
    const labels = {
        database: 'Database',
        env: '.env',
        default: 'Default'
    };
    return (
        <Tag color={colors[source] || 'gray'} style={{ marginLeft: 8 }}>
            {labels[source] || source}
        </Tag>
    );
}

/**
 * Site Configuration settings section
 */
export function SiteSettingsSection({
    config,
    sources,
    loading,
    saved,
    onChange,
    onSave,
    onReset
}) {
    const { t } = useTranslation();

    const renderField = (field, label, placeholder = '') => (
        <div>
            <label>
                {label}
                {sources[field] && <SourceTag source={sources[field]} />}
            </label>
            <Input
                value={config[field] || ''}
                onChange={(e) => onChange(field, e.target.value)}
                placeholder={placeholder}
                disabled={loading}
            />
        </div>
    );

    return (
        <Card title={t('settings.site_configuration', 'Site Configuration')} bordered={false}>
            <p style={{ color: '#888', marginBottom: '1.5rem' }}>
                {t('settings.site_config_note', 'Configure landing page content. Values saved here take precedence over .env file.')}
            </p>

            <Space direction="vertical" style={{ width: '100%' }} size="large">
                {/* Branding */}
                <div>
                    <h4 style={{ marginBottom: '1rem' }}>{t('settings.branding', 'Branding')}</h4>
                    {renderField('site_title', t('settings.site_title', 'Site Title'), 'Backtrader Pro')}
                    <div style={{ marginTop: '1rem' }}>
                        {renderField('site_description', t('settings.site_description', 'Description'), 'Professional quantitative trading platform')}
                    </div>
                </div>

                <Divider />

                {/* Links */}
                <div>
                    <h4 style={{ marginBottom: '1rem' }}>{t('settings.external_links', 'External Links')}</h4>
                    {renderField('site_docs_url', t('settings.docs_url', 'Documentation URL'), 'https://docs.example.com')}
                    <div style={{ marginTop: '1rem' }}>
                        {renderField('site_github_url', t('settings.github_url', 'GitHub URL'), 'https://github.com/example/repo')}
                    </div>
                    <div style={{ marginTop: '1rem' }}>
                        {renderField('site_twitter_url', t('settings.twitter_url', 'Twitter URL'), 'https://twitter.com/example')}
                    </div>
                    <div style={{ marginTop: '1rem' }}>
                        {renderField('site_email', t('settings.contact_email', 'Contact Email'), 'contact@example.com')}
                    </div>
                </div>

                <Divider />

                {/* Stats */}
                <div>
                    <h4 style={{ marginBottom: '1rem' }}>{t('settings.stats_display', 'Stats Display')}</h4>
                    {renderField('site_stats_strategies', t('settings.stats_strategies', 'Strategies Count'), '50+')}
                    <div style={{ marginTop: '1rem' }}>
                        {renderField('site_stats_backtests', t('settings.stats_backtests', 'Backtests Count'), '10K+')}
                    </div>
                    <div style={{ marginTop: '1rem' }}>
                        {renderField('site_stats_users', t('settings.stats_users', 'Users Count'), '1K+')}
                    </div>
                </div>

                <Divider />

                {/* Actions */}
                <div style={{ display: 'flex', gap: '1rem', alignItems: 'center' }}>
                    {saved && (
                        <span style={{ color: '#52c41a' }}>
                            <CheckCircleOutlined style={{ marginRight: 4 }} />
                            {t('settings.saved', 'Settings saved!')}
                        </span>
                    )}
                    <Button icon={<UndoOutlined />} onClick={onReset} disabled={loading}>
                        {t('settings.reset', 'Reset Defaults')}
                    </Button>
                    <Button type="primary" icon={<SaveOutlined />} onClick={onSave} loading={loading}>
                        {t('settings.save', 'Save Changes')}
                    </Button>
                </div>
            </Space>
        </Card>
    );
}
