import {
    Alert,
    Button,
    Card,
    Col,
    Descriptions,
    Divider,
    Input,
    InputNumber,
    Row,
    Select,
    Space,
    Spin,
    Statistic,
    Switch,
    Tag,
    Typography,
    message,
} from 'antd';
import {
    ApiOutlined,
    DashboardOutlined,
    FundProjectionScreenOutlined,
    ReloadOutlined,
    SafetyCertificateOutlined,
} from '@ant-design/icons';
import { useEffect, useMemo, useState } from 'react';
import { useTranslation } from 'react-i18next';
import { usePersistedState } from '../../hooks/usePersistedState';
import { api } from '../../services/api';
import { basisApi } from '../../services/basisApi';

const { Paragraph, Text } = Typography;
const BASIS_TRADING_CACHE_KEY = 'basisArbitrage.tradingState';

function formatMoney(value, digits = 2) {
    return `$${Number(value || 0).toLocaleString(undefined, {
        minimumFractionDigits: digits,
        maximumFractionDigits: digits,
    })}`;
}

function formatPercent(value, digits = 2) {
    return `${(Number(value || 0) * 100).toFixed(digits)}%`;
}

function createEmptyCredentialState() {
    return {
        okx: {
            paper: { api_key: '', secret: '', passphrase: '' },
            live: { api_key: '', secret: '', passphrase: '' },
        },
        binance: {
            paper: { api_key: '', secret: '', passphrase: '' },
            live: { api_key: '', secret: '', passphrase: '' },
        },
    };
}

export default function BasisTradingPanel({
    symbol = 'ETH',
    calculator,
    effectiveFundingRate = 0,
    basisPositive = false,
    refreshNonce = 0,
}) {
    const { t } = useTranslation();
    const [cachedTradingState, setCachedTradingState] = usePersistedState(BASIS_TRADING_CACHE_KEY, {
        exchange: 'okx',
        mode: 'paper',
        leverage: 1,
        confirmLive: false,
        lastExecution: null,
    });
    const [exchange, setExchange] = useState(cachedTradingState.exchange || 'okx');
    const [mode, setMode] = useState(cachedTradingState.mode || 'paper');
    const [leverage, setLeverage] = useState(cachedTradingState.leverage ?? 1);
    const [confirmLive, setConfirmLive] = useState(cachedTradingState.confirmLive ?? false);
    const [credentialLoading, setCredentialLoading] = useState(false);
    const [testingKey, setTestingKey] = useState('');
    const [statusLoading, setStatusLoading] = useState(false);
    const [tradeLoading, setTradeLoading] = useState(false);
    const [credentials, setCredentials] = useState(createEmptyCredentialState());
    const [credentialStatus, setCredentialStatus] = useState(null);
    const [tradeState, setTradeState] = useState(null);
    const [lastExecution, setLastExecution] = useState(cachedTradingState.lastExecution ?? null);
    const [precheckLoading, setPrecheckLoading] = useState(false);
    const [precheck, setPrecheck] = useState(null);

    const selectedCredentials = credentials?.[exchange]?.[mode] || {};
    const requiresPassphrase = credentialStatus?.requires_passphrase;
    const canOpenTrade = Number(calculator?.quantity || 0) > 0 && (mode === 'paper' || credentialStatus?.[mode]?.configured);
    const previewCards = useMemo(() => ([
        {
            key: 'daily',
            title: t('basis.trading.panel_daily'),
            value: formatMoney(calculator?.incomePerDay),
            prefix: <FundProjectionScreenOutlined />,
        },
        {
            key: 'monthlyVolume',
            title: t('basis.trading.panel_monthly_volume'),
            value: formatMoney(calculator?.monthlyVolume),
            prefix: <DashboardOutlined />,
        },
        {
            key: 'signal',
            title: t('basis.trading.panel_signal'),
            value: basisPositive ? t('basis.trading.signal_ready') : t('basis.trading.signal_wait'),
            prefix: <SafetyCertificateOutlined />,
        },
    ]), [basisPositive, calculator?.incomePerDay, calculator?.monthlyVolume, t]);

    const loadCredentialState = async () => {
        try {
            setCredentialLoading(true);
            const response = await api.getCredentials();
            const ccxt = response?.credentials?.ccxt || {};
            setCredentials({
                okx: {
                    paper: {
                        api_key: ccxt?.okx?.paper?.api_key || '',
                        secret: ccxt?.okx?.paper?.secret || '',
                        passphrase: ccxt?.okx?.paper?.passphrase || '',
                    },
                    live: {
                        api_key: ccxt?.okx?.live?.api_key || '',
                        secret: ccxt?.okx?.live?.secret || '',
                        passphrase: ccxt?.okx?.live?.passphrase || '',
                    },
                },
                binance: {
                    paper: {
                        api_key: ccxt?.binance?.paper?.api_key || '',
                        secret: ccxt?.binance?.paper?.secret || '',
                        passphrase: '',
                    },
                    live: {
                        api_key: ccxt?.binance?.live?.api_key || '',
                        secret: ccxt?.binance?.live?.secret || '',
                        passphrase: '',
                    },
                },
            });
        } catch (error) {
            message.error(error.message || t('basis.trading.credentials_load_failed'));
        } finally {
            setCredentialLoading(false);
        }
    };

    const loadExchangeStatus = async () => {
        try {
            setStatusLoading(true);
            const [nextStatus, nextTradeState] = await Promise.all([
                basisApi.getCredentialStatus(exchange),
                basisApi.getTradeState(exchange, mode, `${symbol}/USDT`),
            ]);
            setCredentialStatus(nextStatus);
            setTradeState(nextTradeState);
        } catch (error) {
            message.error(error.message || t('basis.trading.status_load_failed'));
        } finally {
            setStatusLoading(false);
        }
    };

    useEffect(() => {
        loadCredentialState();
    }, []);

    useEffect(() => {
        loadExchangeStatus();
    }, [exchange, mode, refreshNonce, symbol]);

    useEffect(() => {
        setCachedTradingState({
            exchange,
            mode,
            leverage,
            confirmLive,
            lastExecution,
        });
    }, [confirmLive, exchange, lastExecution, leverage, mode, setCachedTradingState]);

    const handleCredentialChange = (field, value) => {
        setCredentials((prev) => ({
            ...prev,
            [exchange]: {
                ...prev[exchange],
                [mode]: {
                    ...prev[exchange][mode],
                    [field]: value,
                },
            },
        }));
    };

    const handleSaveCredentials = async () => {
        try {
            setCredentialLoading(true);
            await api.updateCCXTCredentials(exchange, mode, selectedCredentials);
            message.success(t('basis.trading.credentials_saved'));
            await loadExchangeStatus();
        } catch (error) {
            message.error(error.message || t('basis.trading.credentials_save_failed'));
        } finally {
            setCredentialLoading(false);
        }
    };

    const handleTestCredentials = async () => {
        try {
            setTestingKey(`${exchange}-${mode}`);
            const response = await api.testCredential('ccxt', {
                exchange,
                mode,
                api_key: selectedCredentials.api_key,
                secret: selectedCredentials.secret,
                passphrase: selectedCredentials.passphrase,
                use_testnet: mode === 'paper',
            });
            if (response?.valid) {
                message.success(response.message || t('basis.trading.connection_test_ok'));
            } else {
                message.error(response?.message || t('basis.trading.connection_test_failed'));
            }
        } catch (error) {
            message.error(error.message || t('basis.trading.connection_test_failed'));
        } finally {
            setTestingKey('');
        }
    };

    const tradePayload = {
        exchange,
        mode,
        symbol: `${symbol}/USDT`,
        capital: Number((calculator?.spotCapital || 0) + (calculator?.marginCapital || 0)),
        spot_ratio: calculator && calculator.spotCapital + calculator.marginCapital > 0
            ? (Number(calculator.spotCapital || 0) / Number((calculator.spotCapital || 0) + (calculator.marginCapital || 0))) * 100
            : 50,
        leverage,
        funding_rate: effectiveFundingRate,
        confirm_live: confirmLive,
    };

    const precheckPayload = {
        exchange,
        mode,
        symbol: `${symbol}/USDT`,
        capital: Number((calculator?.spotCapital || 0) + (calculator?.marginCapital || 0)),
        spot_ratio: calculator && calculator.spotCapital + calculator.marginCapital > 0
            ? (Number(calculator.spotCapital || 0) / Number((calculator.spotCapital || 0) + (calculator.marginCapital || 0))) * 100
            : 50,
        leverage,
        funding_rate: effectiveFundingRate,
        entry_price: calculator?.quantity > 0 ? Number(calculator.perpNotional || 0) / Number(calculator.quantity || 1) : undefined,
        cycles_per_month: 4,
        round_trip_fees: 12,
    };

    const handlePrecheck = async () => {
        try {
            setPrecheckLoading(true);
            const response = await basisApi.getTradePrecheck(precheckPayload);
            setPrecheck(response);
            message.success(t('basis.trading.precheck_loaded'));
        } catch (error) {
            message.error(error.message || t('basis.trading.precheck_failed'));
        } finally {
            setPrecheckLoading(false);
        }
    };

    const handleOpenTrade = async () => {
        try {
            setTradeLoading(true);
            const response = await basisApi.openTrade(tradePayload);
            setLastExecution(response);
            message.success(t('basis.trading.open_success'));
            await loadExchangeStatus();
            await handlePrecheck();
        } catch (error) {
            message.error(error.message || t('basis.trading.open_failed'));
        } finally {
            setTradeLoading(false);
        }
    };

    const handleCloseTrade = async () => {
        try {
            setTradeLoading(true);
            const response = await basisApi.closeTrade({
                exchange,
                mode,
                symbol: `${symbol}/USDT`,
                quantity: tradeState?.trade?.perp_base_quantity || tradeState?.trade?.spot_quantity || calculator?.quantity || null,
                spot_quantity: tradeState?.trade?.spot_quantity || calculator?.quantity || null,
                perp_quantity: tradeState?.trade?.perp_base_quantity || tradeState?.trade?.spot_quantity || calculator?.quantity || null,
                confirm_live: confirmLive,
            });
            setLastExecution(response);
            message.success(t('basis.trading.close_success'));
            await loadExchangeStatus();
            await handlePrecheck();
        } catch (error) {
            message.error(error.message || t('basis.trading.close_failed'));
        } finally {
            setTradeLoading(false);
        }
    };

    return (
        <Card
            className="basis-panel"
            title={t('basis.trading.title')}
            extra={<Tag color="processing">{t('basis.trading.standalone')}</Tag>}
            bordered={false}
        >
            <Paragraph className="basis-panel-lead">
                {t('basis.trading.summary', {
                    symbol,
                    rate: formatPercent(effectiveFundingRate, 3),
                })}
            </Paragraph>

            <Row gutter={[12, 12]} className="basis-live-stats">
                {previewCards.map((item) => (
                    <Col xs={24} md={8} key={item.key}>
                        <Card className="basis-nested-card" bordered={false}>
                            <Statistic title={item.title} value={item.value} prefix={item.prefix} />
                        </Card>
                    </Col>
                ))}
            </Row>

            <Row gutter={[16, 16]}>
                <Col xs={24} xl={10}>
                    <Card className="basis-mode-card" bordered={false}>
                        <div className="basis-toolbar" style={{ marginBottom: 12 }}>
                            <div className="basis-toolbar-group">
                                <Text className="basis-mini-label">{t('basis.trading.exchange')}</Text>
                                <Select
                                    value={exchange}
                                    onChange={setExchange}
                                    options={[
                                        { value: 'okx', label: 'OKX' },
                                        { value: 'binance', label: 'Binance' },
                                    ]}
                                />
                            </div>
                            <div className="basis-toolbar-group">
                                <Text className="basis-mini-label">{t('basis.trading.mode')}</Text>
                                <Select
                                    value={mode}
                                    onChange={setMode}
                                    options={[
                                        { value: 'paper', label: t('basis.trading.paper_mode') },
                                        { value: 'live', label: t('basis.trading.live_mode') },
                                    ]}
                                />
                            </div>
                        </div>

                        <div className="basis-toolbar" style={{ marginBottom: 12 }}>
                            <div className="basis-toolbar-group">
                                <Text className="basis-mini-label">{t('basis.trading.leverage')}</Text>
                                <InputNumber min={1} max={3} value={leverage} onChange={(value) => setLeverage(Number(value || 1))} className="basis-input" />
                            </div>
                            <div className="basis-toolbar-group">
                                <Text className="basis-mini-label">{t('basis.trading.hedge_qty')}</Text>
                                <Input value={`${Number(calculator?.quantity || 0).toFixed(4)} ${symbol}`} readOnly />
                            </div>
                        </div>

                        <Space direction="vertical" size="small" style={{ width: '100%' }}>
                            <Text className="basis-mini-label">{t('basis.trading.api_key')}</Text>
                            <Input value={selectedCredentials.api_key} onChange={(event) => handleCredentialChange('api_key', event.target.value)} />
                            <Text className="basis-mini-label">{t('basis.trading.secret')}</Text>
                            <Input.Password value={selectedCredentials.secret} onChange={(event) => handleCredentialChange('secret', event.target.value)} />
                            {requiresPassphrase ? (
                                <>
                                    <Text className="basis-mini-label">{t('basis.trading.passphrase')}</Text>
                                    <Input.Password value={selectedCredentials.passphrase} onChange={(event) => handleCredentialChange('passphrase', event.target.value)} />
                                </>
                            ) : null}
                        </Space>

                        <Space style={{ marginTop: 16 }} wrap>
                            <Button onClick={handleSaveCredentials} loading={credentialLoading}>
                                {t('basis.trading.save_credentials')}
                            </Button>
                            <Button onClick={handleTestCredentials} loading={testingKey === `${exchange}-${mode}`}>
                                {t('basis.trading.test_connection')}
                            </Button>
                            <Button onClick={handlePrecheck} loading={precheckLoading}>
                                {t('basis.trading.precheck')}
                            </Button>
                            <Button icon={<ReloadOutlined />} onClick={loadExchangeStatus} loading={statusLoading}>
                                {t('basis.trading.refresh')}
                            </Button>
                        </Space>

                        <Divider />

                        <Space wrap size={[8, 8]}>
                            <Tag color={credentialStatus?.[mode]?.configured ? 'green' : 'default'}>
                                {credentialStatus?.[mode]?.configured
                                    ? t('basis.trading.credentials_ready')
                                    : t('basis.trading.credentials_missing')}
                            </Tag>
                            <Tag color={basisPositive ? 'green' : 'orange'}>
                                {basisPositive ? t('basis.trading.basis_ready') : t('basis.trading.basis_not_ready')}
                            </Tag>
                        </Space>

                        {mode === 'live' ? (
                            <div className="basis-live-confirm">
                                <Text>{t('basis.trading.live_confirm')}</Text>
                                <Switch checked={confirmLive} onChange={setConfirmLive} />
                            </div>
                        ) : null}

                        <Space style={{ marginTop: 16 }} wrap>
                            <Button type="primary" onClick={handleOpenTrade} loading={tradeLoading} disabled={!canOpenTrade || (mode === 'live' && !confirmLive)}>
                                {t('basis.trading.open_hedge')}
                            </Button>
                            <Button danger onClick={handleCloseTrade} loading={tradeLoading} disabled={mode === 'live' && !confirmLive}>
                                {t('basis.trading.close_hedge')}
                            </Button>
                        </Space>
                    </Card>
                </Col>

                <Col xs={24} xl={14}>
                    <Spin spinning={statusLoading} indicator={<ReloadOutlined spin />}>
                        <Card className="basis-mode-card" bordered={false}>
                            <Text strong>{t('basis.trading.state_title')}</Text>
                            <Descriptions column={1} size="small" className="basis-monitor-descriptions" style={{ marginTop: 12 }}>
                                <Descriptions.Item label={t('basis.trading.state_status')}>
                                    {tradeState?.status || tradeState?.trade?.status || 'idle'}
                                </Descriptions.Item>
                                <Descriptions.Item label={t('basis.trading.state_symbol')}>
                                    {tradeState?.symbol || `${symbol}/USDT`}
                                </Descriptions.Item>
                                <Descriptions.Item label={t('basis.trading.state_spot')}>
                                    {tradeState?.snapshot?.spot_price ? formatMoney(tradeState.snapshot.spot_price) : '--'}
                                </Descriptions.Item>
                                <Descriptions.Item label={t('basis.trading.state_perp')}>
                                    {tradeState?.snapshot?.perp_price ? formatMoney(tradeState.snapshot.perp_price) : '--'}
                                </Descriptions.Item>
                                <Descriptions.Item label={t('basis.trading.state_unrealized')}>
                                    {tradeState?.unrealized_pnl !== undefined ? formatMoney(tradeState.unrealized_pnl) : '--'}
                                </Descriptions.Item>
                                <Descriptions.Item label={t('basis.trading.state_qty')}>
                                    {tradeState?.trade?.spot_quantity || tradeState?.trade?.perp_base_quantity || tradeState?.trade?.perp_contracts
                                        ? `${Number(tradeState.trade?.spot_quantity || 0).toFixed(4)} ${symbol} / ${Number(tradeState.trade?.perp_base_quantity || tradeState.trade?.perp_contracts || 0).toFixed(4)} ${symbol}`
                                        : '--'}
                                </Descriptions.Item>
                            </Descriptions>

                            <Divider />

                            {lastExecution ? (
                                <Alert
                                    type="success"
                                    showIcon
                                    message={t('basis.trading.last_execution')}
                                    description={`${lastExecution.exchange?.toUpperCase()} / ${lastExecution.mode?.toUpperCase()} / ${lastExecution.action?.toUpperCase()}`}
                                />
                            ) : (
                                <Alert
                                    type="info"
                                    showIcon
                                    message={t('basis.trading.no_execution')}
                                    description={t('basis.trading.no_execution_desc')}
                                />
                            )}

                            {mode === 'live' ? (
                                <Alert
                                    style={{ marginTop: 16 }}
                                    type="warning"
                                    showIcon
                                    icon={<ApiOutlined />}
                                    message={t('basis.trading.live_warning_title')}
                                    description={t('basis.trading.live_warning_body')}
                                />
                            ) : null}

                            {precheck ? (
                                <>
                                    <Divider />
                                    <Text strong>{t('basis.trading.precheck_title')}</Text>
                                    <Descriptions column={1} size="small" className="basis-monitor-descriptions" style={{ marginTop: 12 }}>
                                        <Descriptions.Item label={t('basis.trading.precheck_spot_capital')}>
                                            {formatMoney(precheck?.plan?.spot_capital)}
                                        </Descriptions.Item>
                                        <Descriptions.Item label={t('basis.trading.precheck_margin_capital')}>
                                            {formatMoney(precheck?.plan?.margin_capital)}
                                        </Descriptions.Item>
                                        <Descriptions.Item label={t('basis.trading.precheck_qty')}>
                                            {precheck?.plan?.quantity ? `${Number(precheck.plan.quantity).toFixed(4)} ${symbol}` : '--'}
                                        </Descriptions.Item>
                                        <Descriptions.Item label={t('basis.trading.precheck_spot_free')}>
                                            {formatMoney(precheck?.balances?.spot_usdt?.free)}
                                        </Descriptions.Item>
                                        <Descriptions.Item label={t('basis.trading.precheck_swap_free')}>
                                            {formatMoney(precheck?.balances?.swap_usdt?.free)}
                                        </Descriptions.Item>
                                        <Descriptions.Item label={t('basis.trading.precheck_spot_submit')}>
                                            {precheck?.submit_preview?.spot_order
                                                ? `${precheck.submit_preview.spot_order.symbol} / ${precheck.submit_preview.spot_order.side} / ${precheck.submit_preview.spot_order.type} / ${precheck.submit_preview.spot_order.amount}`
                                                : '--'}
                                        </Descriptions.Item>
                                        <Descriptions.Item label={t('basis.trading.precheck_swap_submit')}>
                                            {precheck?.submit_preview?.perp_order
                                                ? `${precheck.submit_preview.perp_order.symbol} / ${precheck.submit_preview.perp_order.side} / ${precheck.submit_preview.perp_order.type} / ${precheck.submit_preview.perp_order.amount}`
                                                : '--'}
                                        </Descriptions.Item>
                                        <Descriptions.Item label={t('basis.trading.precheck_account_mode')}>
                                            {precheck?.account_config
                                                ? `${precheck.account_config.acctLv || '--'} / ${precheck.account_config.posMode || '--'}`
                                                : '--'}
                                        </Descriptions.Item>
                                    </Descriptions>
                                </>
                            ) : null}
                        </Card>
                    </Spin>
                </Col>
            </Row>
        </Card>
    );
}
