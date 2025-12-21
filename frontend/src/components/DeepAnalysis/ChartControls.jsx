import React from 'react'
import { useTranslation } from 'react-i18next'
import { Space, Radio, Checkbox, Row, Col } from 'antd'

/**
 * ChartControls - Shared controls for charts
 * 
 * Props:
 *   ranges: Array of strings e.g. ['1M', '3M', '6M', '1Y', 'YTD', 'ALL']
 *   selectedRange: Currently selected range string
 *   onRangeChange: Callback (range) => {}
 *   series: Array of objects { key, label, color, visible }
 *   onSeriesToggle: Callback (key, visible) => {}
 */
const ChartControls = ({
    ranges = ['1M', '3M', '6M', '1Y', 'YTD', 'ALL'],
    selectedRange = 'ALL',
    onRangeChange,
    series = [],
    onSeriesToggle
}) => {
    const { t } = useTranslation()

    return (
        <Row gutter={[16, 16]} align="middle" style={{ marginBottom: 16 }}>
            <Col xs={24} md={12}>
                <Radio.Group
                    value={selectedRange}
                    onChange={e => onRangeChange && onRangeChange(e.target.value)}
                    buttonStyle="solid"
                    size="small"
                >
                    {ranges.map(range => (
                        <Radio.Button key={range} value={range}>
                            {range}
                        </Radio.Button>
                    ))}
                </Radio.Group>
            </Col>
            <Col xs={24} md={12} style={{ textAlign: 'right' }}>
                <Space wrap>
                    {series.map(s => (
                        <Checkbox
                            key={s.key}
                            checked={s.visible}
                            onChange={e => onSeriesToggle && onSeriesToggle(s.key, e.target.checked)}
                            style={{ color: s.color }}
                        >
                            {s.label}
                        </Checkbox>
                    ))}
                </Space>
            </Col>
        </Row>
    )
}

export default ChartControls
