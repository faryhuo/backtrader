import { useState, useCallback } from 'react';
import { useTranslation } from 'react-i18next';
import {
    Modal,
    Button,
    Space,
    Input,
    Slider,
    Typography,
    Divider,
    Alert,
    Tooltip,
    message,
} from 'antd';
import {
    ShareAltOutlined,
    LinkOutlined,
    CopyOutlined,
    StopOutlined,
    CheckOutlined,
} from '@ant-design/icons';
import { reportApi } from '../../services/reportApi';

const { Text, Paragraph } = Typography;

/**
 * Modal component for sharing reports with configurable expiration.
 * Supports generating, copying, and revoking share links.
 *
 * @param {Object} props - Component props
 * @param {boolean} props.visible - Modal visibility
 * @param {Object} props.report - Report to share
 * @param {function} props.onClose - Close handler
 * @param {function} props.onShareUpdate - Callback when share state changes
 */
function ShareReportModal({ visible, report, onClose, onShareUpdate }) {
    const { t } = useTranslation();

    const [shareLoading, setShareLoading] = useState(false);
    const [shareData, setShareData] = useState(null);
    const [expiresInHours, setExpiresInHours] = useState(168); // 7 days default
    const [copied, setCopied] = useState(false);
    const [revoking, setRevoking] = useState(false);

    // Generate share link
    const generateShareLink = useCallback(async () => {
        if (!report) return;

        try {
            setShareLoading(true);
            const result = await reportApi.createShareLink(report.report_id, expiresInHours);
            const fullUrl = `${window.location.origin}${result.share_url}`;
            setShareData({
                ...result,
                full_url: fullUrl,
            });
            onShareUpdate?.();
            message.success(t('reportCenter.share.generateSuccess', 'Share link generated'));
        } catch (err) {
            console.error('Failed to generate share link:', err);
            message.error(t('reportCenter.share.generateError', 'Failed to generate share link'));
        } finally {
            setShareLoading(false);
        }
    }, [report, expiresInHours, t, onShareUpdate]);

    // Revoke share link
    const revokeShareLink = useCallback(async () => {
        if (!report) return;

        try {
            setRevoking(true);
            await reportApi.revokeShareLink(report.report_id);
            setShareData(null);
            onShareUpdate?.();
            message.success(t('reportCenter.share.revokeSuccess', 'Share link revoked'));
        } catch (err) {
            console.error('Failed to revoke share link:', err);
            message.error(t('reportCenter.share.revokeError', 'Failed to revoke share link'));
        } finally {
            setRevoking(false);
        }
    }, [report, t, onShareUpdate]);

    // Copy share link to clipboard
    const copyShareLink = useCallback(async () => {
        if (!shareData?.full_url) return;

        try {
            await navigator.clipboard.writeText(shareData.full_url);
            setCopied(true);
            message.success(t('reportCenter.share.copied', 'Link copied to clipboard'));
            setTimeout(() => setCopied(false), 3000);
        } catch (_err) {
            message.error(t('reportCenter.share.copyError', 'Failed to copy link'));
        }
    }, [shareData, t]);

    // Handle modal close
    const handleClose = useCallback(() => {
        setShareData(null);
        setCopied(false);
        onClose();
    }, [onClose]);

    return (
        <Modal
            title={
                <Space>
                    <ShareAltOutlined />
                    {t('reportCenter.shareTitle', 'Share Report')}
                </Space>
            }
            open={visible}
            onCancel={handleClose}
            footer={null}
            width={520}
            destroyOnClose
        >
            <div className="share-modal-content">
                {/* Report title */}
                <div className="share-report-info">
                    <Text strong>{report?.title}</Text>
                </div>

                <Divider />

                {/* Share link exists - show link and options */}
                {shareData ? (
                    <div className="share-link-section">
                        <Alert
                            type="success"
                            showIcon
                            icon={<LinkOutlined />}
                            message={t('reportCenter.share.linkActive', 'Share link is active')}
                            description={
                                <Text type="secondary">
                                    {t('reportCenter.share.expiresAt', 'Expires')}: {new Date(shareData.expires_at).toLocaleString()}
                                </Text>
                            }
                            style={{ marginBottom: 16 }}
                        />

                        <Input.Group compact style={{ display: 'flex', marginBottom: 16 }}>
                            <Input
                                value={shareData.full_url}
                                readOnly
                                style={{ flex: 1 }}
                            />
                            <Tooltip title={copied ? t('reportCenter.share.copied', 'Copied!') : t('reportCenter.share.copy', 'Copy link')}>
                                <Button
                                    icon={copied ? <CheckOutlined /> : <CopyOutlined />}
                                    onClick={copyShareLink}
                                    type={copied ? 'primary' : 'default'}
                                />
                            </Tooltip>
                        </Input.Group>

                        <Button
                            danger
                            icon={<StopOutlined />}
                            onClick={revokeShareLink}
                            loading={revoking}
                            block
                        >
                            {t('reportCenter.share.revoke', 'Revoke Share Link')}
                        </Button>
                    </div>
                ) : (
                    <div className="share-generate-section">
                        {/* Expiration selection */}
                        <div className="expiration-section">
                            <Text strong style={{ display: 'block', marginBottom: 8 }}>
                                {t('reportCenter.share.expirationLabel', 'Link expiration')}
                            </Text>
                            <div className="expiration-slider">
                                <Slider
                                    min={24}
                                    max={720}
                                    step={24}
                                    value={expiresInHours}
                                    onChange={setExpiresInHours}
                                    marks={{
                                        24: '1d',
                                        168: '7d',
                                        336: '14d',
                                        720: '30d',
                                    }}
                                    tooltip={{
                                        formatter: (value) => `${Math.round(value / 24)} ${t('reportCenter.share.days', 'days')}`
                                    }}
                                />
                            </div>
                            <Text type="secondary" style={{ display: 'block', textAlign: 'center', marginTop: 8 }}>
                                {t('reportCenter.share.expiresIn', 'Link will expire in')} {Math.round(expiresInHours / 24)} {t('reportCenter.share.days', 'days')}
                            </Text>
                        </div>

                        <Divider />

                        {/* Generate button */}
                        <Button
                            type="primary"
                            icon={<LinkOutlined />}
                            onClick={generateShareLink}
                            loading={shareLoading}
                            block
                            size="large"
                        >
                            {t('reportCenter.share.generate', 'Generate Share Link')}
                        </Button>

                        <Paragraph type="secondary" style={{ marginTop: 16, textAlign: 'center', marginBottom: 0 }}>
                            {t('reportCenter.share.description', 'Anyone with this link can view the report without signing in.')}
                        </Paragraph>
                    </div>
                )}
            </div>
        </Modal>
    );
}

export default ShareReportModal;
