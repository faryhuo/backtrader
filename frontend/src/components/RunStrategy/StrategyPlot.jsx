import PropTypes from 'prop-types';
import { useTranslation } from 'react-i18next';


function StrategyPlot({ result, ticker, startDate, endDate, strategyName }) {
    const { t } = useTranslation();

    if (!result || !result.plot_url) {
        return null;
    }


    return (
        <>
            <div className="card plot-card">
                <div className="plot-container">
                    <img src={result.plot_url} alt="Strategy Plot" />
                </div>
            </div>
        </>
    );
}

StrategyPlot.propTypes = {
    result: PropTypes.shape({
        plot_url: PropTypes.string,
        metrics: PropTypes.object
    }),
    ticker: PropTypes.string,
    startDate: PropTypes.string,
    endDate: PropTypes.string,
    strategyName: PropTypes.string
};

export default StrategyPlot;
