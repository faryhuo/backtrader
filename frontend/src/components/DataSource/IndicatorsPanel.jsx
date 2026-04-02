import PropTypes from 'prop-types';
import { useTranslation } from 'react-i18next';
import { CheckOutlined } from '@ant-design/icons';
import './IndicatorsPanel.css';

function IndicatorsPanel({ indicators, onIndicatorsChange }) {
    const { t } = useTranslation();

    const availableIndicators = [
        { key: 'volume', label: t('datasource.volume'), color: '#26a69a' },
        { key: 'ma5', label: t('datasource.ma5'), color: '#f59e0b' },
        { key: 'ma10', label: t('datasource.ma10'), color: '#8b5cf6' },
        { key: 'ma20', label: t('datasource.ma20'), color: '#ec4899' },
        { key: 'ma50', label: t('datasource.ma50'), color: '#06b6d4' },
    ];

    const toggleIndicator = (key) => {
        onIndicatorsChange({
            ...indicators,
            [key]: !indicators[key]
        });
    };

    return (
        <div className="indicators-panel">
            <h4>{t('datasource.indicators')}</h4>
            <div className="indicators-list">
                {availableIndicators.map(indicator => (
                    <button
                        key={indicator.key}
                        className={`indicator-btn ${indicators[indicator.key] ? 'active' : ''}`}
                        onClick={() => toggleIndicator(indicator.key)}
                    >
                        <span className="indicator-color" style={{ backgroundColor: indicator.color }}></span>
                        <span className="indicator-label">{indicator.label}</span>
                        {indicators[indicator.key] && (
                            <CheckOutlined className="indicator-check" />
                        )}
                    </button>
                ))}
            </div>
        </div>
    );
}

IndicatorsPanel.propTypes = {
    indicators: PropTypes.object.isRequired,
    onIndicatorsChange: PropTypes.func.isRequired
};

export default IndicatorsPanel;
