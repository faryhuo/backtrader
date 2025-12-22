import { Button, Space, Tag, Tooltip, Popconfirm } from 'antd';
import { PlayCircleOutlined, StopOutlined, ReloadOutlined } from '@ant-design/icons';
import { useTranslation } from 'react-i18next';

/**
 * Session Controls Component
 * Displays session status and provides start/stop controls
 */
const SessionControls = ({ session, onStart, onStop, onRefresh, loading }) => {
  const { t } = useTranslation();

  const getStatusColor = (status) => {
    const statusColors = {
      'starting': 'blue',
      'running': 'green',
      'stopping': 'orange',
      'stopped': 'default',
      'error': 'red'
    };
    return statusColors[status] || 'default';
  };

  const getStatusText = (status) => {
    return t(`live.status_${status}`) || status;
  };

  const _isRunning = session && ['starting', 'running'].includes(session.status);
  const isStopped = session && ['stopped', 'error'].includes(session.status);

  return (
    <Space size="middle">
      {session && (
        <>
          <div>
            <span style={{ marginRight: 8 }}>{t('live.session_status')}:</span>
            <Tag color={getStatusColor(session.status)}>
              {getStatusText(session.status)}
            </Tag>
          </div>

          <div>
            <span style={{ marginRight: 8 }}>{t('live.session_id')}:</span>
            <Tooltip title={session.session_id}>
              <code>{session.session_id?.substring(0, 8)}...</code>
            </Tooltip>
          </div>
        </>
      )}

      <Space>
        {!session || isStopped ? (
          <Button
            type="primary"
            icon={<PlayCircleOutlined />}
            onClick={onStart}
            loading={loading}
          >
            {t('live.start_trading')}
          </Button>
        ) : (
          <Popconfirm
            title={t('live.stop_confirm_title')}
            description={t('live.stop_confirm_desc')}
            onConfirm={onStop}
            okText={t('live.yes_stop')}
            cancelText={t('live.no_cancel')}
          >
            <Button
              danger
              icon={<StopOutlined />}
              loading={loading}
              disabled={session.status === 'stopping'}
            >
              {t('live.stop_trading')}
            </Button>
          </Popconfirm>
        )}

        <Tooltip title="Refresh">
          <Button
            icon={<ReloadOutlined />}
            onClick={onRefresh}
            loading={loading}
          />
        </Tooltip>
      </Space>
    </Space>
  );
};

export default SessionControls;
