/**
 * Data Warmup Card Component
 * Form for preheating/warming up the data cache
 */
import { Card, Form, Input, DatePicker, Button, Alert, Typography } from 'antd';
import { FireOutlined } from '@ant-design/icons';
import { useTranslation } from 'react-i18next';
import dayjs from 'dayjs';

const { Paragraph } = Typography;
const { RangePicker } = DatePicker;

function WarmupCard({ onWarmup, loading, result }) {
    const { t } = useTranslation();
    const [form] = Form.useForm();

    const handleSubmit = async (values) => {
        const tickers = values.tickers.split(',').map(t => t.trim().toUpperCase()).filter(Boolean);
        await onWarmup({
            tickers,
            start_date: values.dateRange[0].format('YYYY-MM-DD'),
            end_date: values.dateRange[1].format('YYYY-MM-DD')
        });
    };

    return (
        <Card
            title={
                <span>
                    <FireOutlined className="card-icon warmup-icon" />
                    {t('datamanagement.warmup.title')}
                </span>
            }
            className="feature-card warmup-card"
        >
            <Paragraph type="secondary">
                {t('datamanagement.warmup.description')}
            </Paragraph>
            <Form
                form={form}
                layout="vertical"
                onFinish={handleSubmit}
                initialValues={{
                    dateRange: [dayjs().subtract(1, 'year'), dayjs()]
                }}
            >
                <Form.Item
                    name="tickers"
                    label={t('datamanagement.warmup.tickers_label')}
                    rules={[{ required: true }]}
                >
                    <Input.TextArea
                        placeholder={t('datamanagement.warmup.tickers_placeholder')}
                        rows={2}
                    />
                </Form.Item>
                <Form.Item
                    name="dateRange"
                    label={`${t('datamanagement.warmup.start_date')} - ${t('datamanagement.warmup.end_date')}`}
                    rules={[{ required: true }]}
                >
                    <RangePicker style={{ width: '100%' }} />
                </Form.Item>
                <Form.Item>
                    <Button
                        type="primary"
                        htmlType="submit"
                        loading={loading}
                        icon={<FireOutlined />}
                        block
                    >
                        {t('datamanagement.warmup.submit')}
                    </Button>
                </Form.Item>
            </Form>

            {result && (
                <Alert
                    type="success"
                    showIcon
                    message={`${result.success?.length || 0} succeeded, ${result.failed?.length || 0} failed`}
                    description={`Cache hit rate: ${((result.cache_hit_rate || 0) * 100).toFixed(1)}%`}
                />
            )}
        </Card>
    );
}

export default WarmupCard;
