import { Tag } from 'antd';

/**
 * Renders a tag showing the source of a credential (database or .env)
 */
export function CredentialSourceTag({ source }) {
    return (
        <Tag color={source === 'database' ? 'green' : 'blue'} style={{ marginLeft: 8 }}>
            {source === 'database' ? 'Database' : '.env'}
        </Tag>
    );
}

export default CredentialSourceTag;
