import { InputNumber } from 'antd';
import { SettingOutlined, DownOutlined, RightOutlined } from '@ant-design/icons';

/**
 * Collapsible strategy parameters section
 */
function StrategyParamsSection({
    t, strategyParams, paramOverrides, handleParamChange, paramsExpanded, setParamsExpanded
}) {
    return (
        <div className="strategy-params-section">
            <div
                className="strategy-params-header"
                onClick={() => setParamsExpanded(!paramsExpanded)}
            >
                <span className="params-toggle-icon">
                    {paramsExpanded ? <DownOutlined /> : <RightOutlined />}
                </span>
                <SettingOutlined />
                <span>{t('portfolio.strategy_params', 'Strategy Parameters')}</span>
                <span className="params-count">({strategyParams.length})</span>
            </div>
            {paramsExpanded && (
                <div className="strategy-params-grid">
                    {strategyParams.map((param) => (
                        <div key={param.name} className="strategy-param-item">
                            <label htmlFor={`param-${param.name}`}>
                                {param.name}
                                <span className="param-type">({param.type})</span>
                            </label>
                            <InputNumber
                                id={`param-${param.name}`}
                                step={param.type === 'float' ? 0.01 : 1}
                                value={paramOverrides[param.name] ?? param.value}
                                onChange={(v) => handleParamChange(param.name, v, param.type)}
                                style={{ width: '100%' }}
                            />
                        </div>
                    ))}
                </div>
            )}
        </div>
    );
}

export default StrategyParamsSection;
