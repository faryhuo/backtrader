import { Typography } from 'antd'

const { Text } = Typography

export default function SettingRow({ label, hint, children }) {
    return (
        <div className="onboarding-field">
            <div className="onboarding-field-header">
                <Text strong>{label}</Text>
                {hint ? <Text type="secondary">{hint}</Text> : null}
            </div>
            {children}
        </div>
    )
}
