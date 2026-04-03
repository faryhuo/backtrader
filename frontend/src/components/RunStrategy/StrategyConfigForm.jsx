import { useEffect, useState } from 'react';
import PropTypes from 'prop-types';
import { useTranslation } from 'react-i18next';
import {
    CalendarOutlined,
    DollarOutlined,
    PercentageOutlined,
    NumberOutlined,
    SyncOutlined,
    RocketOutlined,
    SettingOutlined,
    DownOutlined,
    RightOutlined,
    ExpandAltOutlined,
    ShrinkOutlined,
    PieChartOutlined,
    ClockCircleOutlined,
    InfoCircleOutlined,
    SearchOutlined,
} from '@ant-design/icons';
import { Alert, AutoComplete, Collapse, Input, Tooltip } from 'antd';
import { marketDataApi } from '../../services/marketDataApi';
import {
    formatStrategyError,
    shouldShowStrategyErrorDetail,
} from '../../utils/strategyErrorFormatter';

// Sizer type options
const SIZER_OPTIONS = [
    { value: 'fixed_size', label: 'Fixed Size' },
    { value: 'percent_sizer', label: 'Percent Sizer' },
    { value: 'all_in_sizer', label: 'All In' },
    { value: 'risk_sizer', label: 'Risk Control' },
    { value: 'kelly_sizer', label: 'Kelly Criterion' },
];

// Timeframe options
const TIMEFRAME_OPTIONS = [
    { value: '1d', label: 'Daily' },
    { value: '1h', label: 'Hourly' },
    { value: '15m', label: '15 Min' },
    { value: '5m', label: '5 Min' },
    { value: '1m', label: '1 Min' },
];

const DATA_SOURCE_OPTIONS = [
    { value: 'yahoo', labelKey: 'config_form.platform_yahoo', fallback: 'Yahoo Finance' },
    { value: 'eodhd', labelKey: 'config_form.platform_eodhd', fallback: 'EODHD' },
];

const INSTRUMENT_TYPE_OPTIONS = [
    { value: 'stock', labelKey: 'config_form.instrument_type_stock', fallback: 'Stock' },
    { value: 'etf', labelKey: 'config_form.instrument_type_etf', fallback: 'ETF' },
    { value: 'index', labelKey: 'config_form.instrument_type_index', fallback: 'Index' },
    { value: 'forex', labelKey: 'config_form.instrument_type_forex', fallback: 'Forex' },
    { value: 'crypto', labelKey: 'config_form.instrument_type_crypto', fallback: 'Crypto' },
    { value: 'futures', labelKey: 'config_form.instrument_type_futures', fallback: 'Futures' },
    { value: 'fund', labelKey: 'config_form.instrument_type_fund', fallback: 'Fund' },
];

function StrategyConfigForm({
    strategies,
    selectedStrategy,
    setSelectedStrategy,
    fetchStrategies,
    ticker,
    setTicker,
    dataSource,
    setDataSource,
    instrumentType,
    setInstrumentType,
    startDate,
    setStartDate,
    endDate,
    setEndDate,
    initialCash,
    setInitialCash,
    commission,
    setCommission,
    stake,
    setStake,
    sizerType = 'fixed_size',
    setSizerType = () => { },
    sizerConfig = {},
    setSizerConfig = () => { },
    timeframe = '1d',
    setTimeframe = () => { },
    loading,
    onSubmit,
    error,
    strategyParams = [],
    paramOverrides = {},
    onParamChange = () => { }
}) {
    const { t } = useTranslation();
    const [paramsExpanded, setParamsExpanded] = useState(true);
    const [isFormCollapsed, setIsFormCollapsed] = useState(false);
    const [instrumentOptions, setInstrumentOptions] = useState([]);
    const [instrumentExamples, setInstrumentExamples] = useState([]);
    const formattedError = error ? formatStrategyError(error, t) : null;
    const showTechnicalDetail = shouldShowStrategyErrorDetail(formattedError);
    const autoCompleteOptions = instrumentOptions.map((option) => ({
        value: option.code,
        label: (
            <div className="instrument-option">
                <span className="instrument-option-code">{option.code}</span>
                <span className="instrument-option-label">{option.label || option.code}</span>
            </div>
        ),
    }));

    useEffect(() => {
        let cancelled = false;

        async function loadCatalog() {
            try {
                const catalog = await marketDataApi.getInstrumentCatalog({
                    platform: dataSource,
                    instrumentType,
                    query: ticker,
                    limit: 20,
                });
                if (cancelled) return;
                setInstrumentOptions(catalog.options || []);
                setInstrumentExamples(catalog.examples || []);
            } catch {
                if (cancelled) return;
                setInstrumentOptions([]);
                setInstrumentExamples([]);
            }
        }

        loadCatalog();
        return () => {
            cancelled = true;
        };
    }, [dataSource, instrumentType, ticker]);

    // Handle sizer config changes
    const updateSizerConfig = (key, value) => {
        setSizerConfig(prev => ({ ...prev, [key]: value }));
    };

    return (
        <section className="card form-card-enhanced">
            <div className="strategy-form-header">
                <h2 style={{ margin: 0 }}><RocketOutlined /> {t('config_form.title')}</h2>
                <button
                    type="button"
                    className="icon-btn"
                    style={{ width: '32px', height: '32px', border: 'none', background: 'transparent' }}
                    title={isFormCollapsed ? t('common.expand', 'Expand') : t('common.collapse', 'Collapse')}
                    onClick={() => setIsFormCollapsed(!isFormCollapsed)}
                >
                    {isFormCollapsed ? <ExpandAltOutlined style={{ fontSize: '1.2rem', color: '#94a3b8' }} /> : <ShrinkOutlined style={{ fontSize: '1.2rem', color: '#94a3b8' }} />}
                </button>
            </div>
            {!isFormCollapsed && (
                <form onSubmit={onSubmit}>
                    <div className="form-grid">
                        <div className="form-group strategy-select-group form-col-span-2">
                            <label htmlFor="strategy-select">{t('config_form.strategy')}</label>
                            <div className="strategy-input-wrapper">
                                <select
                                    id="strategy-select"
                                    value={selectedStrategy}
                                    onChange={(e) => setSelectedStrategy(e.target.value)}
                                    className="styled-select"
                                >
                                    {strategies.map((s) => (
                                        <option key={s} value={s}>{s}</option>
                                    ))}
                                </select>
                                <button
                                    type="button"
                                    className="icon-btn"
                                    onClick={fetchStrategies}
                                    title={t('config_form.refresh')}
                                >
                                    <SyncOutlined />
                                </button>
                            </div>
                        </div>

                        <div className="form-group form-col-span-2">
                            <label htmlFor="data-source">{t('config_form.data_source', 'Data Platform')}</label>
                            <select
                                id="data-source"
                                value={dataSource}
                                onChange={(e) => setDataSource(e.target.value)}
                                className="styled-select"
                            >
                                {DATA_SOURCE_OPTIONS.map((opt) => (
                                    <option key={opt.value} value={opt.value}>
                                        {t(opt.labelKey, opt.fallback)}
                                    </option>
                                ))}
                            </select>
                        </div>

                        <div className="form-group form-col-span-2">
                            <label htmlFor="instrument-type">{t('config_form.instrument_type', 'Instrument Type')}</label>
                            <select
                                id="instrument-type"
                                value={instrumentType}
                                onChange={(e) => setInstrumentType(e.target.value)}
                                className="styled-select"
                            >
                                {INSTRUMENT_TYPE_OPTIONS.map((opt) => (
                                    <option key={opt.value} value={opt.value}>
                                        {t(opt.labelKey, opt.fallback)}
                                    </option>
                                ))}
                            </select>
                        </div>

                        <div className="form-group form-col-span-2">
                            <label htmlFor="ticker">{t('config_form.instrument_code', 'Instrument Code')}</label>
                            <div className="instrument-search-wrapper">
                                <AutoComplete
                                    id="ticker"
                                    popupClassName="instrument-autocomplete-dropdown"
                                    className="instrument-autocomplete"
                                    options={autoCompleteOptions}
                                    value={ticker}
                                    filterOption={false}
                                    allowClear
                                    onChange={(value) => setTicker(String(value || '').toUpperCase())}
                                    onSelect={(value) => setTicker(String(value || '').toUpperCase())}
                                    placeholder={
                                        instrumentExamples.length > 0
                                            ? instrumentExamples.join(', ')
                                            : t('config_form.instrument_code_placeholder', 'Search instrument code')
                                    }
                                >
                                    <Input.Search
                                        className="instrument-search-input"
                                        required
                                        allowClear
                                        enterButton={false}
                                        prefix={<SearchOutlined />}
                                    />
                                </AutoComplete>
                            </div>
                            {instrumentExamples.length > 0 && (
                                <div className="field-hint">
                                    {t('config_form.instrument_examples', 'Examples')}: {instrumentExamples.join(', ')}
                                </div>
                            )}
                        </div>

                        <div className="form-group form-col-span-2">
                            <label htmlFor="start-date">{t('config_form.start_date')}</label>
                            <div className="input-with-icon">
                                <CalendarOutlined className="input-icon" />
                                <input
                                    id="start-date"
                                    type="date"
                                    value={startDate}
                                    onChange={(e) => setStartDate(e.target.value)}
                                    required
                                />
                            </div>
                        </div>

                        <div className="form-group form-col-span-2">
                            <label htmlFor="end-date">{t('config_form.end_date')}</label>
                            <div className="input-with-icon">
                                <CalendarOutlined className="input-icon" />
                                <input
                                    id="end-date"
                                    type="date"
                                    value={endDate}
                                    onChange={(e) => setEndDate(e.target.value)}
                                    required
                                />
                            </div>
                        </div>

                        <div className="form-group form-col-span-2">
                            <label htmlFor="initial-cash">{t('config_form.initial_capital')}</label>
                            <div className="input-with-icon">
                                <DollarOutlined className="input-icon" />
                                <input
                                    id="initial-cash"
                                    type="number"
                                    value={initialCash}
                                    onChange={(e) => setInitialCash(e.target.value)}
                                    required
                                />
                            </div>
                        </div>

                        <div className="form-group form-col-span-2">
                            <label htmlFor="commission">{t('config_form.commission')}</label>
                            <div className="input-with-icon">
                                <PercentageOutlined className="input-icon" />
                                <input
                                    id="commission"
                                    type="number"
                                    step="0.0001"
                                    value={commission}
                                    onChange={(e) => setCommission(e.target.value)}
                                    required
                                />
                            </div>
                        </div>

                        {/* Sizer Type Selector - First */}
                        <div className="form-group form-col-span-2">
                            <label htmlFor="sizer-type">
                                <PieChartOutlined /> {t('config_form.sizer_type', 'Position Sizing')}
                                <Tooltip title={t('config_form.sizer_type_desc', 'Control how position sizes are calculated for each trade')}>
                                    <InfoCircleOutlined style={{ marginLeft: 6, color: '#64748b', cursor: 'help' }} />
                                </Tooltip>
                            </label>
                            <select
                                id="sizer-type"
                                value={sizerType}
                                onChange={(e) => setSizerType(e.target.value)}
                                className="styled-select"
                            >
                                {SIZER_OPTIONS.map((opt) => (
                                    <option key={opt.value} value={opt.value}>
                                        {t(`sizer.${opt.value}`, opt.label)}
                                    </option>
                                ))}
                            </select>
                        </div>

                        {/* Sizer Config - Only render the relevant one */}
                        {sizerType === 'fixed_size' && (
                            <div className="form-group form-col-span-2">
                                <label htmlFor="stake">{t('config_form.order_size')}</label>
                                <div className="input-with-icon">
                                    <NumberOutlined className="input-icon" />
                                    <input
                                        id="stake"
                                        type="number"
                                        value={stake}
                                        onChange={(e) => setStake(e.target.value)}
                                        required
                                    />
                                </div>
                            </div>
                        )}

                        {sizerType === 'percent_sizer' && (
                            <div className="form-group form-col-span-2">
                                <label htmlFor="sizer-percents">
                                    <PercentageOutlined /> {t('config_form.sizer_percent', 'Position %')}
                                </label>
                                <div className="input-with-icon">
                                    <PercentageOutlined className="input-icon" />
                                    <input
                                        id="sizer-percents"
                                        type="number"
                                        step="0.1"
                                        min="0.1"
                                        max="100"
                                        value={sizerConfig.percents || 10}
                                        onChange={(e) => updateSizerConfig('percents', parseFloat(e.target.value))}
                                    />
                                </div>
                            </div>
                        )}

                        {(sizerType === 'risk_sizer' || sizerType === 'kelly_sizer') && (
                            <div className="form-group form-col-span-2">
                                <label htmlFor="sizer-risk">
                                    <PercentageOutlined /> {t('config_form.sizer_risk', 'Risk per Trade %')}
                                </label>
                                <div className="input-with-icon">
                                    <PercentageOutlined className="input-icon" />
                                    <input
                                        id="sizer-risk"
                                        type="number"
                                        step="0.1"
                                        min="0.1"
                                        max="100"
                                        value={sizerConfig.risk_percent || 2}
                                        onChange={(e) => updateSizerConfig('risk_percent', parseFloat(e.target.value))}
                                    />
                                </div>
                            </div>
                        )}


                        {/* Timeframe Selector */}
                        <div className="form-group form-col-span-2">
                            <label htmlFor="timeframe">
                                <ClockCircleOutlined /> {t('config_form.timeframe', 'Data Interval')}
                                <Tooltip title={t('config_form.timeframe_desc', 'Select the data frequency for backtesting (e.g., daily, hourly)')}>
                                    <InfoCircleOutlined style={{ marginLeft: 6, color: '#64748b', cursor: 'help' }} />
                                </Tooltip>
                            </label>
                            <select
                                id="timeframe"
                                value={timeframe}
                                onChange={(e) => setTimeframe(e.target.value)}
                                className="styled-select"
                            >
                                {TIMEFRAME_OPTIONS.map((opt) => (
                                    <option
                                        key={opt.value}
                                        value={opt.value}
                                        disabled={dataSource === 'eodhd' && opt.value !== '1d'}
                                    >
                                        {t(`timeframe.${opt.value}`, opt.label)}
                                    </option>
                                ))}
                            </select>
                            {dataSource === 'eodhd' && (
                                <div className="field-hint">
                                    {t('config_form.eodhd_timeframe_hint', 'EODHD backtests currently use daily data only.')}
                                </div>
                            )}
                            {dataSource === 'yahoo' && timeframe !== '1d' && (
                                <div className="field-hint">
                                    {t(
                                        `config_form.yahoo_intraday_hint_${timeframe}`,
                                        timeframe === '1m'
                                            ? 'Yahoo Finance 1m data is limited to the most recent 7 days.'
                                            : timeframe === '1h'
                                                ? 'Yahoo Finance 1h data is limited to the most recent 729 days.'
                                                : 'Yahoo Finance intraday data is limited to the most recent 59 days.'
                                    )}
                                </div>
                            )}
                        </div>
                    </div>

                    {/* Strategy Parameters Section */}
                    {strategyParams.length > 0 && (
                        <div className="strategy-params-section">
                            <div
                                className="strategy-params-header"
                                onClick={() => setParamsExpanded(!paramsExpanded)}
                            >
                                <span className="params-toggle-icon">
                                    {paramsExpanded ? <DownOutlined /> : <RightOutlined />}
                                </span>
                                <SettingOutlined />
                                <span>{t('config_form.strategy_params', 'Strategy Parameters')}</span>
                                <span className="params-count">({strategyParams.length})</span>
                            </div>
                            {paramsExpanded && (
                                <div className="strategy-params-grid">
                                    {strategyParams.map((param) => (
                                        <div key={param.name} className="form-group param-group">
                                            <label htmlFor={`param-${param.name}`}>
                                                {param.name}
                                                <span className="param-type">({param.type})</span>
                                            </label>
                                            <input
                                                id={`param-${param.name}`}
                                                type="number"
                                                step={param.type === 'float' ? '0.01' : '1'}
                                                value={paramOverrides[param.name] ?? param.value}
                                                onChange={(e) => onParamChange(param.name, e.target.value, param.type)}
                                            />
                                        </div>
                                    ))}
                                </div>
                            )}
                        </div>
                    )}

                    <div className="form-actions-enhanced">
                        <button type="submit" className="btn-primary glow-effect" disabled={loading}>
                            {loading ? <span className="spinner-sm"></span> : t('config_form.run_backtest')}
                        </button>
                    </div>
                </form>
            )
            }

            {
                formattedError && (
                    <Alert
                        className="strategy-error-alert"
                        type="error"
                        showIcon
                        message={formattedError.title}
                        description={(
                            <div className="strategy-error-alert-body">
                                {formattedError.description && (
                                    <div className="strategy-error-alert-description">
                                        {formattedError.description}
                                    </div>
                                )}
                                {formattedError.suggestions?.length > 0 && (
                                    <ul className="strategy-error-alert-list">
                                        {formattedError.suggestions.map((suggestion) => (
                                            <li key={suggestion}>{suggestion}</li>
                                        ))}
                                    </ul>
                                )}
                                {showTechnicalDetail && (
                                    <Collapse
                                        className="strategy-error-alert-detail"
                                        ghost
                                        size="small"
                                        items={[
                                            {
                                                key: 'technical-detail',
                                                label: t('common.strategy_errors.labels.technical_detail', 'Technical detail'),
                                                children: (
                                                    <div className="strategy-error-alert-detail-content">
                                                        {formattedError.detail}
                                                    </div>
                                                ),
                                            },
                                        ]}
                                    />
                                )}
                            </div>
                        )}
                    />
                )
            }
        </section >
    );
}

StrategyConfigForm.propTypes = {
    strategies: PropTypes.array.isRequired,
    selectedStrategy: PropTypes.string.isRequired,
    setSelectedStrategy: PropTypes.func.isRequired,
    fetchStrategies: PropTypes.func.isRequired,
    ticker: PropTypes.string.isRequired,
    setTicker: PropTypes.func.isRequired,
    dataSource: PropTypes.string.isRequired,
    setDataSource: PropTypes.func.isRequired,
    instrumentType: PropTypes.string.isRequired,
    setInstrumentType: PropTypes.func.isRequired,
    startDate: PropTypes.string.isRequired,
    setStartDate: PropTypes.func.isRequired,
    endDate: PropTypes.string.isRequired,
    setEndDate: PropTypes.func.isRequired,
    initialCash: PropTypes.oneOfType([PropTypes.string, PropTypes.number]).isRequired,
    setInitialCash: PropTypes.func.isRequired,
    commission: PropTypes.oneOfType([PropTypes.string, PropTypes.number]).isRequired,
    setCommission: PropTypes.func.isRequired,
    stake: PropTypes.oneOfType([PropTypes.string, PropTypes.number]).isRequired,
    setStake: PropTypes.func.isRequired,
    sizerType: PropTypes.string,
    setSizerType: PropTypes.func,
    sizerConfig: PropTypes.object,
    setSizerConfig: PropTypes.func,
    timeframe: PropTypes.string,
    setTimeframe: PropTypes.func,
    loading: PropTypes.bool.isRequired,
    onSubmit: PropTypes.func.isRequired,
    error: PropTypes.any,
    strategyParams: PropTypes.array,
    paramOverrides: PropTypes.object,
    onParamChange: PropTypes.func
};


export default StrategyConfigForm;

