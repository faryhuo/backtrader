import PropTypes from 'prop-types';
import { Image } from 'antd';


function StrategyPlot({ result }) {

    if (!result || !result.plot_url) {
        return null;
    }


    return (
        <>
            <div className="card plot-card">
                <div className="plot-container">
                    <Image src={result.plot_url} alt="Strategy Plot" style={{ maxWidth: '100%' }} />
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
};

export default StrategyPlot;
