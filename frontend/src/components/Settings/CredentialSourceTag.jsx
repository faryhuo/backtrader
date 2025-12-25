import { Tag } from 'antd';

/**
 * Renders a tag showing the source of a credential
 * - database: User-specific settings in database
 * - database_global: Global (shared) settings in database
 * - env: Environment variable fallback
 */
export function CredentialSourceTag({ source }) {
    const getConfig = () => {
        switch (source) {
            case 'database':
                return { color: 'green', label: 'Database' };
            case 'database_global':
                return { color: 'cyan', label: 'Global' };
            default:
                return { color: 'blue', label: '.env' };
        }
    };

    const { color, label } = getConfig();

    return (
        <Tag color={color} style={{ marginLeft: 8 }}>
            {label}
        </Tag>
    );
}

export default CredentialSourceTag;
