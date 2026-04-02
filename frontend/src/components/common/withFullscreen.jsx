/* eslint-disable react-refresh/only-export-components */
import { useState } from 'react';
import { Button, Modal, Space, Tooltip } from 'antd';
import { FullscreenOutlined, FullscreenExitOutlined } from '@ant-design/icons';

/**
 * Higher-Order Component that adds fullscreen modal capability to chart components.
 *
 * This HOC wraps a chart component and provides:
 * - A fullscreen button overlay
 * - A modal that displays the chart in expanded view
 * - Consistent styling and behavior across different chart types
 *
 * Usage:
 *   const FullscreenEquityChart = withFullscreen(EquityChartCore, {
 *     title: (t) => t('portfolio.equity_curve', 'Equity Curve'),
 *     icon: <LineChartOutlined />,
 *     modalWidth: '90%',
 *     fullscreenHeight: 500,
 *   });
 *
 * @param {React.ComponentType} WrappedComponent - The chart component to wrap
 * @param {Object} options - Configuration options
 * @param {Function} options.title - Function that takes `t` and returns the modal title
 * @param {React.ReactNode} options.icon - Icon to display in modal title
 * @param {string|number} options.modalWidth - Width of the fullscreen modal (default: '90%')
 * @param {number} options.fullscreenHeight - Height of the chart in fullscreen mode (default: 500)
 * @param {string} options.buttonPosition - Position of fullscreen button ('top-right', 'bottom-right')
 * @returns {React.ComponentType} Enhanced component with fullscreen capability
 */
export function withFullscreen(WrappedComponent, options = {}) {
    const {
        title = (t) => t?.('chart.fullscreen', 'Chart') || 'Chart',
        icon = null,
        modalWidth = '90%',
        fullscreenHeight = 500,
        buttonPosition = 'top-right',
    } = options;

    // Get display name for debugging
    const displayName = WrappedComponent.displayName || WrappedComponent.name || 'Component';

    function FullscreenWrapper(props) {
        const [isModalVisible, setIsModalVisible] = useState(false);
        const { t, ...chartProps } = props;

        // Calculate button position styles
        const buttonPositionStyles = {
            'top-right': { top: 8, right: 8 },
            'bottom-right': { bottom: 8, right: 8 },
            'top-left': { top: 8, left: 8 },
            'bottom-left': { bottom: 8, left: 8 },
        };

        const positionStyle = buttonPositionStyles[buttonPosition] || buttonPositionStyles['top-right'];

        return (
            <>
                {/* Container with normal chart and fullscreen button */}
                <div style={{ position: 'relative' }} className="fullscreen-chart-container">
                    {/* Render the wrapped chart component */}
                    <WrappedComponent {...chartProps} t={t} />

                    {/* Fullscreen button overlay */}
                    <Tooltip title={t?.('common.fullscreen', 'Fullscreen') || 'Fullscreen'}>
                        <Button
                            type="text"
                            size="small"
                            icon={<FullscreenOutlined />}
                            onClick={() => setIsModalVisible(true)}
                            style={{
                                position: 'absolute',
                                ...positionStyle,
                                zIndex: 10,
                                background: 'rgba(255, 255, 255, 0.8)',
                                border: '1px solid #d9d9d9',
                            }}
                            className="fullscreen-button"
                        />
                    </Tooltip>
                </div>

                {/* Fullscreen modal */}
                <Modal
                    title={
                        <Space>
                            {icon}
                            <span>{typeof title === 'function' ? title(t) : title}</span>
                        </Space>
                    }
                    open={isModalVisible}
                    onCancel={() => setIsModalVisible(false)}
                    width={modalWidth}
                    footer={null}
                    destroyOnClose
                    centered
                    className="fullscreen-chart-modal"
                >
                    <div style={{ minHeight: fullscreenHeight }}>
                        <WrappedComponent
                            {...chartProps}
                            t={t}
                            height={fullscreenHeight}
                            isFullscreen={true}
                        />
                    </div>
                </Modal>
            </>
        );
    }

    // Set display name for debugging
    FullscreenWrapper.displayName = `withFullscreen(${displayName})`;

    return FullscreenWrapper;
}

/**
 * Custom hook for managing fullscreen state.
 * Use this when you need more control over the fullscreen behavior.
 *
 * @returns {Object} { isFullscreen, openFullscreen, closeFullscreen, toggleFullscreen }
 */
export function useFullscreen() {
    const [isFullscreen, setIsFullscreen] = useState(false);

    return {
        isFullscreen,
        openFullscreen: () => setIsFullscreen(true),
        closeFullscreen: () => setIsFullscreen(false),
        toggleFullscreen: () => setIsFullscreen(prev => !prev),
    };
}

/**
 * Standalone fullscreen button component.
 * Use when you need a fullscreen button outside of the HOC pattern.
 *
 * @param {Object} props
 * @param {Function} props.onClick - Click handler
 * @param {boolean} props.isFullscreen - Current fullscreen state
 * @param {Object} props.style - Additional styles
 */
export function FullscreenButton({ onClick, isFullscreen = false, style = {}, t }) {
    const Icon = isFullscreen ? FullscreenExitOutlined : FullscreenOutlined;
    const tooltip = isFullscreen
        ? (t?.('common.exit_fullscreen', 'Exit Fullscreen') || 'Exit Fullscreen')
        : (t?.('common.fullscreen', 'Fullscreen') || 'Fullscreen');

    return (
        <Tooltip title={tooltip}>
            <Button
                type="text"
                size="small"
                icon={<Icon />}
                onClick={onClick}
                style={{
                    background: 'rgba(255, 255, 255, 0.8)',
                    border: '1px solid #d9d9d9',
                    ...style,
                }}
            />
        </Tooltip>
    );
}

export default withFullscreen;
