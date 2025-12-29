import { Card, Tooltip } from 'antd';
import { InfoCircleOutlined } from '@ant-design/icons';

/**
 * Correlation matrix display card
 */
function CorrelationCard({ t, correlation }) {
    const tooltipContent = t('portfolio.correlation_tooltip',
        '相关系数矩阵显示各资产收益之间的相关性。值范围从-1到+1：' +
        '\n• +1：完全正相关（同涨同跌）' +
        '\n• 0：无相关性' +
        '\n• -1：完全负相关（一涨一跌）' +
        '\n较低的相关性有助于分散投资风险。'
    );

    return (
        <Card className="correlation-card" title={
            <span>
                <Tooltip title={<pre style={{ margin: 0, whiteSpace: 'pre-wrap' }}>{tooltipContent}</pre>}>
                    <InfoCircleOutlined style={{ marginRight: 8, cursor: 'help' }} />
                </Tooltip>
                {t('portfolio.correlation', 'Correlation Matrix')}
            </span>
        }>
            <div className="correlation-matrix">
                <table>
                    <thead>
                        <tr>
                            <th></th>
                            {correlation.tickers?.map(ticker => <th key={ticker}>{ticker}</th>)}
                        </tr>
                    </thead>
                    <tbody>
                        {correlation.matrix?.map((row, i) => (
                            <tr key={i}>
                                <th>{correlation.tickers?.[i]}</th>
                                {row.map((val, j) => (
                                    <td
                                        key={j}
                                        style={{
                                            backgroundColor: `rgba(${val > 0 ? '0,255,0' : '255,0,0'}, ${Math.abs(val) * 0.5})`,
                                        }}
                                    >
                                        {val.toFixed(2)}
                                    </td>
                                ))}
                            </tr>
                        ))}
                    </tbody>
                </table>
            </div>
        </Card>
    );
}

export default CorrelationCard;
