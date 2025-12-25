import { Space, Input, Select, DatePicker, Button, Segmented } from 'antd';
import { ReloadOutlined, FilterOutlined, FundOutlined, PieChartOutlined } from '@ant-design/icons';
import dayjs from 'dayjs';

const { RangePicker } = DatePicker;

/**
 * Filter bar component for BacktestHistory page
 * 
 * Provides UI for switching between strategy/portfolio views and
 * filtering by ticker, strategy name, and date range.
 */
function FilterBar({
    t, recordType, onRecordTypeChange, ticker, setTicker, strategyName, setStrategyName,
    dateRange, setDateRange, strategies, onFilter, onReset
}) {
    return (
        <div className="card" style={{ marginBottom: '1rem', padding: '1rem' }}>
            <Space wrap style={{ width: '100%', justifyContent: 'space-between' }}>
                <Segmented
                    options={[
                        {
                            label: (
                                <Space>
                                    <FundOutlined />
                                    {t('history.type_strategy')}
                                </Space>
                            ),
                            value: 'strategy'
                        },
                        {
                            label: (
                                <Space>
                                    <PieChartOutlined />
                                    {t('history.type_portfolio')}
                                </Space>
                            ),
                            value: 'portfolio'
                        }
                    ]}
                    value={recordType}
                    onChange={onRecordTypeChange}
                />

                {recordType === 'strategy' && (
                    <Space wrap>
                        <Input
                            placeholder={t('history.filter_ticker')}
                            value={ticker}
                            onChange={(e) => setTicker(e.target.value || null)}
                            style={{ width: 120 }}
                            allowClear
                        />
                        <Select
                            placeholder={t('history.filter_strategy')}
                            value={strategyName}
                            onChange={setStrategyName}
                            style={{ width: 200 }}
                            allowClear
                        >
                            {strategies.map(name => (
                                <Select.Option key={name} value={name}>{name}</Select.Option>
                            ))}
                        </Select>
                        <RangePicker
                            value={dateRange ? [dayjs(dateRange[0]), dayjs(dateRange[1])] : null}
                            onChange={(dates) => setDateRange(dates ? [dates[0].format('YYYY-MM-DD'), dates[1].format('YYYY-MM-DD')] : null)}
                            placeholder={[t('history.start_date'), t('history.end_date')]}
                        />
                        <Button
                            type="primary"
                            icon={<FilterOutlined />}
                            onClick={onFilter}
                        >
                            {t('common.filter')}
                        </Button>
                    </Space>
                )}

                <Button
                    icon={<ReloadOutlined />}
                    onClick={onReset}
                >
                    {t('common.reset')}
                </Button>
            </Space>
        </div>
    );
}

export default FilterBar;
