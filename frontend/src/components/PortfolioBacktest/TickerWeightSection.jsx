import { Button, InputNumber, Select, Space, Progress } from 'antd';
import { DeleteOutlined } from '@ant-design/icons';

/**
 * Ticker & Weight input section with grid layout
 */
function TickerWeightSection({
    t, tickers, weights, totalWeight, isWeightValid,
    addTicker, removeTicker, updateTicker, updateWeight, normalizeWeights, equalWeights
}) {
    return (
        <div className="ticker-weight-section">
            <div className="section-header">
                <h4>{t('portfolio.assets', 'Assets & Weights')}</h4>
                <Space>
                    <Button size="small" onClick={equalWeights}>
                        {t('portfolio.equal_weights', 'Equal Weights')}
                    </Button>
                    <Button size="small" onClick={normalizeWeights}>
                        {t('portfolio.normalize', 'Normalize')}
                    </Button>
                    <Button type="dashed" size="small" onClick={addTicker}>
                        + {t('portfolio.add_ticker', 'Add Ticker')}
                    </Button>
                </Space>
            </div>

            <div className="ticker-weight-grid">
                {tickers.map((ticker, index) => (
                    <div key={index} className="ticker-weight-row">
                        <Select
                            mode="tags"
                            className="ticker-input"
                            placeholder="AAPL"
                            value={ticker ? [ticker] : []}
                            onChange={(values) => updateTicker(index, values[values.length - 1] || '')}
                            tokenSeparators={[',']}
                            maxTagCount={1}
                            allowClear
                        />
                        <InputNumber
                            className="weight-input"
                            min={0}
                            max={1}
                            step={0.01}
                            value={weights[index]}
                            onChange={(v) => updateWeight(index, v)}
                            formatter={v => `${(v * 100).toFixed(0)}%`}
                            parser={v => parseFloat(v.replace('%', '')) / 100}
                        />
                        <Button
                            type="text"
                            danger
                            icon={<DeleteOutlined />}
                            onClick={() => removeTicker(index)}
                            disabled={tickers.length <= 1}
                        />
                    </div>
                ))}
            </div>

            <div className="weight-status">
                <Progress
                    percent={Math.min(totalWeight * 100, 100)}
                    status={isWeightValid ? 'success' : 'exception'}
                    format={() => `${(totalWeight * 100).toFixed(0)}%`}
                />
                {!isWeightValid && (
                    <span className="weight-warning">
                        {t('portfolio.weight_warning', 'Weights will be normalized to 100%')}
                    </span>
                )}
            </div>
        </div>
    );
}

export default TickerWeightSection;
