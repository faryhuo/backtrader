import {
    LineChartOutlined,
    BarChartOutlined,
    SwapOutlined,
    FileSearchOutlined,
    BulbOutlined,
    ExperimentOutlined,
    CodeOutlined
} from '@ant-design/icons';
import PerformanceOverview from '../components/RunStrategy/PerformanceOverview';
import TradeLog from '../components/RunStrategy/TradeLog';
import StrategyPlot from '../components/RunStrategy/StrategyPlot';
import TaskExecutionLog from '../components/RunStrategy/TaskExecutionLog';
import DeepAnalysis from '../components/DeepAnalysis';
import AIInsightTab from '../components/RunStrategy/AIInsightTab';
import CodeViewer from '../components/RunStrategy/CodeViewer';

/**
 * Build tab items configuration for RunStrategy results
 * 
 * @param {Object} params - Configuration parameters
 * @returns {Array} Tab items configuration array for Ant Design Tabs
 */
export function buildTabItems({
    t, result, tradeList, plotUrl, analyses, activeTab, setActiveTab,
    aiLoading, handleAIAnalysis,
    strategyCode, paramOverrides, ticker, startDate, endDate, initialCash, backtestId
}) {
    const executionLogs = result?.metrics?.execution_logs || result?.execution_logs || [];

    const tabItems = [
        {
            key: 'overview',
            label: <span><LineChartOutlined className="tab-icon" /> {t('history.tab_overview', 'Overview')}</span>,
            children: <PerformanceOverview result={result} />
        },
        {
            key: 'chart',
            label: <span><BarChartOutlined className="tab-icon" /> {t('history.tab_chart', 'Chart')}</span>,
            children: (
                <div style={{ padding: '20px 0' }}>
                    <StrategyPlot result={result} t={t} />
                </div>
            )
        },
        {
            key: 'trades',
            label: <span><SwapOutlined className="tab-icon" /> {t('history.tab_trades', 'Trades')}</span>,
            children: <TradeLog trades={tradeList} />
        },
        {
            key: 'task_logs',
            label: <span><FileSearchOutlined className="tab-icon" /> {t('history.tab_task_logs', 'Log Output')}</span>,
            children: (
                <div style={{ padding: '20px 0' }}>
                    <TaskExecutionLog backtestId={backtestId} logs={executionLogs} />
                </div>
            )
        },
        {
            key: 'ai_insight',
            label: <span><BulbOutlined className="tab-icon" /> {t('history.tab_ai_insight', 'AI Insight')}</span>,
            children: (
                <AIInsightTab
                    t={t}
                    analyses={analyses}
                    activeTab={activeTab}
                    setActiveTab={setActiveTab}
                    aiLoading={aiLoading}
                    handleAIAnalysis={handleAIAnalysis}
                    plotUrl={plotUrl}
                    result={result}
                />
            )
        },
        {
            key: 'deep_analysis',
            label: <span><ExperimentOutlined className="tab-icon" /> {t('history.tab_deep_analysis', 'Deep Analysis')}</span>,
            children: result?.backtest_id ? (
                <DeepAnalysis backtest={{
                    backtest_id: result.backtest_id,
                    ticker,
                    start_date: startDate,
                    end_date: endDate,
                    initial_cash: initialCash
                }} />
            ) : (
                <div style={{ padding: '2rem', textAlign: 'center', color: '#888' }}>
                    {t('history.save_first_hint', 'Please run backtest again to generate Deep Analysis.')}
                </div>
            )
        }
    ];

    if (strategyCode) {
        tabItems.push({
            key: 'strategy_code',
            label: <span><CodeOutlined className="tab-icon" /> {t('history.tab_strategy_code', 'Strategy Code')}</span>,
            children: (
                <div style={{ padding: '20px' }}>
                    <CodeViewer
                        code={strategyCode}
                        language="python"
                        params={paramOverrides}
                        maxHeight={500}
                    />
                </div>
            )
        });
    }

    return tabItems;
}

export default buildTabItems;
