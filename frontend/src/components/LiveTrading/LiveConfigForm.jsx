import React, { useState, useEffect } from 'react';
import { Form, Input, Select, InputNumber, Button, Card, Space, Alert, Tooltip, Radio } from 'antd';
import { InfoCircleOutlined } from '@ant-design/icons';
import { useTranslation } from 'react-i18next';
import { api } from '../../services/api';

const { Option } = Select;

/**
 * Live Trading Configuration Form
 * Form for configuring and starting a new trading session
 */
const LiveConfigForm = ({ onSubmit, loading }) => {
  const { t } = useTranslation();
  const [form] = Form.useForm();
  const [strategies, setStrategies] = useState([]);
  const [exchanges, setExchanges] = useState([]);
  const [loadingData, setLoadingData] = useState(false);
  const [mode, setMode] = useState('paper');
  const [assetClass, setAssetClass] = useState('crypto');

  useEffect(() => {
    loadStrategies();
    loadExchanges('crypto');
  }, []);

  const loadStrategies = async () => {
    try {
      setLoadingData(true);
      const data = await api.getStrategies();
      setStrategies(data || []);
    } catch (error) {
      console.error('Failed to load strategies:', error);
    } finally {
      setLoadingData(false);
    }
  };

  const loadExchanges = async (type) => {
    if (type === 'crypto') {
      try {
        const data = await api.getExchanges();
        setExchanges(data?.exchanges || ['binance', 'okx', 'bybit']);
      } catch (error) {
        console.error('Failed to load exchanges:', error);
        setExchanges(['binance', 'okx', 'bybit']);
      }
    } else {
      // Mock exchanges for stocks
      setExchanges(['alpaca', 'ibkr', 'futu']);
    }
  };

  const handleAssetChange = (e) => {
    const val = e.target.value;
    setAssetClass(val);
    form.setFieldsValue({ exchange: undefined }); // Reset exchange
    loadExchanges(val);
  };

  const handleSubmit = (values) => {
    onSubmit({ ...values, asset_class: assetClass });
  };

  return (
    <Card title={t('live.trading_session_config')}>
      {mode === 'live' && (
        <Alert
          message={t('live.live_trading_alert')}
          description={t('live.live_trading_alert_desc')}
          type="warning"
          showIcon
          style={{ marginBottom: 16 }}
        />
      )}

      <Form
        form={form}
        layout="vertical"
        onFinish={handleSubmit}
        initialValues={{
          asset_class: 'crypto',
          exchange: 'binance',
          mode: 'paper',
          timeframe: '1m',
          initial_cash: 10000,
          commission: 0.001
        }}
      >
        <Form.Item label={t('live.asset_class')} name="asset_class">
          <Radio.Group onChange={handleAssetChange} value={assetClass} buttonStyle="solid">
            <Radio.Button value="crypto">{t('live.asset_crypto')}</Radio.Button>
            <Radio.Button value="stock">{t('live.asset_stock')}</Radio.Button>
          </Radio.Group>
        </Form.Item>

        <Form.Item
          label={t('live.strategy')}
          name="strategy_name"
          rules={[{ required: true, message: t('live.select_strategy') }]}
        >
          <Select
            placeholder={t('live.select_strategy')}
            loading={loadingData}
            showSearch
            filterOption={(input, option) =>
              option.children.toLowerCase().includes(input.toLowerCase())
            }
          >
            {strategies.map((strategy) => (
              <Option key={strategy} value={strategy}>
                {strategy}
              </Option>
            ))}
          </Select>
        </Form.Item>

        <Form.Item
          label={t('live.symbol')}
          name="symbol"
          rules={[{ required: true, message: t('live.symbol_placeholder') }]}
          tooltip={t('live.symbol_tooltip')}
        >
          <Input placeholder={assetClass === 'crypto' ? "BTC/USDT" : "AAPL"} />
        </Form.Item>

        <Space style={{ width: '100%' }} size="large" wrap>
          <Form.Item
            label={t('live.exchange')}
            name="exchange"
            rules={[{ required: true, message: t('live.select_exchange') }]}
            style={{ minWidth: 150 }}
          >
            <Select>
              {exchanges.map((exchange) => (
                <Option key={exchange} value={exchange}>
                  {exchange.toUpperCase()}
                </Option>
              ))}
            </Select>
          </Form.Item>

          <Form.Item
            label={
              <span>
                {t('live.mode')}{' '}
                <Tooltip title={t('live.mode_tooltip')}>
                  <InfoCircleOutlined />
                </Tooltip>
              </span>
            }
            name="mode"
            rules={[{ required: true }]}
            style={{ minWidth: 120 }}
          >
            <Select onChange={setMode}>
              <Option value="paper">{t('live.mode_paper')}</Option>
              <Option value="live">{t('live.mode_live')}</Option>
            </Select>
          </Form.Item>

          <Form.Item
            label={t('live.timeframe')}
            name="timeframe"
            rules={[{ required: true }]}
            style={{ minWidth: 100 }}
          >
            <Select>
              <Option value="1m">1m</Option>
              <Option value="5m">5m</Option>
              <Option value="15m">15m</Option>
              <Option value="30m">30m</Option>
              <Option value="1h">1h</Option>
              <Option value="4h">4h</Option>
              <Option value="1d">1d</Option>
            </Select>
          </Form.Item>
        </Space>

        <Space style={{ width: '100%' }} size="large" wrap>
          <Form.Item
            label={t('live.initial_cash')}
            name="initial_cash"
            rules={[
              { required: true },
              { type: 'number', min: 100 }
            ]}
          >
            <InputNumber
              style={{ width: 150 }}
              min={100}
              step={1000}
              formatter={(value) => `$ ${value}`.replace(/\B(?=(\d{3})+(?!\d))/g, ',')}
              parser={(value) => value.replace(/\$\s?|(,*)/g, '')}
            />
          </Form.Item>

          <Form.Item
            label={
              <span>
                {t('live.commission')}{' '}
                <Tooltip title={t('live.commission_tooltip')}>
                  <InfoCircleOutlined />
                </Tooltip>
              </span>
            }
            name="commission"
            rules={[
              { required: true },
              { type: 'number', min: 0, max: 0.1 }
            ]}
          >
            <InputNumber
              style={{ width: 150 }}
              min={0}
              max={0.1}
              step={0.0001}
              formatter={(value) => `${(value * 100).toFixed(2)}%`}
              parser={(value) => parseFloat(value.replace('%', '')) / 100}
            />
          </Form.Item>
        </Space>

        <Form.Item>
          <Button
            type="primary"
            htmlType="submit"
            loading={loading}
            size="large"
            block
          >
            {t('live.start_session')}
          </Button>
        </Form.Item>
      </Form>
    </Card>
  );
};

export default LiveConfigForm;
