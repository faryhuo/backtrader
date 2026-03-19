import { Alert, List, Typography } from 'antd';
import dayjs from 'dayjs';
import { useTranslation } from 'react-i18next';

const { Text } = Typography;

const TradeErrorPanel = ({ errors }) => {
  const { t } = useTranslation();

  if (!errors || errors.length === 0) {
    return (
      <Alert
        type="success"
        showIcon
        message={t('live.errors.none', 'No recent trading errors')}
      />
    );
  }

  return (
    <List
      dataSource={errors}
      split
      renderItem={(item) => (
        <List.Item style={{ paddingLeft: 0, paddingRight: 0 }}>
          <Alert
            type="error"
            showIcon
            style={{ width: '100%' }}
            message={item.displayMessage || item.message}
            description={(
              <Text type="secondary">
                {dayjs(item.timestamp).format('YYYY-MM-DD HH:mm:ss')}
              </Text>
            )}
          />
        </List.Item>
      )}
    />
  );
};

export default TradeErrorPanel;
