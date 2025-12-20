import PropTypes from 'prop-types';


function StrategyPlot({ result }) {

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
};

export default StrategyPlot;
