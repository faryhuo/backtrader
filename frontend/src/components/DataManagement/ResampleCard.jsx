/**
 * Data Resample Card Component
 * Form for resampling OHLCV data to different timeframes
 */
import {
    Card,
    Form,
    Input,
    DatePicker,
    Select,
    Row,
    Col,
    Button,
    Alert,
    Divider,
    Typography,
    Tooltip
} from 'antd';
import { SyncOutlined, InfoCircleOutlined } from '@ant-design/icons';
import { useTranslation } from 'react-i18next';
import dayjs from 'dayjs';

const { Paragraph, Text } = Typography;
const { RangePicker } = DatePicker;

function ResampleCard({ onResample, loading, result, timeframes }) {
    const { t } = useTranslation();
    const [form] = Form.useForm();

    const handleSubmit = async (values) => {
        await onResample({
            ticker: values.ticker.toUpperCase(),
            start_date: values.dateRange[0].format('YYYY-MM-DD'),
            end_date: values.dateRange[1].format('YYYY-MM-DD'),
            target_timeframe: values.target_timeframe,
            include_incomplete: values.include_incomplete || false
        });
    };

    return (
        <Card
            title={
                <span>
                    <SyncOutlined className="card-icon resample-icon" />
                    {t('datamanagement.resample.title')}
                </span>
            }
            className="feature-card resample-card"
            style={{ marginTop: 16 }}
        >
            <Paragraph type="secondary">
                {t('datamanagement.resample.description')}
            </Paragraph>
            <Form
                form={form}
                layout="vertical"
                onFinish={handleSubmit}
                initialValues={{
                    dateRange: [dayjs().subtract(1, 'month'), dayjs()],
                    target_timeframe: '1d'
                }}
            >
                <Form.Item
                    name="ticker"
                    label={t('datamanagement.resample.ticker_label')}
                    rules={[{ required: true }]}
                >
                    <Input placeholder="AAPL" />
                </Form.Item>
                <Form.Item
                    name="dateRange"
                    label={`${t('datamanagement.resample.start_date')} - ${t('datamanagement.resample.end_date')}`}
                    rules={[{ required: true }]}
                >
                    <RangePicker style={{ width: '100%' }} />
                </Form.Item>
                <Row gutter={16}>
                    <Col span={16}>
                        <Form.Item
                            name="target_timeframe"
                            label={t('datamanagement.resample.target_timeframe')}
                            rules={[{ required: true }]}
                        >
                            <Select>
                                {timeframes.map(tf => (
                                    <Select.Option key={tf} value={tf}>
                                        {t(`datamanagement.timeframes.${tf}`, tf)}
                                    </Select.Option>
                                ))}
                            </Select>
                        </Form.Item>
                    </Col>
                    <Col span={8}>
                        <Form.Item
                            name="include_incomplete"
                            label={
                                <Tooltip title={t('datamanagement.resample.include_incomplete')}>
                                    <span>Incomplete <InfoCircleOutlined /></span>
                                </Tooltip>
                            }
                            valuePropName="checked"
                        >
                            <Select defaultValue={false}>
                                <Select.Option value={false}>No</Select.Option>
                                <Select.Option value={true}>Yes</Select.Option>
                            </Select>
                        </Form.Item>
                    </Col>
                </Row>
                <Form.Item>
                    <Button
                        type="primary"
                        htmlType="submit"
                        loading={loading}
                        icon={<SyncOutlined />}
                        block
                    >
                        {t('datamanagement.resample.submit')}
                    </Button>
                </Form.Item>
            </Form>

            {result && (
                <Alert
                    type="success"
                    showIcon
                    message={t('datamanagement.resample.result_count', { count: result.record_count })}
                    description={`Timeframe: ${result.timeframe}`}
                />
            )}

            <Divider />
            <div className="strategy-info">
                <Text strong><InfoCircleOutlined /> {t('datamanagement.resample.strategy.title')}</Text>
                <ul>
                    <li>{t('datamanagement.resample.strategy.open')}</li>
                    <li>{t('datamanagement.resample.strategy.high')}</li>
                    <li>{t('datamanagement.resample.strategy.low')}</li>
                    <li>{t('datamanagement.resample.strategy.close')}</li>
                    <li>{t('datamanagement.resample.strategy.volume')}</li>
                    <li>{t('datamanagement.resample.strategy.boundary')}</li>
                </ul>
            </div>
        </Card>
    );
}

export default ResampleCard;
