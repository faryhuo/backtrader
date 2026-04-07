import { useEffect, useMemo, useState } from 'react';
import {
  Alert,
  Button,
  Card,
  Col,
  Form,
  InputNumber,
  Radio,
  Row,
  Select,
  Tag,
  Typography,
} from 'antd';
import {
  ClockCircleOutlined,
  DollarOutlined,
  DownOutlined,
  PercentageOutlined,
  PlayCircleOutlined,
  PieChartOutlined,
  RadarChartOutlined,
  RightOutlined,
  SafetyCertificateOutlined,
  SearchOutlined,
  SettingOutlined,
  SwapOutlined,
  WarningOutlined,
} from '@ant-design/icons';
import { useSearchParams } from 'react-router-dom';
import { useTranslation } from 'react-i18next';
import { useStrategyParams } from '../../hooks/useStrategyParams';
import { api } from '../../services/api';
import SymbolSearchModal from './SymbolSearchModal';
import './LiveConfigForm.css';

const { Text, Title, Paragraph } = Typography;

// Fallback pairs used only when the Binance API is unavailable
const FALLBACK_PAIRS = [
  'BTC/USDT', 'ETH/USDT', 'BNB/USDT', 'SOL/USDT', 'XRP/USDT',
  'DOGE/USDT', 'ADA/USDT', 'AVAX/USDT', 'DOT/USDT', 'MATIC/USDT',
];

const TIMEFRAMES = ['1m', '5m', '15m', '1h', '4h', '1d'];
const MARKET_OPTIONS = [
  { value: 'spot', label: 'Spot' },
  { value: 'futures', label: 'Futures' },
];
const SIZER_OPTIONS = [
  { value: 'fixed_size', label: 'Fixed Size' },
  { value: 'percent_sizer', label: 'Percent Sizer' },
  { value: 'all_in_sizer', label: 'All In' },
  { value: 'risk_sizer', label: 'Risk Control' },
  { value: 'kelly_sizer', label: 'Kelly Criterion' },
];

const LiveConfigForm = ({ onSubmit, loading }) => {
  const { t } = useTranslation();
  const [searchParams] = useSearchParams();
  const [form] = Form.useForm();
  const [strategies, setStrategies] = useState([]);
  const [loadingData, setLoadingData] = useState(false);
  const [symbols, setSymbols] = useState(FALLBACK_PAIRS);
  const [symbolsLoading, setSymbolsLoading] = useState(false);
  const [symbolModalOpen, setSymbolModalOpen] = useState(false);
  const [mode, setMode] = useState('paper');
  const [market, setMarket] = useState('spot');
  const [paramsExpanded, setParamsExpanded] = useState(true);
  const [sizerType, setSizerType] = useState('percent_sizer');

  const formValues = Form.useWatch([], form) || {};
  const selectedStrategyName = formValues.strategy_name || '';

  const {
    strategyParams,
    paramOverrides,
    handleParamChange,
    getParamsForApi,
  } = useStrategyParams(selectedStrategyName, {
    enabled: Boolean(selectedStrategyName),
    includeCode: false,
  });

  useEffect(() => {
    const loadStrategies = async () => {
      try {
        setLoadingData(true);
        const data = await api.getStrategies();
        setStrategies(Array.isArray(data) ? data : (data?.strategies || []));
      } catch (error) {
        console.error('Failed to load strategies:', error);
      } finally {
        setLoadingData(false);
      }
    };

    loadStrategies();
  }, []);

  useEffect(() => {
    const loadSymbols = async () => {
      try {
        setSymbolsLoading(true);
        const data = await api.getSymbols(market);
        const pairs = Array.isArray(data?.symbols)
          ? data.symbols.map((s) => s.symbol)
          : null;
        if (pairs && pairs.length > 0) {
          setSymbols(pairs);
        }
      } catch (_error) {
        // Silently fall back to hardcoded pairs on network/API error
      } finally {
        setSymbolsLoading(false);
      }
    };

    loadSymbols();
  }, [market]);

  useEffect(() => {
    const nextMode = searchParams.get('mode');
    const nextMarket = searchParams.get('market');
    const nextSymbol = searchParams.get('symbol');
    const nextStrategy = searchParams.get('strategy_name');
    const nextTimeframe = searchParams.get('timeframe');
    const nextValues = {};

    if (nextMode === 'paper' || nextMode === 'live') {
      nextValues.mode = nextMode;
      setMode(nextMode);
    }

    if (nextMarket === 'spot' || nextMarket === 'futures') {
      nextValues.market = nextMarket;
      setMarket(nextMarket);
    }

    if (nextSymbol) {
      nextValues.symbol = nextSymbol;
    }

    if (nextStrategy) {
      nextValues.strategy_name = nextStrategy;
    }

    if (TIMEFRAMES.includes(nextTimeframe)) {
      nextValues.timeframe = nextTimeframe;
    }

    if (Object.keys(nextValues).length > 0) {
      form.setFieldsValue(nextValues);
    }
  }, [form, searchParams]);

  const selectedSymbol = formValues.symbol || 'BTC/USDT';

  const selectedStrategy = formValues.strategy_name || t('live.form.unselected', 'Not selected');
  const selectedTimeframe = formValues.timeframe || '1m';
  const selectedCommission = formValues.commission ?? 0.001;

  const modeTone = useMemo(() => {
    return mode === 'live' ? 'danger' : 'safe';
  }, [mode]);

  const startLabel = mode === 'live'
    ? t('live.form.start_live', 'Start LIVE Trading')
    : t('live.form.start_paper', 'Start Paper Trading');

  const handleSubmit = (values) => {
    onSubmit({
      strategy_name: values.strategy_name,
      symbol: values.symbol,
      market: values.market,
      mode: values.mode,
      timeframe: values.timeframe,
      params: getParamsForApi(),
      sizer_type: values.sizer_type || sizerType,
      sizer_config: values.sizer_type === 'percent_sizer'
        ? { percents: values.sizer_percents ?? 10 }
        : values.sizer_type === 'fixed_size'
          ? { stake: values.sizer_stake ?? 1 }
          : values.sizer_type === 'risk_sizer' || values.sizer_type === 'kelly_sizer'
            ? { risk_percent: values.sizer_risk_percent ?? 2 }
            : {},
      commission: values.commission,
    });
  };

  return (
    <>
    <div className="live-launch-grid">
      <div className="live-launch-panel">
        <div className="live-launch-hero">
          <div>
            <Text className="live-launch-eyebrow">
              {t('live.form.eyebrow', 'Session Launcher')}
            </Text>
            <Title level={3} className="live-launch-title">
              {t('live.form.title', 'Build the next live trading session')}
            </Title>
            <Paragraph className="live-launch-description">
              {t(
                'live.form.description',
                'Choose strategy, market, execution mode, and capital before the engine starts routing signals and market data.'
              )}
            </Paragraph>
          </div>

          <div className={`live-mode-pill live-mode-pill-${modeTone}`}>
            <SafetyCertificateOutlined />
            <span>
              {mode === 'live'
                ? t('live.form.live_mode_label', 'LIVE mode armed')
                : t('live.form.paper_mode_label', 'Paper mode ready')}
            </span>
          </div>
        </div>

        <Form
          form={form}
          layout="vertical"
          onFinish={handleSubmit}
          initialValues={{
            mode: 'paper',
            market: 'spot',
            timeframe: '1m',
            sizer_type: 'percent_sizer',
            sizer_percents: 10,
            commission: 0.001,
            symbol: 'BTC/USDT',
          }}
        >
          <div className="launch-section">
            <div className="launch-section-heading">
              <RadarChartOutlined />
              <span>{t('live.form.section_strategy', 'Strategy and market')}</span>
            </div>

            <Row gutter={[16, 0]}>
              <Col xs={24} md={9}>
                <Form.Item
                  name="strategy_name"
                  label={t('live.form.strategy', 'Strategy')}
                  rules={[{ required: true, message: t('live.form.strategy_required', 'Select a strategy') }]}
                >
                  <Select
                    placeholder={t('live.form.select_strategy', 'Select strategy')}
                    loading={loadingData}
                    showSearch
                    optionFilterProp="label"
                    options={strategies.map((item) => {
                      const value = item.name || item;
                      return { value, label: value };
                    })}
                  />
                </Form.Item>
              </Col>

              <Col xs={24} md={7}>
                <Form.Item
                  name="market"
                  label={t('live.form.market', 'Market')}
                  rules={[{ required: true }]}
                >
                  <Select
                    options={MARKET_OPTIONS.map((option) => ({
                      value: option.value,
                      label: t(`live.form.market_${option.value}`, option.label),
                    }))}
                    onChange={(value) => {
                      setMarket(value);
                      form.setFieldsValue({ symbol: 'BTC/USDT' });
                    }}
                  />
                </Form.Item>
              </Col>

              <Col xs={24} md={8}>
                <Form.Item
                  name="symbol"
                  label={t('live.form.symbol', 'Trading Pair')}
                  rules={[{ required: true }]}
                >
                  <Select
                    showSearch
                    optionFilterProp="label"
                    loading={symbolsLoading}
                    suffixIcon={
                      <SearchOutlined
                        style={{ cursor: 'pointer' }}
                        onMouseDown={(e) => {
                          e.preventDefault();
                          e.stopPropagation();
                          setSymbolModalOpen(true);
                        }}
                      />
                    }
                    options={symbols.map((pair) => ({ value: pair, label: pair }))}
                  />
                </Form.Item>
              </Col>
            </Row>

            {strategyParams.length > 0 && (
              <div className="live-param-section">
                <button
                  type="button"
                  className="live-param-toggle"
                  onClick={() => setParamsExpanded((prev) => !prev)}
                >
                  {paramsExpanded ? <DownOutlined /> : <RightOutlined />}
                  <SettingOutlined />
                  <span>{t('live.form.strategy_params', 'Strategy Parameters')}</span>
                  <span className="live-param-count">({strategyParams.length})</span>
                </button>

                {paramsExpanded && (
                  <div className="live-param-grid">
                    {strategyParams.map((param) => {
                      const value = paramOverrides[param.name] ?? param.value;
                      const isNumeric = param.type === 'int' || param.type === 'float';

                      return (
                        <Form.Item
                          key={param.name}
                          label={`${param.name} (${param.type})`}
                          className="live-param-item"
                        >
                          {isNumeric ? (
                            <InputNumber
                              style={{ width: '100%' }}
                              step={param.type === 'float' ? 0.01 : 1}
                              value={Number(value)}
                              onChange={(nextValue) => handleParamChange(param.name, nextValue, param.type)}
                            />
                          ) : (
                            <input
                              className="live-param-input"
                              value={value ?? ''}
                              onChange={(event) => handleParamChange(param.name, event.target.value, param.type)}
                            />
                          )}
                        </Form.Item>
                      );
                    })}
                  </div>
                )}
              </div>
            )}
          </div>

          <div className="launch-section">
            <div className="launch-section-heading">
              <SwapOutlined />
              <span>{t('live.form.section_execution', 'Execution settings')}</span>
            </div>

            <Form.Item
              name="mode"
              label={t('live.form.mode', 'Trading Mode')}
            >
              <Radio.Group
                className="live-mode-switch"
                onChange={(event) => setMode(event.target.value)}
                buttonStyle="solid"
              >
                <Radio.Button value="paper">
                  {t('live.form.paper_mode', 'Paper (Testnet)')}
                </Radio.Button>
                <Radio.Button value="live">
                  {t('live.form.live_mode', 'Live (Real Money)')}
                </Radio.Button>
              </Radio.Group>
            </Form.Item>

            {mode === 'live' ? (
              <Alert
                type="error"
                showIcon
                icon={<WarningOutlined />}
                className="live-mode-alert"
                message={t('live.form.live_warning', 'LIVE MODE: Real money will be used. Make sure your Binance API keys are configured.')}
              />
            ) : (
              <Alert
                type="info"
                showIcon
                className="live-mode-alert"
                message={t('live.form.paper_hint', 'Paper mode connects to exchange testnet APIs so you can verify market data, balances, logs, and order routing without using production funds.')}
              />
            )}

            <Form.Item
              name="timeframe"
              label={t('live.form.timeframe', 'Timeframe')}
            >
              <Select
                suffixIcon={<ClockCircleOutlined />}
                options={TIMEFRAMES.map((value) => ({
                  value,
                  label: `${value} - ${t(`timeframe.${value}`, value)}`,
                }))}
              />
            </Form.Item>

            <Row gutter={[16, 0]}>
              <Col xs={24} md={12}>
                <Form.Item
                  name="sizer_type"
                  label={t('config_form.sizer_type', 'Position Sizing')}
                >
                  <Select
                    suffixIcon={<PieChartOutlined />}
                    onChange={(value) => setSizerType(value)}
                    options={SIZER_OPTIONS.map((option) => ({
                      value: option.value,
                      label: t(`sizer.${option.value}`, option.label),
                    }))}
                  />
                </Form.Item>
              </Col>

              <Col xs={24} md={12}>
                {sizerType === 'fixed_size' && (
                  <Form.Item
                    name="sizer_stake"
                    label={t('config_form.order_size', 'Order Size')}
                  >
                    <InputNumber min={1} step={1} style={{ width: '100%' }} />
                  </Form.Item>
                )}

                {sizerType === 'percent_sizer' && (
                  <Form.Item
                    name="sizer_percents"
                    label={t('config_form.sizer_percent', 'Position %')}
                  >
                    <InputNumber
                      min={0.1}
                      max={100}
                      step={0.1}
                      prefix={<PercentageOutlined />}
                      style={{ width: '100%' }}
                    />
                  </Form.Item>
                )}

                {(sizerType === 'risk_sizer' || sizerType === 'kelly_sizer') && (
                  <Form.Item
                    name="sizer_risk_percent"
                    label={t('config_form.sizer_risk', 'Risk per Trade %')}
                  >
                    <InputNumber
                      min={0.1}
                      max={100}
                      step={0.1}
                      prefix={<PercentageOutlined />}
                      style={{ width: '100%' }}
                    />
                  </Form.Item>
                )}
              </Col>
            </Row>
          </div>

          <div className="launch-section">
            <div className="launch-section-heading">
              <DollarOutlined />
              <span>{t('live.form.section_capital', 'Capital source and costs')}</span>
            </div>

            <Alert
              type="warning"
              showIcon
              className="live-mode-alert"
              message={
                mode === 'live'
                  ? t('live.form.balance_source_live', 'Live mode loads available quote balance directly from the exchange account before the session starts.')
                  : t('live.form.balance_source_paper', 'Paper mode loads available quote balance from the exchange testnet account before the session starts.')
              }
            />

            <Form.Item
              name="commission"
              label={t('live.form.commission', 'Commission Rate')}
            >
              <InputNumber min={0} max={0.1} step={0.0001} style={{ width: '100%' }} />
            </Form.Item>
          </div>

          <Card className="launch-summary-card" bordered={false}>
            <div className="launch-summary-header">
              <span>{t('live.form.summary_title', 'Launch summary')}</span>
              <Tag color={mode === 'live' ? 'red' : 'cyan'}>
                {mode === 'live'
                  ? t('live.form.live_summary_tag', 'LIVE')
                  : t('live.form.paper_summary_tag', 'PAPER')}
              </Tag>
            </div>

            <Row gutter={[12, 12]}>
              <Col xs={24} sm={12}>
                <div className="launch-summary-item">
                  <span>{t('live.form.strategy', 'Strategy')}</span>
                  <strong>{selectedStrategy}</strong>
                </div>
              </Col>
              <Col xs={24} sm={12}>
                <div className="launch-summary-item">
                  <span>{t('live.form.symbol', 'Trading Pair')}</span>
                  <strong>{selectedSymbol}</strong>
                </div>
              </Col>
              <Col xs={24} sm={12}>
                <div className="launch-summary-item">
                  <span>{t('live.form.market', 'Market')}</span>
                  <strong>{t(`live.form.market_${market}`, market)}</strong>
                </div>
              </Col>
              <Col xs={24} sm={12}>
                <div className="launch-summary-item">
                  <span>{t('live.form.timeframe', 'Timeframe')}</span>
                  <strong>{t(`timeframe.${selectedTimeframe}`, selectedTimeframe)}</strong>
                </div>
              </Col>
              <Col xs={24} sm={12}>
                <div className="launch-summary-item">
                  <span>{t('live.form.balance_source', 'Balance source')}</span>
                  <strong>
                    {mode === 'live'
                      ? t('live.form.balance_source_live_short', 'Exchange live account')
                      : t('live.form.balance_source_paper_short', 'Exchange testnet account')}
                  </strong>
                </div>
              </Col>
            </Row>

            <div className="launch-summary-footer">
              <Text className="launch-summary-footnote">
                {t('live.form.commission_preview', 'Commission')}: {Number(selectedCommission).toFixed(4)}
              </Text>
              <Button
                type="primary"
                htmlType="submit"
                icon={<PlayCircleOutlined />}
                loading={loading}
                size="large"
                className="launch-submit-button"
                danger={mode === 'live'}
              >
                {startLabel}
              </Button>
            </div>
          </Card>
        </Form>
      </div>

      <div className="live-launch-sidebar">
        <Card className="launch-side-card" bordered={false}>
          <Text className="launch-side-label">
            {t('live.form.sidebar_title', 'Before you launch')}
          </Text>
          <Title level={4} className="launch-side-title">
            {t('live.form.sidebar_heading', 'Make the session intentional')}
          </Title>
          <Paragraph className="launch-side-copy">
            {t(
              'live.form.sidebar_description',
              'The launcher should answer three questions before a session starts: what strategy is running, what market it trades, and what capital it is allowed to risk.'
            )}
          </Paragraph>

          <div className="launch-checklist">
            <div className="launch-check-item">
              <span>01</span>
              <div>
                <strong>{t('live.form.check_strategy_title', 'Choose a strategy you trust')}</strong>
                <p>{t('live.form.check_strategy_text', 'Use a validation strategy for smoke tests, then switch to a production strategy once logs and orders look correct.')}</p>
              </div>
            </div>
            <div className="launch-check-item">
              <span>02</span>
              <div>
                <strong>{t('live.form.check_mode_title', 'Paper first, live later')}</strong>
                <p>{t('live.form.check_mode_text', 'Paper mode should verify exchange-backed feed status, account sync, order routing, and UI visibility before you arm real execution.')}</p>
              </div>
            </div>
            <div className="launch-check-item">
              <span>03</span>
              <div>
                <strong>{t('live.form.check_risk_title', 'Use the right exchange account')}</strong>
                <p>{t('live.form.check_risk_text', 'The launcher no longer accepts local fake balances. If credentials or account balances are missing, startup should fail immediately.')}</p>
              </div>
            </div>
          </div>
        </Card>
      </div>
    </div>

    <SymbolSearchModal
      open={symbolModalOpen}
      market={market}
      onClose={() => setSymbolModalOpen(false)}
      onSelect={(symbol) => form.setFieldsValue({ symbol })}
    />
    </>
  );
};

export default LiveConfigForm;
