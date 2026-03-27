import { useState } from 'react'
import {
    Alert,
    Button,
    Card,
    Checkbox,
    Divider,
    Input,
    InputNumber,
    Space,
    Switch,
    Tabs,
    Typography
} from 'antd'

import SettingRow from './SettingRow'

const { Paragraph } = Typography

const BINANCE_LIVE_API_MANAGEMENT_URL = 'https://www.binance.com/en/my/settings/api-management'
const BINANCE_SPOT_TESTNET_URL = 'https://testnet.binance.vision/'
const BINANCE_API_SECURITY_GUIDE_URL = 'https://www.binance.com/en/academy/articles/what-are-api-keys-and-security-types'

function BinanceApiGuide({ t, mode }) {
    const isPaper = mode === 'paper'
    const title = isPaper
        ? t('onboarding.sections.paper_api_guide', 'Binance paper guide')
        : t('onboarding.sections.live_api_guide', 'Binance live guide')
    const intro = isPaper
        ? t('onboarding.guide.paper_intro', 'Use Binance Spot Test Network to generate sandbox credentials for paper mode, then keep the sandbox URL and credentials in the paper configuration below.')
        : t('onboarding.guide.live_intro', 'Create the key from Binance API Management, enable only the permissions you actually need, then lock it down with IP restrictions before pasting it back here.')
    const steps = isPaper
        ? [
            t('onboarding.guide.paper_step_1', 'Open Binance Spot Test Network and sign in with a supported account to access the sandbox environment.'),
            t('onboarding.guide.paper_step_2', 'Generate a sandbox API key and secret from the testnet page, then copy both values immediately.'),
            t('onboarding.guide.paper_step_3', 'Keep the sandbox URL set to https://testnet.binance.vision and use these credentials only for paper mode.'),
            t('onboarding.guide.paper_step_4', 'Do not reuse live exchange keys here. Paper mode should stay isolated from your real trading account.'),
            t('onboarding.guide.paper_step_5', 'Paste the sandbox key pair into the paper tab below and run the paper test against testnet.')
        ]
        : [
            t('onboarding.guide.live_step_1', 'Open Binance API Management and click Create API, then choose a system-generated key.'),
            t('onboarding.guide.live_step_2', 'Complete Binance security verification and copy the API Key and Secret Key immediately.'),
            t('onboarding.guide.live_step_3', 'Enable only the permissions you need. For this app, keep Enable Reading on; enable Spot & Margin Trading only if you plan to place live orders.'),
            t('onboarding.guide.live_step_4', 'In API restrictions, set Restrict access to trusted IPs only and add the server public IP that will run this platform.'),
            t('onboarding.guide.live_step_5', 'Use separate keys for separate environments when possible, then paste the key pair here and run the live test button.')
        ]
    const primaryHref = isPaper ? BINANCE_SPOT_TESTNET_URL : BINANCE_LIVE_API_MANAGEMENT_URL
    const primaryLabel = isPaper
        ? t('onboarding.actions.open_binance_testnet', 'Open Binance Spot Test Network')
        : t('onboarding.actions.create_binance_api', 'Create Binance API Key')
    const warningTitle = isPaper
        ? t('onboarding.guide.paper_warning_title', 'Paper mode checklist')
        : t('onboarding.guide.live_warning_title', 'Security checklist')
    const warningDescription = isPaper
        ? t('onboarding.guide.paper_warning', 'Sandbox credentials are for paper mode only. Keep live credentials out of the paper tab, and leave the sandbox URL pointed at Binance Spot Test Network.')
        : t('onboarding.guide.live_warning', 'Binance recommends enabling only required permissions, storing secrets outside source control, rotating keys regularly, and deleting or replacing a key immediately if it may have been exposed.')

    return (
        <Card size="small" className="onboarding-nested-card" title={title}>
            <Space direction="vertical" style={{ width: '100%' }} size="middle">
                <Paragraph style={{ marginBottom: 0 }}>{intro}</Paragraph>
                <Space wrap>
                    <Button type="primary" href={primaryHref} target="_blank" rel="noreferrer">
                        {primaryLabel}
                    </Button>
                    <Button href={BINANCE_API_SECURITY_GUIDE_URL} target="_blank" rel="noreferrer">
                        {t('onboarding.actions.open_binance_security_guide', 'Open Binance permissions guide')}
                    </Button>
                </Space>
                <ol className="onboarding-guide-list">
                    {steps.map((step) => <li key={step}>{step}</li>)}
                </ol>
                <Alert
                    type="warning"
                    showIcon
                    message={warningTitle}
                    description={warningDescription}
                />
            </Space>
        </Card>
    )
}

export default function TradingSetupSection({ config, updateConfig, testConnection, testing, t }) {
    const [activeTradingTab, setActiveTradingTab] = useState('paper')

    return (
        <Card className="onboarding-card">
            <Alert
                type="warning"
                showIcon
                message={t('onboarding.trading_note', 'The onboarding flow only supports Binance and lets you configure paper and live credentials together.')}
                style={{ marginBottom: 20 }}
            />
            <Divider>{t('onboarding.sections.trading_modes', 'Paper and live setup')}</Divider>
            <Tabs
                className="onboarding-mode-tabs"
                activeKey={activeTradingTab}
                onChange={setActiveTradingTab}
                items={[
                    {
                        key: 'paper',
                        label: t('onboarding.tabs.paper', 'Paper'),
                        children: (
                            <Space direction="vertical" style={{ width: '100%' }} size="middle">
                                <BinanceApiGuide t={t} mode="paper" />
                                <Card size="small" className="onboarding-nested-card" title={t('onboarding.sections.paper_config', 'Paper configuration')}>
                                    <Space direction="vertical" style={{ width: '100%' }}>
                                        <SettingRow label={t('onboarding.fields.paper_enabled', 'Paper mode enabled')}>
                                            <Switch checked={config.trading.binance.paper_enabled} onChange={(checked) => updateConfig(['trading', 'binance', 'paper_enabled'], checked)} />
                                        </SettingRow>
                                        <SettingRow label={t('onboarding.fields.paper_balance', 'Paper balance (USDT)')}>
                                            <InputNumber style={{ width: '100%' }} value={config.trading.binance.initial_balance_usdt} onChange={(value) => updateConfig(['trading', 'binance', 'initial_balance_usdt'], value ?? 10000)} />
                                        </SettingRow>
                                        <SettingRow label={t('onboarding.fields.sandbox_url', 'Sandbox URL')}>
                                            <Input value={config.trading.binance.sandbox_url} onChange={(event) => updateConfig(['trading', 'binance', 'sandbox_url'], event.target.value)} />
                                        </SettingRow>
                                    </Space>
                                </Card>
                                <Card size="small" className="onboarding-nested-card" title={t('onboarding.sections.paper_credentials', 'Binance paper')}>
                                    <Space direction="vertical" style={{ width: '100%' }}>
                                        <SettingRow label={t('onboarding.fields.api_key', 'API key')}>
                                            <Input.Password value={config.trading.credentials.paper.api_key} onChange={(event) => updateConfig(['trading', 'credentials', 'paper', 'api_key'], event.target.value)} />
                                        </SettingRow>
                                        <SettingRow label={t('onboarding.fields.secret', 'Secret')}>
                                            <Input.Password value={config.trading.credentials.paper.secret} onChange={(event) => updateConfig(['trading', 'credentials', 'paper', 'secret'], event.target.value)} />
                                        </SettingRow>
                                        <Button
                                            onClick={() => testConnection('ccxt', {
                                                exchange: 'binance',
                                                mode: 'paper',
                                                api_key: config.trading.credentials.paper.api_key,
                                                secret: config.trading.credentials.paper.secret,
                                                use_testnet: true
                                            }, 'ccxt:paper')}
                                            loading={testing === 'ccxt:paper'}
                                        >
                                            {t('onboarding.actions.test_paper', 'Test paper')}
                                        </Button>
                                    </Space>
                                </Card>
                            </Space>
                        )
                    },
                    {
                        key: 'live',
                        label: t('onboarding.tabs.live', 'Live'),
                        children: (
                            <Space direction="vertical" style={{ width: '100%' }} size="middle">
                                <BinanceApiGuide t={t} mode="live" />
                                <Card size="small" className="onboarding-nested-card" title={t('onboarding.sections.live_config', 'Live configuration')}>
                                    <SettingRow
                                        label={t('onboarding.fields.enable_trading', 'Enable live trading entry')}
                                        hint={t('onboarding.hints.enable_trading', 'Prefer paper mode first. Live mode requires explicit acknowledgement and full credentials.')}
                                    >
                                        <Switch
                                            checked={config.trading.live_trading_enabled}
                                            onChange={(checked) => updateConfig(['trading', 'live_trading_enabled'], checked)}
                                        />
                                    </SettingRow>
                                    {config.trading.live_trading_enabled ? (
                                        <Checkbox checked={config.trading.live_risk_acknowledged} onChange={(event) => updateConfig(['trading', 'live_risk_acknowledged'], event.target.checked)}>
                                            {t('onboarding.live_ack', 'I understand live trading can place real orders and accept that risk.')}
                                        </Checkbox>
                                    ) : null}
                                </Card>
                                <Card size="small" className="onboarding-nested-card" title={t('onboarding.sections.live_credentials', 'Binance live')}>
                                    <Space direction="vertical" style={{ width: '100%' }}>
                                        <SettingRow label={t('onboarding.fields.api_key', 'API key')}>
                                            <Input.Password value={config.trading.credentials.live.api_key} onChange={(event) => updateConfig(['trading', 'credentials', 'live', 'api_key'], event.target.value)} />
                                        </SettingRow>
                                        <SettingRow label={t('onboarding.fields.secret', 'Secret')}>
                                            <Input.Password value={config.trading.credentials.live.secret} onChange={(event) => updateConfig(['trading', 'credentials', 'live', 'secret'], event.target.value)} />
                                        </SettingRow>
                                        <Button
                                            onClick={() => testConnection('ccxt', {
                                                exchange: 'binance',
                                                mode: 'live',
                                                api_key: config.trading.credentials.live.api_key,
                                                secret: config.trading.credentials.live.secret,
                                                use_testnet: false
                                            }, 'ccxt:live')}
                                            loading={testing === 'ccxt:live'}
                                        >
                                            {t('onboarding.actions.test_live', 'Test live')}
                                        </Button>
                                    </Space>
                                </Card>
                            </Space>
                        )
                    }
                ]}
            />
        </Card>
    )
}
