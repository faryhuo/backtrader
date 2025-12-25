import { DatePicker, Select, InputNumber } from 'antd';

/**
 * Parameters section for date range, strategy, cash, commission
 */
function ParametersSection({
    t, dateRange, setDateRange, strategies, selectedStrategy, setSelectedStrategy,
    initialCash, setInitialCash, commission, setCommission
}) {
    return (
        <div className="params-section">
            <div className="param-group">
                <label>{t('portfolio.date_range', 'Date Range')}</label>
                <DatePicker.RangePicker
                    value={dateRange}
                    onChange={setDateRange}
                    format="YYYY-MM-DD"
                />
            </div>
            <div className="param-group">
                <label>{t('portfolio.strategy', 'Strategy')}</label>
                <Select
                    value={selectedStrategy}
                    onChange={setSelectedStrategy}
                    style={{ width: 200 }}
                    options={strategies.map(s => ({ value: s, label: s }))}
                />
            </div>
            <div className="param-group">
                <label>{t('portfolio.initial_cash', 'Initial Cash')}</label>
                <InputNumber
                    value={initialCash}
                    onChange={setInitialCash}
                    min={1000}
                    step={10000}
                    formatter={v => `$ ${v}`.replace(/\B(?=(\d{3})+(?!\d))/g, ',')}
                    parser={v => v.replace(/\$\s?|(,*)/g, '')}
                />
            </div>
            <div className="param-group">
                <label>{t('portfolio.commission', 'Commission')}</label>
                <InputNumber
                    value={commission}
                    onChange={setCommission}
                    min={0}
                    max={0.1}
                    step={0.0001}
                    formatter={v => `${(v * 100).toFixed(2)}%`}
                    parser={v => parseFloat(v.replace('%', '')) / 100}
                />
            </div>
        </div>
    );
}

export default ParametersSection;
