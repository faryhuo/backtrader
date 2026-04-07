import {
    Alert,
    Card,
    Col,
    Descriptions,
    Divider,
    Empty,
    InputNumber,
    Layout,
    Select,
    Segmented,
    Spin,
    Progress,
    Row,
    Space,
    Statistic,
    Switch,
    Table,
    Tag,
    Timeline,
    Typography,
} from 'antd';
import {
    AlertOutlined,
    CheckCircleOutlined,
    ClockCircleOutlined,
    DollarCircleOutlined,
    FundOutlined,
    LineChartOutlined,
    ReloadOutlined,
    SafetyCertificateOutlined,
    SwapOutlined,
} from '@ant-design/icons';
import { useEffect, useMemo, useState } from 'react';
import { useTranslation } from 'react-i18next';
import { basisApi } from '../services/basisApi';
import './BasisArbitrage.css';

const { Content } = Layout;
const { Title, Paragraph, Text } = Typography;

const fundingThresholds = [
    { key: 'standard', rate: '> 0.01% / 8h', judgmentKey: 'basis.thresholds.standard.judgment', noteKey: 'basis.thresholds.standard.note', color: 'cyan' },
    { key: 'premium', rate: '> 0.03% / 8h', judgmentKey: 'basis.thresholds.premium.judgment', noteKey: 'basis.thresholds.premium.note', color: 'gold' },
    { key: 'weak', rate: '< 0.005% / 8h', judgmentKey: 'basis.thresholds.weak.judgment', noteKey: 'basis.thresholds.weak.note', color: 'default' },
    { key: 'negative', rate: '< 0', judgmentKey: 'basis.thresholds.negative.judgment', noteKey: 'basis.thresholds.negative.note', color: 'red' },
];

const capitalSplit = [
    { key: 'spot_open', legKey: 'basis.volume.spot_open.leg', actionKey: 'basis.volume.spot_open.action', notional: '$5,000' },
    { key: 'spot_close', legKey: 'basis.volume.spot_close.leg', actionKey: 'basis.volume.spot_close.action', notional: '$5,000' },
    { key: 'perp_open', legKey: 'basis.volume.perp_open.leg', actionKey: 'basis.volume.perp_open.action', notional: '$5,000' },
    { key: 'perp_close', legKey: 'basis.volume.perp_close.leg', actionKey: 'basis.volume.perp_close.action', notional: '$5,000' },
];

const MONITOR_SYMBOLS = ['ETH', 'BTC', 'SOL'];

function formatPercent(value, digits = 4) {
    return `${(Number(value || 0) * 100).toFixed(digits)}%`;
}

function formatMoney(value, digits = 2) {
    return `$${Number(value || 0).toLocaleString(undefined, {
        minimumFractionDigits: digits,
        maximumFractionDigits: digits,
    })}`;
}

function getFundingTone(rate) {
    if (rate >= 0.0003) return 'gold';
    if (rate >= 0.0001) return 'cyan';
    if (rate >= 0.00005) return 'blue';
    if (rate >= 0) return 'default';
    return 'red';
}

function getFundingDecision(rate) {
    if (rate >= 0.0003) return 'premium';
    if (rate >= 0.0001) return 'standard';
    if (rate >= 0) return 'weak';
    return 'negative';
}

export default function BasisArbitrage() {
    const { t } = useTranslation();
    const [symbol, setSymbol] = useState('ETH');
    const [autoRefresh, setAutoRefresh] = useState(true);
    const [refreshSeconds, setRefreshSeconds] = useState(30);
    const [snapshot, setSnapshot] = useState(null);
    const [monitorLoading, setMonitorLoading] = useState(true);
    const [monitorError, setMonitorError] = useState('');
    const [capital, setCapital] = useState(10000);
    const [spotRatio, setSpotRatio] = useState(50);
    const [manualFundingRate, setManualFundingRate] = useState(null);
    const [entryPrice, setEntryPrice] = useState(2000);
    const [cyclesPerMonth, setCyclesPerMonth] = useState(4);
    const [roundTripFees, setRoundTripFees] = useState(12);

    const fundingColumns = [
        { title: t('basis.table.rate'), dataIndex: 'rate', key: 'rate', width: 180 },
        {
            title: t('basis.table.judgment'),
            dataIndex: 'judgmentKey',
            key: 'judgment',
            render: (_, record) => <Tag color={record.color}>{t(record.judgmentKey)}</Tag>,
        },
        {
            title: t('basis.table.note'),
            dataIndex: 'noteKey',
            key: 'note',
            render: (noteKey) => t(noteKey),
        },
    ];

    const volumeColumns = [
        { title: t('basis.volume.table_leg'), dataIndex: 'legKey', key: 'leg', render: (legKey) => t(legKey) },
        { title: t('basis.volume.table_action'), dataIndex: 'actionKey', key: 'action', render: (actionKey) => t(actionKey) },
        { title: t('basis.volume.table_notional'), dataIndex: 'notional', key: 'notional' },
    ];

    useEffect(() => {
        if (snapshot?.spotPrice > 0) {
            setEntryPrice(Number(snapshot.spotPrice.toFixed(2)));
        }
    }, [snapshot?.spotPrice]);

    useEffect(() => {
        let cancelled = false;

        async function loadSnapshot() {
            if (!cancelled) {
                setMonitorLoading(true);
                setMonitorError('');
            }

            try {
                const nextSnapshot = await basisApi.getBasisSnapshot(symbol);
                if (cancelled) {
                    return;
                }
                setSnapshot(nextSnapshot);
            } catch (error) {
                if (!cancelled) {
                    setMonitorError(error.message || 'Failed to load funding snapshot');
                }
            } finally {
                if (!cancelled) {
                    setMonitorLoading(false);
                }
            }
        }

        loadSnapshot();

        if (!autoRefresh) {
            return () => {
                cancelled = true;
            };
        }

        const timerId = window.setInterval(loadSnapshot, Math.max(10, refreshSeconds) * 1000);
        return () => {
            cancelled = true;
            window.clearInterval(timerId);
        };
    }, [autoRefresh, refreshSeconds, symbol]);

    const effectiveFundingRate = useMemo(() => {
        if (manualFundingRate !== null && manualFundingRate !== undefined) {
            return Number(manualFundingRate) / 100;
        }
        return Number(snapshot?.fundingRate || 0);
    }, [manualFundingRate, snapshot?.fundingRate]);

    const calculator = useMemo(() => {
        const totalCapital = Number(capital || 0);
        const spotCapital = totalCapital * (Number(spotRatio || 0) / 100);
        const marginCapital = totalCapital - spotCapital;
        const price = Number(entryPrice || 0);
        const quantity = price > 0 ? spotCapital / price : 0;
        const perpNotional = quantity * price;
        const incomePer8h = perpNotional * effectiveFundingRate;
        const incomePerDay = incomePer8h * 3;
        const incomePerMonth = incomePerDay * 30;
        const incomePerYear = incomePerDay * 365;
        const netYearlyIncome = incomePerYear - Number(roundTripFees || 0) * Math.max(1, Number(cyclesPerMonth || 0));
        const annualizedNet = totalCapital > 0 ? netYearlyIncome / totalCapital : 0;
        const singleCycleVolume = spotCapital * 2 + perpNotional * 2;
        const monthlyVolume = singleCycleVolume * Number(cyclesPerMonth || 0);

        return {
            spotCapital,
            marginCapital,
            quantity,
            perpNotional,
            incomePer8h,
            incomePerDay,
            incomePerMonth,
            incomePerYear,
            netYearlyIncome,
            annualizedNet,
            singleCycleVolume,
            monthlyVolume,
        };
    }, [capital, spotRatio, entryPrice, effectiveFundingRate, cyclesPerMonth, roundTripFees]);

    const currentDecision = snapshot ? getFundingDecision(snapshot.fundingRate) : null;
    const basisIsPositive = Number(snapshot?.basis || 0) > 0;
    const monitorStatusTag = currentDecision
        ? <Tag color={getFundingTone(snapshot?.fundingRate)}>{t(`basis.thresholds.${currentDecision}.judgment`)}</Tag>
        : null;

    return (
        <Layout>
            <Content className="basis-page">
                <div className="basis-hero">
                    <div className="basis-hero-copy">
                        <Space align="center" size={10} className="basis-eyebrow">
                            <SwapOutlined />
                            <span>{t('basis.eyebrow')}</span>
                        </Space>
                        <Title level={1} className="basis-title">{t('basis.title')}</Title>
                        <Paragraph className="basis-subtitle">{t('basis.subtitle')}</Paragraph>
                        <div className="basis-tags">
                            <Tag color="blue">{t('basis.tags.delta_neutral')}</Tag>
                            <Tag color="cyan">{t('basis.tags.funding_capture')}</Tag>
                            <Tag color="gold">{t('basis.tags.okx_eth')}</Tag>
                        </div>
                    </div>

                    <Card className="basis-highlight-card" bordered={false}>
                        <Text className="basis-mini-label">{t('basis.highlight.label')}</Text>
                        <div className="basis-highlight-rate">{t('basis.highlight.rate')}</div>
                        <Paragraph className="basis-highlight-text">{t('basis.highlight.description')}</Paragraph>
                        <Progress percent={40} showInfo={false} strokeColor="#22d3ee" trailColor="rgba(148, 163, 184, 0.16)" />
                        <Text className="basis-highlight-footnote">{t('basis.highlight.footnote')}</Text>
                    </Card>
                </div>

                <Row gutter={[18, 18]}>
                    <Col xs={24} xl={13}>
                        <Card
                            className="basis-panel"
                            title={t('basis.monitor.title', { defaultValue: '自动资金费率监控' })}
                            extra={monitorStatusTag}
                            bordered={false}
                        >
                            <div className="basis-toolbar">
                                <div className="basis-toolbar-group">
                                    <Text className="basis-mini-label">{t('basis.monitor.symbol', { defaultValue: '监控标的' })}</Text>
                                    <Segmented
                                        options={MONITOR_SYMBOLS}
                                        value={symbol}
                                        onChange={setSymbol}
                                    />
                                </div>
                                <div className="basis-toolbar-group">
                                    <Text className="basis-mini-label">{t('basis.monitor.auto', { defaultValue: '自动刷新' })}</Text>
                                    <Space>
                                        <Switch checked={autoRefresh} onChange={setAutoRefresh} />
                                        <InputNumber min={10} max={300} value={refreshSeconds} onChange={(value) => setRefreshSeconds(Number(value || 30))} addonAfter="s" />
                                    </Space>
                                </div>
                            </div>

                            {monitorLoading ? (
                                <div className="basis-monitor-loading">
                                    <Spin indicator={<ReloadOutlined spin />} />
                                </div>
                            ) : monitorError ? (
                                <Alert
                                    type="error"
                                    showIcon
                                    message={t('basis.monitor.load_failed', { defaultValue: '资金费率加载失败' })}
                                    description={monitorError}
                                />
                            ) : snapshot ? (
                                <>
                                    <Row gutter={[12, 12]} className="basis-live-stats">
                                        <Col xs={24} md={8}>
                                            <Card className="basis-nested-card" bordered={false}>
                                                <Statistic title={t('basis.monitor.current_rate', { defaultValue: '当前资金费率' })} value={formatPercent(snapshot.fundingRate)} />
                                            </Card>
                                        </Col>
                                        <Col xs={24} md={8}>
                                            <Card className="basis-nested-card" bordered={false}>
                                                <Statistic title={t('basis.monitor.current_basis', { defaultValue: '当前基差' })} value={formatMoney(snapshot.basis)} />
                                            </Card>
                                        </Col>
                                        <Col xs={24} md={8}>
                                            <Card className="basis-nested-card" bordered={false}>
                                                <Statistic title={t('basis.monitor.basis_percent', { defaultValue: '基差百分比' })} value={formatPercent(snapshot.basisPercent)} />
                                            </Card>
                                        </Col>
                                    </Row>

                                    <Descriptions className="basis-monitor-descriptions" column={1} size="small">
                                        <Descriptions.Item label={t('basis.monitor.swap_price', { defaultValue: '永续价格' })}>{formatMoney(snapshot.swapPrice)}</Descriptions.Item>
                                        <Descriptions.Item label={t('basis.monitor.spot_price', { defaultValue: '现货价格' })}>{formatMoney(snapshot.spotPrice)}</Descriptions.Item>
                                        <Descriptions.Item label={t('basis.monitor.basis_check', { defaultValue: '基差判断' })}>
                                            <Tag color={basisIsPositive ? 'green' : 'red'}>
                                                {basisIsPositive
                                                    ? t('basis.monitor.basis_positive', { defaultValue: '永续溢价，可做现货多 + 永续空' })
                                                    : t('basis.monitor.basis_negative', { defaultValue: '永续折价，当前不适合这个方向' })}
                                            </Tag>
                                        </Descriptions.Item>
                                        <Descriptions.Item label={t('basis.monitor.next_settlement', { defaultValue: '下次结算' })}>
                                            {snapshot.nextFundingTime ? new Date(snapshot.nextFundingTime).toLocaleString() : '--'}
                                        </Descriptions.Item>
                                        <Descriptions.Item label={t('basis.monitor.updated_at', { defaultValue: '最近更新' })}>
                                            {snapshot.ts ? new Date(snapshot.ts).toLocaleString() : '--'}
                                        </Descriptions.Item>
                                    </Descriptions>
                                </>
                            ) : (
                                <Empty description={t('basis.monitor.empty', { defaultValue: '暂无监控数据' })} />
                            )}
                        </Card>
                    </Col>

                    <Col xs={24} xl={11}>
                        <Card
                            className="basis-panel"
                            title={t('basis.calculator.title', { defaultValue: '本金收益与刷量计算器' })}
                            extra={<Tag color="green">{t('basis.calculator.extra', { defaultValue: '按你的本金实时计算' })}</Tag>}
                            bordered={false}
                        >
                            <Row gutter={[12, 12]}>
                                <Col xs={24} md={12}>
                                    <Text className="basis-mini-label">{t('basis.calculator.capital', { defaultValue: '总本金' })}</Text>
                                    <InputNumber className="basis-input" min={1000} step={1000} value={capital} onChange={(value) => setCapital(Number(value || 0))} addonBefore="$" />
                                </Col>
                                <Col xs={24} md={12}>
                                    <Text className="basis-mini-label">{t('basis.calculator.spot_ratio', { defaultValue: '现货资金占比' })}</Text>
                                    <InputNumber className="basis-input" min={10} max={90} step={5} value={spotRatio} onChange={(value) => setSpotRatio(Number(value || 50))} addonAfter="%" />
                                </Col>
                                <Col xs={24} md={12}>
                                    <Text className="basis-mini-label">{t('basis.calculator.price', { defaultValue: '入场价格' })}</Text>
                                    <InputNumber className="basis-input" min={1} value={entryPrice} onChange={(value) => setEntryPrice(Number(value || 0))} addonBefore="$" />
                                </Col>
                                <Col xs={24} md={12}>
                                    <Text className="basis-mini-label">{t('basis.calculator.rate', { defaultValue: '资金费率（8h）' })}</Text>
                                    <InputNumber className="basis-input" step={0.001} value={manualFundingRate ?? Number((snapshot?.fundingRate || 0) * 100)} onChange={(value) => setManualFundingRate(value === null ? null : Number(value))} addonAfter="%" />
                                </Col>
                                <Col xs={24} md={12}>
                                    <Text className="basis-mini-label">{t('basis.calculator.cycles', { defaultValue: '每月调仓次数' })}</Text>
                                    <InputNumber className="basis-input" min={1} max={60} value={cyclesPerMonth} onChange={(value) => setCyclesPerMonth(Number(value || 1))} />
                                </Col>
                                <Col xs={24} md={12}>
                                    <Text className="basis-mini-label">{t('basis.calculator.fees', { defaultValue: '单次往返手续费' })}</Text>
                                    <InputNumber className="basis-input" min={0} step={1} value={roundTripFees} onChange={(value) => setRoundTripFees(Number(value || 0))} addonBefore="$" />
                                </Col>
                            </Row>

                            <Row gutter={[12, 12]} className="basis-live-stats">
                                <Col xs={24} md={12}><Card className="basis-nested-card" bordered={false}><Statistic title={t('basis.calculator.quantity', { defaultValue: '对冲数量' })} value={calculator.quantity.toFixed(4)} suffix={symbol} /></Card></Col>
                                <Col xs={24} md={12}><Card className="basis-nested-card" bordered={false}><Statistic title={t('basis.calculator.perp_notional', { defaultValue: '合约名义价值' })} value={formatMoney(calculator.perpNotional)} /></Card></Col>
                                <Col xs={24} md={12}><Card className="basis-nested-card" bordered={false}><Statistic title={t('basis.calculator.per_day', { defaultValue: '每日收益' })} value={formatMoney(calculator.incomePerDay)} /></Card></Col>
                                <Col xs={24} md={12}><Card className="basis-nested-card" bordered={false}><Statistic title={t('basis.calculator.per_month', { defaultValue: '每月收益' })} value={formatMoney(calculator.incomePerMonth)} /></Card></Col>
                                <Col xs={24} md={12}><Card className="basis-nested-card" bordered={false}><Statistic title={t('basis.calculator.net_year', { defaultValue: '净年收益' })} value={formatMoney(calculator.netYearlyIncome)} /></Card></Col>
                                <Col xs={24} md={12}><Card className="basis-nested-card" bordered={false}><Statistic title={t('basis.calculator.net_annualized', { defaultValue: '净年化' })} value={`${(calculator.annualizedNet * 100).toFixed(2)}%`} /></Card></Col>
                            </Row>

                            <Descriptions className="basis-monitor-descriptions" column={1} size="small">
                                <Descriptions.Item label={t('basis.calculator.spot_capital', { defaultValue: '现货占用资金' })}>{formatMoney(calculator.spotCapital)}</Descriptions.Item>
                                <Descriptions.Item label={t('basis.calculator.margin_capital', { defaultValue: '合约保证金' })}>{formatMoney(calculator.marginCapital)}</Descriptions.Item>
                                <Descriptions.Item label={t('basis.calculator.single_volume', { defaultValue: '单次操作刷量' })}>{formatMoney(calculator.singleCycleVolume)}</Descriptions.Item>
                                <Descriptions.Item label={t('basis.calculator.monthly_volume', { defaultValue: '月刷量' })}>{formatMoney(calculator.monthlyVolume)}</Descriptions.Item>
                            </Descriptions>
                        </Card>
                    </Col>
                </Row>

                <Row gutter={[16, 16]} className="basis-stat-grid">
                    <Col xs={24} md={12} xl={6}><Card className="basis-stat-card" bordered={false}><Statistic title={t('basis.stats.base_capital')} value="$10,000" prefix={<DollarCircleOutlined />} /></Card></Col>
                    <Col xs={24} md={12} xl={6}><Card className="basis-stat-card" bordered={false}><Statistic title={t('basis.stats.position_example')} value="2.5 ETH" prefix={<FundOutlined />} /></Card></Col>
                    <Col xs={24} md={12} xl={6}><Card className="basis-stat-card" bordered={false}><Statistic title={t('basis.stats.settlement')} value={t('basis.stats.settlement_value')} prefix={<ClockCircleOutlined />} /></Card></Col>
                    <Col xs={24} md={12} xl={6}><Card className="basis-stat-card" bordered={false}><Statistic title={t('basis.stats.mode')} value={t('basis.stats.mode_value')} prefix={<SafetyCertificateOutlined />} /></Card></Col>
                </Row>

                <Row gutter={[18, 18]}>
                    <Col xs={24} xl={14}>
                        <Card className="basis-panel" title={t('basis.section.precheck')} extra={<Tag color="cyan">{t('basis.section.precheck_tag')}</Tag>} bordered={false}>
                            <Paragraph className="basis-panel-lead">{t('basis.precheck.intro')}</Paragraph>
                            <Table columns={fundingColumns} dataSource={fundingThresholds} pagination={false} rowKey="key" className="basis-table" />
                            <Divider />
                            <div className="basis-basis-box">
                                <Text className="basis-mini-label">{t('basis.precheck.basis_formula_label')}</Text>
                                <div className="basis-formula">{t('basis.precheck.basis_formula')}</div>
                                <ul className="basis-list">
                                    <li>{t('basis.precheck.basis_positive')}</li>
                                    <li>{t('basis.precheck.basis_negative')}</li>
                                </ul>
                            </div>
                        </Card>
                    </Col>

                    <Col xs={24} xl={10}>
                        <Card className="basis-panel" title={t('basis.section.execution')} extra={<Tag color="geekblue">{t('basis.section.execution_tag')}</Tag>} bordered={false}>
                            <Timeline
                                items={[
                                    { color: '#22d3ee', children: <div><Text strong>{t('basis.execution.spot_title')}</Text><Paragraph>{t('basis.execution.spot_body')}</Paragraph></div> },
                                    { color: '#f97316', children: <div><Text strong>{t('basis.execution.perp_title')}</Text><Paragraph>{t('basis.execution.perp_body')}</Paragraph></div> },
                                    { color: '#facc15', children: <div><Text strong>{t('basis.execution.sync_title')}</Text><Paragraph>{t('basis.execution.sync_body')}</Paragraph></div> },
                                ]}
                            />
                            <Alert className="basis-inline-alert" type="warning" showIcon icon={<AlertOutlined />} message={t('basis.execution.warning_title')} description={t('basis.execution.warning_body')} />
                        </Card>
                    </Col>
                </Row>

                <Row gutter={[18, 18]}>
                    <Col xs={24} lg={14}>
                        <Card className="basis-panel" title={t('basis.section.management')} extra={<Tag color="purple">{t('basis.section.management_tag')}</Tag>} bordered={false}>
                            <div className="basis-check-grid">
                                <div className="basis-check-item"><CheckCircleOutlined /><div><Text strong>{t('basis.management.funding_title')}</Text><Paragraph>{t('basis.management.funding_body')}</Paragraph></div></div>
                                <div className="basis-check-item"><CheckCircleOutlined /><div><Text strong>{t('basis.management.match_title')}</Text><Paragraph>{t('basis.management.match_body')}</Paragraph></div></div>
                                <div className="basis-check-item"><CheckCircleOutlined /><div><Text strong>{t('basis.management.margin_title')}</Text><Paragraph>{t('basis.management.margin_body')}</Paragraph></div></div>
                                <div className="basis-check-item"><CheckCircleOutlined /><div><Text strong>{t('basis.management.alert_title')}</Text><Paragraph>{t('basis.management.alert_body')}</Paragraph></div></div>
                            </div>
                        </Card>
                    </Col>

                    <Col xs={24} lg={10}>
                        <Card className="basis-panel" title={t('basis.section.exit')} extra={<Tag color="volcano">{t('basis.section.exit_tag')}</Tag>} bordered={false}>
                            <ul className="basis-list basis-exit-list">
                                <li>{t('basis.exit.negative')}</li>
                                <li>{t('basis.exit.low')}</li>
                                <li>{t('basis.exit.capital')}</li>
                            </ul>
                            <Divider />
                            <Paragraph className="basis-panel-lead">{t('basis.exit.execution_title')}</Paragraph>
                            <ul className="basis-list">
                                <li>{t('basis.exit.step_spot')}</li>
                                <li>{t('basis.exit.step_perp')}</li>
                                <li>{t('basis.exit.step_sync')}</li>
                            </ul>
                        </Card>
                    </Col>
                </Row>

                <Row gutter={[18, 18]}>
                    <Col xs={24} xl={12}>
                        <Card className="basis-panel" title={t('basis.section.pnl')} extra={<LineChartOutlined />} bordered={false}>
                            <Row gutter={[12, 12]}>
                                <Col span={12}><Card className="basis-nested-card" bordered={false}><Statistic title={t('basis.pnl.per_8h')} value="$1" /></Card></Col>
                                <Col span={12}><Card className="basis-nested-card" bordered={false}><Statistic title={t('basis.pnl.per_day')} value="$3" /></Card></Col>
                                <Col span={12}><Card className="basis-nested-card" bordered={false}><Statistic title={t('basis.pnl.per_month')} value="$90" /></Card></Col>
                                <Col span={12}><Card className="basis-nested-card" bordered={false}><Statistic title={t('basis.pnl.annualized')} value="10.8%" /></Card></Col>
                            </Row>
                            <Paragraph className="basis-footnote">{t('basis.pnl.footnote')}</Paragraph>
                        </Card>
                    </Col>

                    <Col xs={24} xl={12}>
                        <Card className="basis-panel" title={t('basis.section.volume')} extra={<Tag color="green">{t('basis.volume.extra')}</Tag>} bordered={false}>
                            <Table columns={volumeColumns} dataSource={capitalSplit} pagination={false} rowKey="key" className="basis-table" />
                            <Paragraph className="basis-footnote">{t('basis.volume.footnote')}</Paragraph>
                        </Card>
                    </Col>
                </Row>

                <Card className="basis-panel basis-risk-panel" title={t('basis.section.risks')} extra={<Tag color="red">{t('basis.section.risks_tag')}</Tag>} bordered={false}>
                    <Row gutter={[16, 16]}>
                        <Col xs={24} md={12} xl={6}><Alert type="info" showIcon message={t('basis.risks.capital_title')} description={t('basis.risks.capital_body')} /></Col>
                        <Col xs={24} md={12} xl={6}><Alert type="warning" showIcon message={t('basis.risks.margin_title')} description={t('basis.risks.margin_body')} /></Col>
                        <Col xs={24} md={12} xl={6}><Alert type="success" showIcon message={t('basis.risks.symbols_title')} description={t('basis.risks.symbols_body')} /></Col>
                        <Col xs={24} md={12} xl={6}><Alert type="error" showIcon message={t('basis.risks.market_title')} description={t('basis.risks.market_body')} /></Col>
                    </Row>
                </Card>
            </Content>
        </Layout>
    );
}
