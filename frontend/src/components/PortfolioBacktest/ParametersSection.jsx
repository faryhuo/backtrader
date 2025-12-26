import { DatePicker, Select, InputNumber } from 'antd';
import PropTypes from 'prop-types';

const SIZER_OPTIONS = [
    { value: 'fixed_size', label: 'Fixed Size' },
    { value: 'percent_sizer', label: 'Percent Sizer' },
    { value: 'all_in_sizer', label: 'All In' },
    { value: 'risk_sizer', label: 'Risk Control' },
    { value: 'kelly_sizer', label: 'Kelly Criterion' },
];

const TIMEFRAME_OPTIONS = [
    { value: '1d', label: 'Daily' },
    { value: '1h', label: 'Hourly' },
    { value: '15m', label: '15 Min' },
    { value: '5m', label: '5 Min' },
    { value: '1m', label: '1 Min' },
];

/**
 * Parameters section for date range, strategy, cash, commission, sizer, timeframe
 */
function ParametersSection({
    t, dateRange, setDateRange, strategies, selectedStrategy, setSelectedStrategy,
    initialCash, setInitialCash, commission, setCommission, stake, setStake,
    sizerType, setSizerType, sizerConfig, setSizerConfig, timeframe, setTimeframe
}) {
    const updateSizerConfig = (key, value) => {
        setSizerConfig(prev => ({ ...prev, [key]: value }));
    };

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
            <div className="param-group">
                <label>{t('config_form.sizer_type', 'Position Sizing')}</label>
                <Select
                    value={sizerType}
                    onChange={setSizerType}
                    style={{ width: 200 }}
                    options={SIZER_OPTIONS.map(opt => ({
                        value: opt.value,
                        label: t(`sizer.${opt.value}`, opt.label)
                    }))}
                />
            </div>

            {sizerType === 'fixed_size' && (
                <div className="param-group">
                    <label>{t('config_form.order_size', 'Order Size')}</label>
                    <InputNumber
                        value={stake}
                        onChange={setStake}
                        min={1}
                        step={10}
                    />
                </div>
            )}

            {sizerType === 'percent_sizer' && (

                <div className="param-group">
                    <label>{t('config_form.sizer_percent', 'Position %')}</label>
                    <InputNumber
                        value={sizerConfig.percents || 10}
                        onChange={(v) => updateSizerConfig('percents', v)}
                        min={0.1}
                        max={100}
                        step={0.5}
                        formatter={v => `${v}%`}
                        parser={v => v.replace('%', '')}
                    />
                </div>
            )}

            {(sizerType === 'risk_sizer' || sizerType === 'kelly_sizer') && (
                <div className="param-group">
                    <label>{t('config_form.sizer_risk', 'Risk per Trade %')}</label>
                    <InputNumber
                        value={sizerConfig.risk_percent || 2}
                        onChange={(v) => updateSizerConfig('risk_percent', v)}
                        min={0.1}
                        max={100}
                        step={0.5}
                        formatter={v => `${v}%`}
                        parser={v => v.replace('%', '')}
                    />
                </div>
            )}

            <div className="param-group">
                <label>{t('config_form.timeframe', 'Data Interval')}</label>
                <Select
                    value={timeframe}
                    onChange={setTimeframe}
                    style={{ width: 200 }}
                    options={TIMEFRAME_OPTIONS.map(opt => ({
                        value: opt.value,
                        label: t(`timeframe.${opt.value}`, opt.label)
                    }))}
                />
            </div>
        </div>
    );
}

ParametersSection.propTypes = {
    t: PropTypes.func.isRequired,
    dateRange: PropTypes.array,
    setDateRange: PropTypes.func.isRequired,
    strategies: PropTypes.array.isRequired,
    selectedStrategy: PropTypes.string,
    setSelectedStrategy: PropTypes.func.isRequired,
    initialCash: PropTypes.number.isRequired,
    setInitialCash: PropTypes.func.isRequired,
    commission: PropTypes.number.isRequired,
    setCommission: PropTypes.func.isRequired,
    stake: PropTypes.number,
    setStake: PropTypes.func.isRequired,
    sizerType: PropTypes.string,
    setSizerType: PropTypes.func.isRequired,
    sizerConfig: PropTypes.object,
    setSizerConfig: PropTypes.func.isRequired,
    timeframe: PropTypes.string,
    setTimeframe: PropTypes.func.isRequired,
};

export default ParametersSection;

