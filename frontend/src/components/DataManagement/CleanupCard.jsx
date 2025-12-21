/**
 * Data Cleanup Card Component
 * Form for cleaning up cached data
 */
import {
    Card,
    Form,
    Input,
    DatePicker,
    InputNumber,
    Row,
    Col,
    Button,
    Popconfirm,
    Typography
} from 'antd';
import { DeleteOutlined } from '@ant-design/icons';
import { useTranslation } from 'react-i18next';

const { Paragraph } = Typography;

function CleanupCard({ onCleanup, loading }) {
    const { t } = useTranslation();
    const [form] = Form.useForm();

    const handleSubmit = async (values) => {
        const params = {};
        if (values.before_date) {
            params.before_date = values.before_date.format('YYYY-MM-DD');
        }
        if (values.older_than_days) {
            params.older_than_days = values.older_than_days;
        }
        if (values.tickers) {
            params.tickers = values.tickers;
        }

        await onCleanup(params);
        form.resetFields();
    };

    return (
        <Card
            title={
                <span>
                    <DeleteOutlined className="card-icon cleanup-icon" />
                    {t('datamanagement.cleanup.title')}
                </span>
            }
            className="feature-card cleanup-card"
        >
            <Paragraph type="secondary">
                {t('datamanagement.cleanup.description')}
            </Paragraph>
            <Form
                form={form}
                layout="vertical"
                onFinish={handleSubmit}
            >
                <Row gutter={16}>
                    <Col span={12}>
                        <Form.Item
                            name="before_date"
                            label={t('datamanagement.cleanup.before_date')}
                        >
                            <DatePicker style={{ width: '100%' }} />
                        </Form.Item>
                    </Col>
                    <Col span={12}>
                        <Form.Item
                            name="older_than_days"
                            label={t('datamanagement.cleanup.older_than_days')}
                        >
                            <InputNumber min={1} style={{ width: '100%' }} />
                        </Form.Item>
                    </Col>
                </Row>
                <Form.Item
                    name="tickers"
                    label={t('datamanagement.cleanup.tickers_filter')}
                >
                    <Input placeholder="AAPL, MSFT (optional)" />
                </Form.Item>
                <Form.Item>
                    <Popconfirm
                        title={t('datamanagement.cleanup.confirm_title')}
                        description={t('datamanagement.cleanup.confirm_message')}
                        onConfirm={form.submit}
                        okText={t('common.confirm')}
                        cancelText={t('common.cancel')}
                    >
                        <Button
                            danger
                            loading={loading}
                            icon={<DeleteOutlined />}
                            block
                        >
                            {t('datamanagement.cleanup.submit')}
                        </Button>
                    </Popconfirm>
                </Form.Item>
            </Form>
        </Card>
    );
}

export default CleanupCard;
