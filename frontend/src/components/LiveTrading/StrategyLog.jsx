import { useEffect, useRef } from 'react';
import { List, Tag, Empty } from 'antd';
import { InfoCircleOutlined, WarningOutlined, CloseCircleOutlined } from '@ant-design/icons';
import { useTranslation } from 'react-i18next';

const ICON_MAP = {
  info: <InfoCircleOutlined style={{ color: '#1890ff' }} />,
  warning: <WarningOutlined style={{ color: '#faad14' }} />,
  error: <CloseCircleOutlined style={{ color: '#ff4d4f' }} />,
};

const TAG_COLOR = {
  info: 'blue',
  warning: 'orange',
  error: 'red',
  buy: 'green',
  sell: 'red',
  signal: 'purple',
};

const formatTime = (timestamp) => {
  const date = new Date(timestamp);
  return date.toLocaleTimeString('zh-CN', { hour12: false });
};

const StrategyLog = ({ logs = [] }) => {
  const { t } = useTranslation();
  const listRef = useRef(null);

  // Auto-scroll to top when new logs arrive
  useEffect(() => {
    if (listRef.current) {
      listRef.current.scrollTop = 0;
    }
  }, [logs.length]);

  if (!logs || logs.length === 0) {
    return (
      <div style={{
        height: 200,
        display: 'flex',
        alignItems: 'center',
        justifyContent: 'center',
        background: '#1f1f1f',
        borderRadius: 8,
        border: '1px solid #303030'
      }}>
        <Empty
          image={Empty.PRESENTED_IMAGE_SIMPLE}
          description={<span style={{ color: '#888' }}>{t('live.no_strategy_logs', 'No strategy logs yet')}</span>}
        />
      </div>
    );
  }

  return (
    <div
      style={{
        maxHeight: 200,
        overflowY: 'auto',
        background: '#1f1f1f',
        borderRadius: 8,
        border: '1px solid #303030',
      }}
    >
      <List
        ref={listRef}
        size="small"
        dataSource={logs}
        renderItem={(item) => {
          // Auto-detect log type from message content
          let type = item.level || 'info';
          const msg = item.message?.toLowerCase() || '';
          if (msg.includes('buy')) {
            type = 'buy';
          } else if (msg.includes('sell')) {
            type = 'sell';
          } else if (msg.includes('signal')) {
            type = 'signal';
          }

          return (
            <List.Item
              style={{
                padding: '4px 8px',
                borderBottom: '1px solid #303030',
                background: type === 'buy' ? 'rgba(0, 255, 0, 0.05)' :
                           type === 'sell' ? 'rgba(255, 0, 0, 0.05)' : 'transparent'
              }}
            >
              <div style={{ display: 'flex', alignItems: 'center', width: '100%', gap: 8 }}>
                <span style={{ color: '#888', fontSize: 11, minWidth: 70 }}>
                  {formatTime(item.timestamp)}
                </span>
                {ICON_MAP[type] || ICON_MAP.info}
                <Tag
                  color={TAG_COLOR[type] || 'blue'}
                  style={{ margin: 0, fontSize: 10, padding: '0 4px' }}
                >
                  {type.toUpperCase()}
                </Tag>
                <span style={{ color: '#ddd', fontSize: 12, flex: 1 }}>
                  {item.message}
                </span>
              </div>
            </List.Item>
          );
        }}
      />
    </div>
  );
};

export default StrategyLog;
