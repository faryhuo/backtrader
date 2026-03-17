import { useState, useEffect } from 'react';
import { Form, Select, InputNumber, Button, Alert, Radio, Space } from 'antd';
import { PlayCircleOutlined, WarningOutlined } from '@ant-design/icons';
import { useTranslation } from 'react-i18next';
import { api } from '../../services/api';

const COMMON_PAIRS = [
  'BTC/USDT', 'ETH/USDT', 'BNB/USDT', 'SOL/USDT', 'XRP/USDT',
  'DOGE/USDT', 'ADA/USDT', 'AVAX/USDT', 'DOT/USDT', 'MATIC/USDT',
];

const TIMEFRAMES = [
  { value: '1m', label: '1m' },
  { value: '5m', label: '5m' },
  { value: '15m', label: '15m' },
  { value: '30m', label: '30m' },
  { value: '1h', label: '1h' },
  { value: '4h', label: '4h' },
  { value: '1d', label: '1d' },
];

/**
 * Simplified config form for Binance Spot trading
 */
const LiveConfigForm = ({ onSubmit, loading }) => {
  const { t } = useTranslation();
  const [form] = Form.useForm();
  const [strategies, setStrategies] = useState([]);
  const [loadingData, setLoadingData] = useState(false);
  const [mode, setMode] = useState('paper');

  useEffect(() => {
    loadStrategies();
  }, []);

  const loadStrategies = async () => {
    try {
      setLoadingData(true);
      const data = await api.getStrategies();
      setStrategies(Array.isArray(data) ? data : (data?.strategies || []));
    } catch (e) {
      console.error('Failed to load strategies:', e);
    } finally {
      setLoadingData(false);
    }
  };

  const handleSubmit = (values) => {
    onSubmit({
      strategy_name: values.strategy_name,
      symbol: values.symbol,
      mode: values.mode,
      timeframe: values.timeframe,
      initial_cash: values.initial_cash,
      commission: values.commission,
    });
  };

  return (
    <Form
      form={form}
      layout="vertical"
      onFinish={handleSubmit}
      initialValues={{
        mode: 'paper',
        timeframe: '1m',
        initial_cash: 10000,
        commission: 0.001,
        symbol: 'BTC/USDT',
      }}
    >
      {/* Strategy */}
      <Form.Item
        name="strategy_name"
        label={t('live.form.strategy', 'Strategy')}
        rules={[{ required: true, message: t('live.form.strategy_required', 'Select a strategy') }]}
      >
        <Select
          placeholder={t('live.form.select_strategy', 'Select strategy')}
          loading={loadingData}
          showSearch
          optionFilterProp="children"
        >
          {strategies.map(s => (
            <Select.Option key={s.name || s} value={s.name || s}>{s.name || s}</Select.Option>
          ))}
        </Select>
      </Form.Item>

      {/* Symbol */}
      <Form.Item
        name="symbol"
        label={t('live.form.symbol', 'Trading Pair')}
        rules={[{ required: true }]}
      >
        <Select showSearch placeholder="BTC/USDT">
          {COMMON_PAIRS.map(pair => (
            <Select.Option key={pair} value={pair}>{pair}</Select.Option>
          ))}
        </Select>
      </Form.Item>

      {/* Mode */}
      <Form.Item
        name="mode"
        label={t('live.form.mode', 'Trading Mode')}
      >
        <Radio.Group onChange={e => setMode(e.target.value)} buttonStyle="solid">
          <Radio.Button value="paper" style={{ minWidth: 120 }}>
            {t('live.form.paper_mode', 'Paper (Testnet)')}
          </Radio.Button>
          <Radio.Button value="live" style={{ minWidth: 120 }}>
            {t('live.form.live_mode', 'Live (Real Money)')}
          </Radio.Button>
        </Radio.Group>
      </Form.Item>

      {mode === 'live' && (
        <Alert
          type="error"
          icon={<WarningOutlined />}
          showIcon
          message={t('live.form.live_warning', 'LIVE MODE: Real money will be used. Make sure your Binance API keys are configured.')}
          style={{ marginBottom: 16 }}
        />
      )}

      {/* Timeframe */}
      <Form.Item name="timeframe" label={t('live.form.timeframe', 'Timeframe')}>
        <Select>
          {TIMEFRAMES.map(tf => (
            <Select.Option key={tf.value} value={tf.value}>{tf.label}</Select.Option>
          ))}
        </Select>
      </Form.Item>

      {/* Cash & Commission */}
      <Space size="large" style={{ width: '100%' }}>
        <Form.Item
          name="initial_cash"
          label={t('live.form.initial_cash', 'Initial Cash (USDT)')}
          style={{ flex: 1 }}
        >
          <InputNumber min={100} max={10000000} style={{ width: '100%' }} />
        </Form.Item>

        <Form.Item
          name="commission"
          label={t('live.form.commission', 'Commission Rate')}
          style={{ flex: 1 }}
        >
          <InputNumber min={0} max={0.1} step={0.0001} style={{ width: '100%' }} />
        </Form.Item>
      </Space>

      {/* Submit */}
      <Form.Item>
        <Button
          type="primary"
          htmlType="submit"
          icon={<PlayCircleOutlined />}
          loading={loading}
          block
          size="large"
          danger={mode === 'live'}
        >
          {mode === 'live'
            ? t('live.form.start_live', 'Start LIVE Trading')
            : t('live.form.start_paper', 'Start Paper Trading')
          }
        </Button>
      </Form.Item>
    </Form>
  );
};

export default LiveConfigForm;
