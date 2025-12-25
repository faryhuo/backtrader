import { RobotOutlined } from '@ant-design/icons';

/**
 * Empty state component displayed when no backtest has been run
 */
function EmptyState({ t }) {
    return (
        <div className="empty-state-container">
            <div className="empty-state-icon">
                <RobotOutlined />
            </div>
            <h3>{t('config_form.ready_to_run', 'Ready to Backtest')}</h3>
            <p>{t('config_form.select_strategy_hint', 'Configure your parameters above and hit "Run Backtest" to see AI-powered analysis.')}</p>
        </div>
    );
}

export default EmptyState;
