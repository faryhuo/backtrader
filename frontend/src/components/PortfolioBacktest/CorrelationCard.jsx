import { Card } from 'antd';
import { InfoCircleOutlined } from '@ant-design/icons';

/**
 * Correlation matrix display card
 */
function CorrelationCard({ t, correlation }) {
    return (
        <Card className="correlation-card" title={
            <span><InfoCircleOutlined /> {t('portfolio.correlation', 'Correlation Matrix')}</span>
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
