import { Card, Progress } from 'antd';
import { LoadingOutlined, CheckCircleOutlined } from '@ant-design/icons';

/**
 * Task progress card displayed during backtest execution
 * Shows loading spinner, task name, message, and progress bar
 */
function TaskProgressCard({ taskProgress }) {
    return (
        <Card className="task-progress-card" style={{
            background: 'linear-gradient(135deg, rgba(34, 211, 238, 0.1) 0%, rgba(8, 145, 178, 0.1) 100%)',
            border: '1px solid rgba(34, 211, 238, 0.3)',
            borderRadius: '12px',
            marginTop: '24px'
        }}>
            <div style={{ display: 'flex', alignItems: 'center', gap: '16px', marginBottom: '16px' }}>
                {taskProgress.status === 'completed' ? (
                    <CheckCircleOutlined style={{ fontSize: '24px', color: '#52c41a' }} />
                ) : (
                    <LoadingOutlined style={{ fontSize: '24px', color: '#22d3ee' }} spin />
                )}
                <div>
                    <h3 style={{ margin: 0, color: '#e2e8f0', fontSize: '16px' }}>{taskProgress.name}</h3>
                    <span style={{ color: '#94a3b8', fontSize: '14px' }}>{taskProgress.message}</span>
                </div>
            </div>
            <Progress
                percent={taskProgress.progress}
                status={taskProgress.status === 'running' ? 'active' : 'normal'}
                strokeColor={{ '0%': '#22d3ee', '100%': '#0891b2' }}
                trailColor="rgba(255,255,255,0.1)"
            />
        </Card>
    );
}

export default TaskProgressCard;
