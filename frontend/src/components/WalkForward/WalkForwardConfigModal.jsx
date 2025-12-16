import React, { useState, useEffect } from 'react'
import { useTranslation } from 'react-i18next'
import {
    Modal,
    Form,
    Input,
    Select,
    InputNumber,
    DatePicker,
    Switch,
    Row,
    Col,
    Button,
    Space,
    Divider,
    Tooltip,
    Typography,
    message
} from 'antd'
import { PlusOutlined, MinusCircleOutlined, QuestionCircleOutlined } from '@ant-design/icons'
import dayjs from 'dayjs'
import { api } from '../../services/api'

const { Option } = Select
const { RangePicker } = DatePicker
const { Text } = Typography

const WalkForwardConfigModal = ({ visible, onCancel, onSubmit }) => {
    const { t } = useTranslation()
    const [form] = Form.useForm()
    const [strategies, setStrategies] = useState([])
    const [loading, setLoading] = useState(false)
    const [paramFields, setParamFields] = useState([{ name: '', values: '' }])

    useEffect(() => {
        if (visible) {
            loadStrategies()
            form.resetFields()
            setParamFields([{ name: '', values: '' }])
        }
    }, [visible])

    const loadStrategies = async () => {
        try {
            const data = await api.getStrategies()
            setStrategies(data)
        } catch (error) {
            message.error(t('walkforward.config.loadStrategiesError'))
        }
    }

    const handleSubmit = async () => {
        try {
            const values = await form.validateFields()
            setLoading(true)

            // Transform param fields to param_grid
            const param_grid = {}
            values.parameters.forEach(param => {
                if (param.name && param.values) {
                    // Parse comma-separated values
                    const valuesList = param.values.split(',').map(v => {
                        const trimmed = v.trim()
                        // Try to parse as number
                        const num = Number(trimmed)
                        return isNaN(num) ? trimmed : num
                    })
                    param_grid[param.name] = valuesList
                }
            })

            if (Object.keys(param_grid).length === 0) {
                message.error(t('walkforward.config.noParametersError'))
                setLoading(false)
                return
            }

            const payload = {
                strategy_name: values.strategy_name,
                ticker: values.ticker,
                start_date: values.date_range[0].format('YYYY-MM-DD'),
                end_date: values.date_range[1].format('YYYY-MM-DD'),
                param_grid,
                train_period_days: values.train_period_days,
                test_period_days: values.test_period_days,
                anchored: values.anchored,
                optimization_metric: values.optimization_metric,
                initial_cash: values.initial_cash,
                commission: values.commission,
                stake: values.stake
            }

            await onSubmit(payload)
            setLoading(false)
        } catch (error) {
            setLoading(false)
            console.error('Validation failed:', error)
        }
    }

    return (
        <Modal
            title={t('walkforward.config.title')}
            open={visible}
            onCancel={onCancel}
            onOk={handleSubmit}
            confirmLoading={loading}
            width={800}
            okText={t('walkforward.config.start')}
            cancelText={t('walkforward.config.cancel')}
        >
            <Form
                form={form}
                layout="vertical"
                initialValues={{
                    ticker: 'AAPL',
                    date_range: [dayjs().subtract(3, 'year'), dayjs()],
                    train_period_days: 365,
                    test_period_days: 90,
                    anchored: false,
                    optimization_metric: 'sharpe_ratio',
                    initial_cash: 100000,
                    commission: 0.0005,
                    stake: 100,
                    parameters: [{ name: '', values: '' }]
                }}
            >
                <Row gutter={16}>
                    <Col span={12}>
                        <Form.Item
                            label={t('walkforward.config.strategy')}
                            name="strategy_name"
                            rules={[{ required: true, message: t('walkforward.config.strategyRequired') }]}
                        >
                            <Select placeholder={t('walkforward.config.selectStrategy')}>
                                {strategies.map(s => (
                                    <Option key={s} value={s}>{s}</Option>
                                ))}
                            </Select>
                        </Form.Item>
                    </Col>
                    <Col span={12}>
                        <Form.Item
                            label={t('walkforward.config.ticker')}
                            name="ticker"
                            rules={[{ required: true, message: t('walkforward.config.tickerRequired') }]}
                        >
                            <Input placeholder="AAPL" />
                        </Form.Item>
                    </Col>
                </Row>

                <Form.Item
                    label={t('walkforward.config.dateRange')}
                    name="date_range"
                    rules={[{ required: true, message: t('walkforward.config.dateRangeRequired') }]}
                >
                    <RangePicker style={{ width: '100%' }} />
                </Form.Item>

                <Divider>{t('walkforward.config.windowSettings')}</Divider>

                <Row gutter={16}>
                    <Col span={12}>
                        <Form.Item
                            label={
                                <Space>
                                    {t('walkforward.config.trainPeriod')}
                                    <Tooltip title={t('walkforward.config.trainPeriodTooltip')}>
                                        <QuestionCircleOutlined />
                                    </Tooltip>
                                </Space>
                            }
                            name="train_period_days"
                            rules={[{ required: true }]}
                        >
                            <InputNumber min={30} max={1825} addonAfter={t('walkforward.config.days')} style={{ width: '100%' }} />
                        </Form.Item>
                    </Col>
                    <Col span={12}>
                        <Form.Item
                            label={
                                <Space>
                                    {t('walkforward.config.testPeriod')}
                                    <Tooltip title={t('walkforward.config.testPeriodTooltip')}>
                                        <QuestionCircleOutlined />
                                    </Tooltip>
                                </Space>
                            }
                            name="test_period_days"
                            rules={[{ required: true }]}
                        >
                            <InputNumber min={7} max={365} addonAfter={t('walkforward.config.days')} style={{ width: '100%' }} />
                        </Form.Item>
                    </Col>
                </Row>

                <Form.Item
                    label={
                        <Space>
                            {t('walkforward.config.anchored')}
                            <Tooltip title={t('walkforward.config.anchoredTooltip')}>
                                <QuestionCircleOutlined />
                            </Tooltip>
                        </Space>
                    }
                    name="anchored"
                    valuePropName="checked"
                >
                    <Switch
                        checkedChildren={t('walkforward.config.anchoredYes')}
                        unCheckedChildren={t('walkforward.config.anchoredNo')}
                    />
                </Form.Item>

                <Divider>{t('walkforward.config.parameterGrid')}</Divider>

                <Form.List name="parameters">
                    {(fields, { add, remove }) => (
                        <>
                            {fields.map(({ key, name, ...restField }) => (
                                <Row key={key} gutter={8} align="middle">
                                    <Col span={10}>
                                        <Form.Item
                                            {...restField}
                                            name={[name, 'name']}
                                            rules={[{ required: true, message: t('walkforward.config.paramNameRequired') }]}
                                        >
                                            <Input placeholder={t('walkforward.config.paramName')} />
                                        </Form.Item>
                                    </Col>
                                    <Col span={12}>
                                        <Form.Item
                                            {...restField}
                                            name={[name, 'values']}
                                            rules={[{ required: true, message: t('walkforward.config.paramValuesRequired') }]}
                                        >
                                            <Input placeholder={t('walkforward.config.paramValuesPlaceholder')} />
                                        </Form.Item>
                                    </Col>
                                    <Col span={2}>
                                        {fields.length > 1 && (
                                            <MinusCircleOutlined onClick={() => remove(name)} />
                                        )}
                                    </Col>
                                </Row>
                            ))}
                            <Form.Item>
                                <Button type="dashed" onClick={() => add()} block icon={<PlusOutlined />}>
                                    {t('walkforward.config.addParameter')}
                                </Button>
                            </Form.Item>
                        </>
                    )}
                </Form.List>

                <Text type="secondary">
                    {t('walkforward.config.parameterExample')}
                </Text>

                <Divider>{t('walkforward.config.optimizationSettings')}</Divider>

                <Form.Item
                    label={t('walkforward.config.optimizationMetric')}
                    name="optimization_metric"
                    rules={[{ required: true }]}
                >
                    <Select>
                        <Option value="sharpe_ratio">{t('walkforward.config.sharpeRatio')}</Option>
                        <Option value="total_return">{t('walkforward.config.totalReturn')}</Option>
                        <Option value="profit_factor">{t('walkforward.config.profitFactor')}</Option>
                    </Select>
                </Form.Item>

                <Divider>{t('walkforward.config.backtestSettings')}</Divider>

                <Row gutter={16}>
                    <Col span={8}>
                        <Form.Item label={t('walkforward.config.initialCash')} name="initial_cash">
                            <InputNumber min={1000} max={10000000} style={{ width: '100%' }} />
                        </Form.Item>
                    </Col>
                    <Col span={8}>
                        <Form.Item label={t('walkforward.config.commission')} name="commission">
                            <InputNumber min={0} max={0.01} step={0.0001} style={{ width: '100%' }} />
                        </Form.Item>
                    </Col>
                    <Col span={8}>
                        <Form.Item label={t('walkforward.config.stake')} name="stake">
                            <InputNumber min={1} max={10000} style={{ width: '100%' }} />
                        </Form.Item>
                    </Col>
                </Row>
            </Form>
        </Modal>
    )
}

export default WalkForwardConfigModal
