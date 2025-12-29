import { useState } from 'react';
import { Form, Select, InputNumber, Switch, Tooltip, Space } from 'antd';
import {
    SyncOutlined,
    InfoCircleOutlined,
    SettingOutlined,
} from '@ant-design/icons';

/**
 * Rebalance Configuration Section Component
 * 
 * Provides UI for configuring portfolio rebalancing settings:
 * - Enable/disable rebalancing
 * - Rebalance frequency (monthly, quarterly, annually)
 * - Optimization method (equal_weight, risk_parity, min_variance, markowitz)
 * - Min trade threshold
 * - Transaction cost percentage
 */
function RebalanceConfigSection({
    t,
    enabled,
    onEnabledChange,
    config,
    onConfigChange,
}) {
    const frequencyOptions = [
        { value: 'monthly', label: t('portfolio.rebalance.frequency.monthly', 'Monthly') },
        { value: 'monthly_first', label: t('portfolio.rebalance.frequency.monthly_first', 'Monthly (First Day)') },
        { value: 'monthly_last', label: t('portfolio.rebalance.frequency.monthly_last', 'Monthly (Last Day)') },
        { value: 'quarterly', label: t('portfolio.rebalance.frequency.quarterly', 'Quarterly') },
        { value: 'annually', label: t('portfolio.rebalance.frequency.annually', 'Annually') },
    ];

    const optimizationOptions = [
        { value: 'equal_weight', label: t('portfolio.rebalance.optimization.equal_weight', 'Equal Weight') },
        { value: 'risk_parity', label: t('portfolio.rebalance.optimization.risk_parity', 'Risk Parity') },
        { value: 'min_variance', label: t('portfolio.rebalance.optimization.min_variance', 'Minimum Variance') },
        { value: 'markowitz', label: t('portfolio.rebalance.optimization.markowitz', 'Markowitz (Max Sharpe)') },
    ];

    const updateConfig = (key, value) => {
        onConfigChange({ ...config, [key]: value });
    };

    return (
        <div className="rebalance-config-section">
            <div className="section-header">
                <Space>
                    <SyncOutlined />
                    <span>{t('portfolio.rebalance.title', 'Rebalancing')}</span>
                </Space>
                <Switch
                    checked={enabled}
                    onChange={onEnabledChange}
                    checkedChildren={t('common.enabled', 'Enabled')}
                    unCheckedChildren={t('common.disabled', 'Disabled')}
                />
            </div>

            {enabled && (
                <div className="rebalance-config-content">
                    <Form layout="vertical" size="small">
                        <div className="rebalance-config-grid">
                            <Form.Item
                                label={
                                    <Tooltip title={t('portfolio.rebalance.frequency_tooltip', 'How often to rebalance the portfolio')}>
                                        <span>
                                            {t('portfolio.rebalance.frequency_label', 'Frequency')} <InfoCircleOutlined style={{ opacity: 0.5 }} />
                                        </span>
                                    </Tooltip>
                                }
                            >
                                <Select
                                    value={config.frequency || 'monthly'}
                                    onChange={(v) => updateConfig('frequency', v)}
                                    options={frequencyOptions}
                                    style={{ width: '100%' }}
                                />
                            </Form.Item>

                            <Form.Item
                                label={
                                    <Tooltip title={t('portfolio.rebalance.optimization_tooltip', 'Method to calculate target weights during rebalancing')}>
                                        <span>
                                            {t('portfolio.rebalance.optimization_label', 'Optimization Method')} <InfoCircleOutlined style={{ opacity: 0.5 }} />
                                        </span>
                                    </Tooltip>
                                }
                            >
                                <Select
                                    value={config.optimization_method || 'equal_weight'}
                                    onChange={(v) => updateConfig('optimization_method', v)}
                                    options={optimizationOptions}
                                    style={{ width: '100%' }}
                                />
                            </Form.Item>

                            <Form.Item
                                label={
                                    <Tooltip title={t('portfolio.rebalance.threshold_tooltip', 'Minimum position change % required to execute a trade (default 1%)')}>
                                        <span>
                                            {t('portfolio.rebalance.threshold_label', 'Min Trade Threshold')} <InfoCircleOutlined style={{ opacity: 0.5 }} />
                                        </span>
                                    </Tooltip>
                                }
                            >
                                <InputNumber
                                    value={(config.min_trade_threshold || 0.01) * 100}
                                    onChange={(v) => updateConfig('min_trade_threshold', (v || 1) / 100)}
                                    min={0}
                                    max={100}
                                    step={0.5}
                                    formatter={(value) => `${value}%`}
                                    parser={(value) => value.replace('%', '')}
                                    style={{ width: '100%' }}
                                />
                            </Form.Item>

                            <Form.Item
                                label={
                                    <Tooltip title={t('portfolio.rebalance.cost_tooltip', 'Estimated transaction cost as % of trade value (default 0.1%)')}>
                                        <span>
                                            {t('portfolio.rebalance.cost_label', 'Transaction Cost')} <InfoCircleOutlined style={{ opacity: 0.5 }} />
                                        </span>
                                    </Tooltip>
                                }
                            >
                                <InputNumber
                                    value={(config.transaction_cost_pct || 0.001) * 100}
                                    onChange={(v) => updateConfig('transaction_cost_pct', (v || 0.1) / 100)}
                                    min={0}
                                    max={10}
                                    step={0.01}
                                    formatter={(value) => `${value}%`}
                                    parser={(value) => value.replace('%', '')}
                                    style={{ width: '100%' }}
                                />
                            </Form.Item>
                        </div>
                    </Form>
                </div>
            )}

            {!enabled && (
                <div className="rebalance-disabled-hint">
                    {t('portfolio.rebalance.disabled_hint', 'Enable rebalancing to periodically adjust portfolio weights.')}
                </div>
            )}
        </div>
    );
}

export default RebalanceConfigSection;
