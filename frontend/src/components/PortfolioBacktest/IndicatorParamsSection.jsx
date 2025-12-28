import { useState } from 'react';
import { Form, InputNumber, Tooltip, Collapse, Segmented, Button, Space } from 'antd';
import {
    SettingOutlined,
    InfoCircleOutlined,
    CopyOutlined,
    UndoOutlined,
} from '@ant-design/icons';

const { Panel } = Collapse;

/**
 * Indicator parameter modes
 */
const PARAM_MODES = {
    DEFAULT: 'default',
    GLOBAL: 'global',
    PER_ASSET: 'per_asset',
};

/**
 * Default parameter configurations for indicators
 */
const DEFAULT_PARAMS = {
    sma_period: { value: 20, min: 2, max: 500, i18nKey: 'sma_period' },
    ema_period: { value: null, min: 2, max: 500, i18nKey: 'ema_period' },
    rsi_period: { value: 14, min: 2, max: 100, i18nKey: 'rsi_period' },
    rsi_oversold: { value: 30, min: 0, max: 100, i18nKey: 'rsi_oversold' },
    rsi_overbought: { value: 70, min: 0, max: 100, i18nKey: 'rsi_overbought' },
    macd_fast: { value: null, min: 2, max: 100, i18nKey: 'macd_fast' },
    macd_slow: { value: null, min: 2, max: 200, i18nKey: 'macd_slow' },
    macd_signal: { value: null, min: 2, max: 100, i18nKey: 'macd_signal' },
    bb_period: { value: null, min: 2, max: 100, i18nKey: 'bb_period' },
    bb_std: { value: 2.0, min: 0.1, max: 5.0, step: 0.1, i18nKey: 'bb_std' },
    atr_period: { value: null, min: 2, max: 100, i18nKey: 'atr_period' },
};

/**
 * Parameter groups for organized display
 */
const PARAM_GROUPS = [
    { i18nKey: 'trend', params: ['sma_period', 'ema_period'] },
    { i18nKey: 'momentum', params: ['rsi_period', 'rsi_oversold', 'rsi_overbought'] },
    { i18nKey: 'macd', params: ['macd_fast', 'macd_slow', 'macd_signal'] },
    { i18nKey: 'volatility', params: ['bb_period', 'bb_std', 'atr_period'] },
];

/**
 * Unified Indicator Parameters Component
 * 
 * Provides a single UI for configuring indicator parameters with three modes:
 * - Default: Use built-in default values
 * - Global: Configure parameters that apply to all assets
 * - Per-Asset: Configure different parameters for each asset
 */
function IndicatorParamsSection({
    t,
    tickers,
    paramMode,
    onParamModeChange,
    globalParams,
    onGlobalParamsChange,
    perAssetParams,
    onPerAssetParamsChange,
}) {
    const [activeKeys, setActiveKeys] = useState([]);

    // Mode options for segmented control
    const modeOptions = [
        { label: t('portfolio.param_mode.default', 'Default'), value: PARAM_MODES.DEFAULT },
        { label: t('portfolio.param_mode.global', 'Global Custom'), value: PARAM_MODES.GLOBAL },
        { label: t('portfolio.param_mode.per_asset', 'Per-Asset'), value: PARAM_MODES.PER_ASSET },
    ];

    // Get params for a specific ticker (per-asset mode)
    const getTickerParams = (ticker) => perAssetParams[ticker] || {};

    // Update global parameter
    const updateGlobalParam = (paramName, value) => {
        const newParams = { ...globalParams, [paramName]: value };
        if (value === null || value === undefined) delete newParams[paramName];
        onGlobalParamsChange(newParams);
    };

    // Update per-asset parameter
    const updatePerAssetParam = (ticker, paramName, value) => {
        const newParams = {
            ...perAssetParams,
            [ticker]: { ...getTickerParams(ticker), [paramName]: value },
        };
        if (value === null || value === undefined) {
            delete newParams[ticker][paramName];
        }
        if (Object.keys(newParams[ticker] || {}).length === 0) {
            delete newParams[ticker];
        }
        onPerAssetParamsChange(newParams);
    };

    // Apply one ticker's params to all others
    const applyToAll = (sourceTicker) => {
        const sourceParams = getTickerParams(sourceTicker);
        const newParams = {};
        tickers.forEach((ticker) => {
            if (Object.keys(sourceParams).length > 0) {
                newParams[ticker] = { ...sourceParams };
            }
        });
        onPerAssetParamsChange(newParams);
    };

    // Reset functions
    const resetGlobal = () => onGlobalParamsChange({});
    const resetTicker = (ticker) => {
        const newParams = { ...perAssetParams };
        delete newParams[ticker];
        onPerAssetParamsChange(newParams);
    };
    const resetAllPerAsset = () => onPerAssetParamsChange({});

    // Render parameter input
    const renderParamInput = (paramKey, value, onChange) => {
        const config = DEFAULT_PARAMS[paramKey];
        const label = t(`portfolio.indicators.${config.i18nKey}.label`, paramKey);
        const tooltip = t(`portfolio.indicators.${config.i18nKey}.tooltip`, '');

        return (
            <Form.Item
                key={paramKey}
                label={
                    <Tooltip title={tooltip}>
                        <span>
                            {label} <InfoCircleOutlined style={{ opacity: 0.5 }} />
                        </span>
                    </Tooltip>
                }
                style={{ marginBottom: 8 }}
            >
                <InputNumber
                    value={value}
                    placeholder={config.value !== null ? String(config.value) : t('portfolio.not_set', 'Not set')}
                    min={config.min}
                    max={config.max}
                    step={config.step || 1}
                    onChange={onChange}
                    style={{ width: '100%' }}
                />
            </Form.Item>
        );
    };

    // Render a parameter group
    const renderParamGroup = (group, params, onParamChange) => {
        const groupTitle = t(`portfolio.indicators.groups.${group.i18nKey}`, group.i18nKey);
        return (
            <div key={group.i18nKey} className="param-group">
                <div className="param-group-title">{groupTitle}</div>
                <div className="param-group-inputs">
                    {group.params.map((paramKey) =>
                        renderParamInput(
                            paramKey,
                            params?.[paramKey],
                            (v) => onParamChange(paramKey, v)
                        )
                    )}
                </div>
            </div>
        );
    };

    // Count custom params
    const getGlobalCustomCount = () => Object.keys(globalParams || {}).length;
    const getTickerCustomCount = (ticker) => Object.keys(getTickerParams(ticker)).length;

    // Filter valid tickers
    const validTickers = tickers.filter((t) => t && t.trim());

    return (
        <div className="indicator-params-section">
            <div className="section-header">
                <Space>
                    <SettingOutlined />
                    <span>{t('portfolio.indicator_params', 'Indicator Parameters')}</span>
                </Space>
                {paramMode !== PARAM_MODES.DEFAULT && (
                    <Button
                        size="small"
                        icon={<UndoOutlined />}
                        onClick={paramMode === PARAM_MODES.GLOBAL ? resetGlobal : resetAllPerAsset}
                    >
                        {t('portfolio.reset_all', 'Reset All')}
                    </Button>
                )}
            </div>

            <div className="param-mode-selector">
                <Segmented
                    options={modeOptions}
                    value={paramMode}
                    onChange={onParamModeChange}
                    block
                />
            </div>

            {/* Default mode - just show hint */}
            {paramMode === PARAM_MODES.DEFAULT && (
                <div className="param-mode-hint">
                    {t('portfolio.param_mode.default_hint', 'Using built-in default parameter values for all indicators.')}
                </div>
            )}

            {/* Global mode - show global params editor with same styling as per-asset */}
            {paramMode === PARAM_MODES.GLOBAL && (
                <div className="global-params-content">
                    <div className="param-mode-hint">
                        {t('portfolio.global_indicator_hint', 'Configure indicator parameters that apply to all assets. Leave empty to use defaults.')}
                    </div>
                    <div className="global-params-panel">
                        <Form layout="vertical" size="small" className="per-asset-collapse">
                            {PARAM_GROUPS.map((group) =>
                                renderParamGroup(group, globalParams, updateGlobalParam)
                            )}
                        </Form>
                    </div>
                </div>
            )}

            {/* Per-asset mode - show per-asset editors */}
            {paramMode === PARAM_MODES.PER_ASSET && validTickers.length > 0 && (
                <div className="per-asset-params-content">
                    <div className="param-mode-hint">
                        {t('portfolio.per_asset_hint', 'Configure different indicator parameters for each asset. Leave empty to use defaults.')}
                    </div>
                    <Collapse
                        activeKey={activeKeys}
                        onChange={setActiveKeys}
                        className="per-asset-collapse"
                    >
                        {validTickers.map((ticker) => {
                            const customCount = getTickerCustomCount(ticker);
                            return (
                                <Panel
                                    key={ticker}
                                    header={
                                        <Space>
                                            <span className="ticker-name">{ticker}</span>
                                            {customCount > 0 && (
                                                <span className="custom-badge">
                                                    {customCount} {t('portfolio.custom', 'custom')}
                                                </span>
                                            )}
                                        </Space>
                                    }
                                    extra={
                                        <Space onClick={(e) => e.stopPropagation()}>
                                            <Tooltip title={t('portfolio.apply_to_all', 'Apply to all tickers')}>
                                                <Button
                                                    type="text"
                                                    size="small"
                                                    icon={<CopyOutlined />}
                                                    onClick={(e) => {
                                                        e.stopPropagation();
                                                        applyToAll(ticker);
                                                    }}
                                                    disabled={customCount === 0}
                                                />
                                            </Tooltip>
                                            <Tooltip title={t('portfolio.reset', 'Reset')}>
                                                <Button
                                                    type="text"
                                                    size="small"
                                                    icon={<UndoOutlined />}
                                                    onClick={(e) => {
                                                        e.stopPropagation();
                                                        resetTicker(ticker);
                                                    }}
                                                    disabled={customCount === 0}
                                                />
                                            </Tooltip>
                                        </Space>
                                    }
                                >
                                    <Form layout="vertical" size="small">
                                        {PARAM_GROUPS.map((group) =>
                                            renderParamGroup(
                                                group,
                                                getTickerParams(ticker),
                                                (paramName, value) => updatePerAssetParam(ticker, paramName, value)
                                            )
                                        )}
                                    </Form>
                                </Panel>
                            );
                        })}
                    </Collapse>
                </div>
            )}

            {paramMode === PARAM_MODES.PER_ASSET && validTickers.length === 0 && (
                <div className="param-mode-hint">
                    {t('portfolio.no_tickers_hint', 'Add tickers above to configure per-asset parameters.')}
                </div>
            )}
        </div>
    );
}

export default IndicatorParamsSection;
export { PARAM_MODES };
