import { Card, Tabs } from 'antd';
import { useTranslation } from 'react-i18next';
import ExchangeCredentialForm from './ExchangeCredentialForm';
import { SUPPORTED_EXCHANGES } from '../../constants/settingsConstants';

/**
 * Exchange Credentials settings section with nested tabs for each exchange and mode
 */
export function ExchangeSettingsSection({
    credentials,
    loading,
    testing,
    onCCXTCredentialChange,
    onSave,
    onTest
}) {
    const { t } = useTranslation();

    const renderExchangeTabs = (exchange, hasPassphrase) => {
        const modes = [
            { key: 'paper', label: t('settings.paper_testnet', 'Paper (Testnet)') },
            { key: 'live', label: t('settings.live_production', 'Live (Production)') }
        ];

        return (
            <Tabs
                items={modes.map(mode => ({
                    key: mode.key,
                    label: mode.label,
                    children: (
                        <ExchangeCredentialForm
                            exchange={exchange}
                            mode={mode.key}
                            values={credentials.ccxt?.[exchange]?.[mode.key] || {}}
                            loading={loading}
                            testing={testing}
                            onChange={onCCXTCredentialChange}
                            onSave={onSave}
                            onTest={onTest}
                            showPassphrase={hasPassphrase}
                        />
                    )
                }))}
            />
        );
    };

    const exchangeTabItems = SUPPORTED_EXCHANGES.map(exchange => ({
        key: exchange.key,
        label: exchange.label,
        children: renderExchangeTabs(exchange.key, exchange.hasPassphrase)
    }));

    return (
        <Card title={t('settings.exchange_credentials', 'Exchange Credentials')} bordered={false}>
            <Tabs items={exchangeTabItems} />
        </Card>
    );
}

export default ExchangeSettingsSection;
