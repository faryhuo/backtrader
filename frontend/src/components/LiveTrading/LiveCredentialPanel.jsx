import { Alert, Button, Card, Col, Input, Row, Space, Tabs, Typography } from 'antd';
import { ApiOutlined, LinkOutlined, SaveOutlined } from '@ant-design/icons';
import { useTranslation } from 'react-i18next';

const { Text } = Typography;

export default function LiveCredentialPanel({
  paperCredentials,
  liveCredentials,
  paperTestUrl,
  loading = false,
  testingKey = null,
  onCredentialChange,
  onPaperTestUrlChange,
  onSaveCredentials,
  onTestCredentials,
  onSavePaperTestUrl,
}) {
  const { t } = useTranslation();

  const renderCredentialFields = (mode, values) => (
    <Space direction="vertical" size="middle" style={{ width: '100%' }}>
      <Alert
        type={mode === 'live' ? 'warning' : 'info'}
        showIcon
        message={
          mode === 'live'
            ? t('live.config.live_hint', 'Live credentials will be used for real-money execution.')
            : t('live.config.paper_hint', 'Paper credentials should point to your Binance testnet account.')
        }
      />

      <Row gutter={[16, 16]}>
        <Col xs={24} md={12}>
          <Text>{t('live.config.api_key', 'API Key')}</Text>
          <Input.Password
            value={values?.api_key || ''}
            onChange={(event) => onCredentialChange(mode, 'api_key', event.target.value)}
            placeholder={t('live.config.api_key_placeholder', 'Enter API Key')}
            disabled={loading}
          />
        </Col>
        <Col xs={24} md={12}>
          <Text>{t('live.config.secret', 'Secret')}</Text>
          <Input.Password
            value={values?.secret || ''}
            onChange={(event) => onCredentialChange(mode, 'secret', event.target.value)}
            placeholder={t('live.config.secret_placeholder', 'Enter Secret')}
            disabled={loading}
          />
        </Col>
      </Row>

      {mode === 'paper' ? (
        <div>
          <Text>{t('live.config.paper_test_url', 'Paper Test URL')}</Text>
          <Input
            value={paperTestUrl || ''}
            onChange={(event) => onPaperTestUrlChange(event.target.value)}
            placeholder="https://testnet.binance.vision"
            prefix={<LinkOutlined />}
            disabled={loading}
          />
        </div>
      ) : null}

      <Space wrap>
        <Button
          type="primary"
          icon={<SaveOutlined />}
          onClick={() => onSaveCredentials(mode)}
          loading={loading}
        >
          {t('live.config.save_credentials', 'Save Credentials')}
        </Button>
        <Button
          onClick={() => onTestCredentials(mode)}
          loading={testingKey === mode}
        >
          {t('live.config.test_connection', 'Test Connection')}
        </Button>
        {mode === 'paper' ? (
          <Button
            icon={<ApiOutlined />}
            onClick={onSavePaperTestUrl}
            loading={loading}
          >
            {t('live.config.save_test_url', 'Save Test URL')}
          </Button>
        ) : null}
      </Space>
    </Space>
  );

  return (
    <Card
      className="dashboard-panel"
      bordered={false}
      title={t('live.config.title', 'Trading Access')}
      extra={<Text type="secondary">{t('live.config.subtitle', 'Configure exchange keys and the paper endpoint before launching.')}</Text>}
    >
      <Tabs
        defaultActiveKey="paper"
        items={[
          {
            key: 'paper',
            label: t('live.form.paper_mode', 'Paper (Testnet)'),
            children: renderCredentialFields('paper', paperCredentials),
          },
          {
            key: 'live',
            label: t('live.form.live_mode', 'Live (Real Money)'),
            children: renderCredentialFields('live', liveCredentials),
          },
        ]}
      />
    </Card>
  );
}
