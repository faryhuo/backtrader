/**
 * SharedReport Page - Public view for shared reports.
 *
 * Features:
 * - Access reports via share token (no authentication required)
 * - Display HTML report content in iframe
 * - Handle expired/invalid tokens
 */

import { useState, useEffect } from 'react';
import { useParams, useNavigate } from 'react-router-dom';
import { useTranslation } from 'react-i18next';
import { Result, Button, Spin } from 'antd';
import { FileTextOutlined, HomeOutlined } from '@ant-design/icons';
import { reportApi } from '../services/reportApi';
import './SharedReport.css';

function SharedReport() {
    const { token } = useParams();
    const navigate = useNavigate();
    const { t } = useTranslation();

    const [loading, setLoading] = useState(true);
    const [error, setError] = useState(null);
    const [htmlContent, setHtmlContent] = useState(null);

    useEffect(() => {
        const fetchReport = async () => {
            if (!token) {
                setError('missing_token');
                setLoading(false);
                return;
            }

            try {
                setLoading(true);
                const content = await reportApi.getSharedReport(token);
                setHtmlContent(content);
                setError(null);
            } catch (err) {
                console.error('Failed to load shared report:', err);
                if (err.message.includes('401') || err.message.includes('expired')) {
                    setError('expired');
                } else if (err.message.includes('404')) {
                    setError('not_found');
                } else {
                    setError('unknown');
                }
            } finally {
                setLoading(false);
            }
        };

        fetchReport();
    }, [token]);

    // Loading state
    if (loading) {
        return (
            <div className="shared-report-loading">
                <Spin size="large" tip={t('sharedReport.loading', 'Loading shared report...')} />
            </div>
        );
    }

    // Error states
    if (error) {
        const errorConfig = {
            missing_token: {
                status: '404',
                title: t('sharedReport.error.missingToken.title', 'Invalid Link'),
                subTitle: t('sharedReport.error.missingToken.subTitle', 'The share link is invalid or incomplete.'),
            },
            expired: {
                status: '403',
                title: t('sharedReport.error.expired.title', 'Link Expired'),
                subTitle: t('sharedReport.error.expired.subTitle', 'This share link has expired or is no longer valid.'),
            },
            not_found: {
                status: '404',
                title: t('sharedReport.error.notFound.title', 'Report Not Found'),
                subTitle: t('sharedReport.error.notFound.subTitle', 'The shared report could not be found.'),
            },
            unknown: {
                status: '500',
                title: t('sharedReport.error.unknown.title', 'Error'),
                subTitle: t('sharedReport.error.unknown.subTitle', 'Failed to load the shared report. Please try again later.'),
            },
        };

        const config = errorConfig[error] || errorConfig.unknown;

        return (
            <div className="shared-report-error">
                <Result
                    status={config.status}
                    title={config.title}
                    subTitle={config.subTitle}
                    icon={<FileTextOutlined />}
                    extra={[
                        <Button
                            key="home"
                            type="primary"
                            icon={<HomeOutlined />}
                            onClick={() => navigate('/')}
                        >
                            {t('common.backHome', 'Back to Home')}
                        </Button>,
                    ]}
                />
            </div>
        );
    }

    // Success - display report
    return (
        <div className="shared-report">
            <div className="shared-report-container">
                <iframe
                    srcDoc={htmlContent}
                    title={t('sharedReport.title', 'Shared Report')}
                    className="shared-report-iframe"
                    sandbox="allow-scripts allow-same-origin"
                />
            </div>
        </div>
    );
}

export default SharedReport;
