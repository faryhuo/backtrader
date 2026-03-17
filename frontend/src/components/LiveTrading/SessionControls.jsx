import { useState, useEffect } from 'react';
import { Button, Space, Tag, Popconfirm, Typography, Tooltip } from 'antd';
import { PauseCircleOutlined, ReloadOutlined, ClockCircleOutlined } from '@ant-design/icons';
import { useTranslation } from 'react-i18next';

const { Text } = Typography;

/**
 * Session controls: status badge, session info, stop/refresh buttons, duration timer
 */
const SessionControls = ({ session, ticker: _ticker, onStop, onRefresh, loading }) => {
  const { t } = useTranslation();
  const [elapsed, setElapsed] = useState('');

  useEffect(() => {
    if (!session?.start_time) return;

    const update = () => {
      const start = new Date(session.start_time).getTime();
      const diff = Math.floor((Date.now() - start) / 1000);
      const h = Math.floor(diff / 3600);
      const m = Math.floor((diff % 3600) / 60);
      const s = diff % 60;
      setElapsed(`${h}h ${m}m ${s}s`);
    };

    update();
    const interval = setInterval(update, 1000);
    return () => clearInterval(interval);
  }, [session?.start_time]);

  const statusColor = {
    starting: 'blue',
    running: 'green',
    stopping: 'orange',
    stopped: 'default',
    error: 'red',
  };

  if (!session) return null;

  return (
    <Space size="middle" wrap>
      <Tag color={statusColor[session.status] || 'default'}>
        {session.status?.toUpperCase()}
      </Tag>

      <Tooltip title={session.session_id}>
        <Text type="secondary">
          {session.strategy_name} / {session.symbol} / {session.mode}
        </Text>
      </Tooltip>

      {elapsed && (
        <Space size={4}>
          <ClockCircleOutlined style={{ color: '#8b8b8b' }} />
          <Text type="secondary">{elapsed}</Text>
        </Space>
      )}

      <Button
        icon={<ReloadOutlined />}
        onClick={onRefresh}
        loading={loading}
        size="small"
      />

      <Popconfirm
        title={t('live.confirm_stop', 'Stop this trading session?')}
        onConfirm={onStop}
        okText={t('common.yes', 'Yes')}
        cancelText={t('common.no', 'No')}
        okButtonProps={{ danger: true }}
      >
        <Button danger icon={<PauseCircleOutlined />} loading={loading} size="small">
          {t('live.stop_session', 'Stop')}
        </Button>
      </Popconfirm>
    </Space>
  );
};

export default SessionControls;
