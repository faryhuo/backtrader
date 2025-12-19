import PropTypes from 'prop-types';
import { useState, useEffect } from 'react';
import { useTranslation } from 'react-i18next';
import {
    BarChartOutlined,
    AreaChartOutlined,
    FullscreenOutlined,
    FullscreenExitOutlined,
    CameraOutlined,
    DownloadOutlined,
    LineOutlined,
    CalendarOutlined,
    SyncOutlined
} from '@ant-design/icons';
import './ChartToolbar.css';

function ChartToolbar({
    onTimeRangeChange,
    onChartTypeChange,
    onExportData,
    onExportImage,
    onFetchData,
    currentChartType = 'candlestick',
    currentTimeRange = '1m',
    startDate,
    endDate
}) {
    const { t } = useTranslation();
    const [isFullscreen, setIsFullscreen] = useState(false);
    const [customStartDate, setCustomStartDate] = useState(startDate || '');
    const [customEndDate, setCustomEndDate] = useState(endDate || '');
    const [showCustomDatePicker, setShowCustomDatePicker] = useState(false);

    // Sync custom dates when props change
    useEffect(() => {
        if (startDate) setCustomStartDate(startDate);
        if (endDate) setCustomEndDate(endDate);
    }, [startDate, endDate]);

    const timeRanges = [
        { label: '1W', value: '1w', weeks: 1 },
        { label: '1M', value: '1m', months: 1 },
        { label: '3M', value: '3m', months: 3 },
        { label: '6M', value: '6m', months: 6 },
        { label: '1Y', value: '1y', years: 1 },
        { label: 'YTD', value: 'ytd', isYTD: true },
        { label: 'ALL', value: 'all' }
    ];

    const chartTypes = [
        { label: t('datasource.candlestick'), value: 'candlestick', icon: <BarChartOutlined /> },
        { label: t('datasource.line'), value: 'line', icon: <LineOutlined /> },
        { label: t('datasource.area'), value: 'area', icon: <AreaChartOutlined /> }
    ];

    const handleFullscreen = () => {
        if (!document.fullscreenElement) {
            const chartContainer = document.querySelector('.chart-card');
            if (chartContainer?.requestFullscreen) {
                chartContainer.requestFullscreen();
                setIsFullscreen(true);
            }
        } else {
            if (document.exitFullscreen) {
                document.exitFullscreen();
                setIsFullscreen(false);
            }
        }
    };

    const handleTimeRangeClick = (range) => {
        setShowCustomDatePicker(false);

        if (onTimeRangeChange) {
            const today = new Date();
            let startDateObj;

            if (range.value === 'all') {
                startDateObj = new Date(today);
                startDateObj.setFullYear(today.getFullYear() - 5);
            } else if (range.isYTD) {
                startDateObj = new Date(today.getFullYear(), 0, 1);
            } else if (range.weeks) {
                startDateObj = new Date(today);
                startDateObj.setDate(today.getDate() - (range.weeks * 7));
            } else if (range.months) {
                startDateObj = new Date(today);
                startDateObj.setMonth(today.getMonth() - range.months);
            } else if (range.years) {
                startDateObj = new Date(today);
                startDateObj.setFullYear(today.getFullYear() - range.years);
            }

            const newStartDate = startDateObj.toISOString().split('T')[0];
            const newEndDate = today.toISOString().split('T')[0];

            setCustomStartDate(newStartDate);
            setCustomEndDate(newEndDate);

            onTimeRangeChange({
                start: newStartDate,
                end: newEndDate,
                range: range.value
            });

            // Auto-trigger data fetch
            if (onFetchData) {
                setTimeout(() => onFetchData(), 50);
            }
        }
    };

    const handleCustomDateToggle = () => {
        setShowCustomDatePicker(!showCustomDatePicker);
    };

    const handleApplyCustomDate = () => {
        if (customStartDate && customEndDate && onTimeRangeChange) {
            onTimeRangeChange({
                start: customStartDate,
                end: customEndDate,
                range: 'custom'
            });

            // Auto-trigger data fetch
            if (onFetchData) {
                setTimeout(() => onFetchData(), 50);
            }
        }
    };

    return (
        <div className="chart-toolbar-wrapper">
            <div className="chart-toolbar">
                {/* Time Range Selector */}
                <div className="toolbar-section">
                    <span className="toolbar-label">{t('datasource.date_range')}:</span>
                    <div className="toolbar-button-group">
                        {timeRanges.map(range => (
                            <button
                                key={range.value}
                                className={`toolbar-btn ${currentTimeRange === range.value ? 'active' : ''}`}
                                onClick={() => handleTimeRangeClick(range)}
                            >
                                {range.label}
                            </button>
                        ))}
                        <button
                            className={`toolbar-btn ${currentTimeRange === 'custom' || showCustomDatePicker ? 'active' : ''}`}
                            onClick={handleCustomDateToggle}
                            title={t('datasource.custom_range')}
                        >
                            <CalendarOutlined />
                        </button>
                    </div>
                </div>

                {/* Chart Type Selector */}
                <div className="toolbar-section">
                    <span className="toolbar-label">{t('datasource.chart_type')}:</span>
                    <div className="toolbar-button-group">
                        {chartTypes.map(type => (
                            <button
                                key={type.value}
                                className={`toolbar-btn icon-btn ${currentChartType === type.value ? 'active' : ''}`}
                                onClick={() => onChartTypeChange && onChartTypeChange(type.value)}
                                title={type.label}
                            >
                                {type.icon}
                            </button>
                        ))}
                    </div>
                </div>

                {/* Actions */}
                <div className="toolbar-section toolbar-actions">
                    <button
                        className="toolbar-btn icon-btn"
                        onClick={onExportImage}
                        title={t('datasource.export_chart')}
                    >
                        <CameraOutlined />
                    </button>
                    <button
                        className="toolbar-btn icon-btn"
                        onClick={onExportData}
                        title={t('datasource.export_data')}
                    >
                        <DownloadOutlined />
                    </button>
                    <button
                        className="toolbar-btn icon-btn"
                        onClick={handleFullscreen}
                        title={isFullscreen ? t('datasource.exit_fullscreen') : t('datasource.fullscreen')}
                    >
                        {isFullscreen ? <FullscreenExitOutlined /> : <FullscreenOutlined />}
                    </button>
                </div>
            </div>

            {/* Custom Date Picker Panel */}
            {showCustomDatePicker && (
                <div className="custom-date-picker-panel">
                    <div className="date-picker-row">
                        <div className="date-picker-field">
                            <label>{t('config_form.start_date')}</label>
                            <input
                                type="date"
                                value={customStartDate}
                                onChange={(e) => setCustomStartDate(e.target.value)}
                            />
                        </div>
                        <span className="date-separator">→</span>
                        <div className="date-picker-field">
                            <label>{t('config_form.end_date')}</label>
                            <input
                                type="date"
                                value={customEndDate}
                                onChange={(e) => setCustomEndDate(e.target.value)}
                            />
                        </div>
                        <button
                            className="btn-primary btn-apply-date"
                            onClick={handleApplyCustomDate}
                        >
                            <SyncOutlined /> {t('datasource.apply')}
                        </button>
                    </div>
                </div>
            )}
        </div>
    );
}

ChartToolbar.propTypes = {
    onTimeRangeChange: PropTypes.func,
    onChartTypeChange: PropTypes.func,
    onExportData: PropTypes.func,
    onExportImage: PropTypes.func,
    onFetchData: PropTypes.func,
    currentChartType: PropTypes.string,
    currentTimeRange: PropTypes.string,
    startDate: PropTypes.string,
    endDate: PropTypes.string
};

export default ChartToolbar;
