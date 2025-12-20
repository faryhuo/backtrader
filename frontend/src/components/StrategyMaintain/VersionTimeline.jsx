import PropTypes from 'prop-types';
import { useState } from 'react';
import { HistoryOutlined, RollbackOutlined, DiffOutlined } from '@ant-design/icons';
import './VersionTimeline.css';

/**
 * VersionTimeline - Displays version history for a strategy
 * 
 * Shows a chronological list of versions with metadata like
 * commit messages, timestamps, and change statistics.
 */
function VersionTimeline({
    versions,
    loading,
    onVersionSelect,
    onCompare,
    onRollback,
    selectedForCompare,
    t
}) {
    const [expandedVersion, setExpandedVersion] = useState(null);

    const formatDate = (isoString) => {
        const date = new Date(isoString);
        return date.toLocaleString();
    };

    const toggleExpand = (versionNumber) => {
        setExpandedVersion(expandedVersion === versionNumber ? null : versionNumber);
    };

    if (loading) {
        return (
            <div className="version-timeline loading">
                <div className="loading-spinner"></div>
                <span>{t('maintain.versions.loading')}</span>
            </div>
        );
    }

    if (!versions || versions.length === 0) {
        return (
            <div className="version-timeline empty">
                <HistoryOutlined className="empty-icon" />
                <p>{t('maintain.versions.no_versions')}</p>
            </div>
        );
    }

    return (
        <div className="version-timeline">
            <div className="timeline-header">
                <HistoryOutlined />
                <h3>{t('maintain.versions.title')}</h3>
                <span className="version-count">{versions.length} {t('maintain.versions.versions')}</span>
            </div>

            <div className="timeline-list">
                {versions.map((version, index) => (
                    <div
                        key={version.version_number}
                        className={`timeline-item ${selectedForCompare.includes(version.version_number) ? 'selected-for-compare' : ''}`}
                    >
                        <div className="timeline-connector">
                            <div className="timeline-dot"></div>
                            {index < versions.length - 1 && <div className="timeline-line"></div>}
                        </div>

                        <div className="timeline-content">
                            <div
                                className="version-header"
                                onClick={() => toggleExpand(version.version_number)}
                            >
                                <div className="version-info">
                                    <span className="version-number">v{version.version_number}</span>
                                    <span className="version-date">{formatDate(version.created_at)}</span>
                                </div>
                                <div className="version-stats">
                                    {version.lines_added > 0 && (
                                        <span className="stat added">+{version.lines_added}</span>
                                    )}
                                    {version.lines_removed > 0 && (
                                        <span className="stat removed">-{version.lines_removed}</span>
                                    )}
                                </div>
                            </div>

                            {version.commit_message && (
                                <p className="commit-message">{version.commit_message}</p>
                            )}

                            {expandedVersion === version.version_number && (
                                <div className="version-actions">
                                    <button
                                        className="action-btn view"
                                        onClick={() => onVersionSelect(version.version_number)}
                                        title={t('maintain.versions.view')}
                                    >
                                        <HistoryOutlined /> {t('maintain.versions.view')}
                                    </button>
                                    <button
                                        className="action-btn compare"
                                        onClick={() => onCompare(version.version_number)}
                                        title={t('maintain.versions.compare')}
                                    >
                                        <DiffOutlined /> {t('maintain.versions.compare')}
                                    </button>
                                    {index > 0 && (
                                        <button
                                            className="action-btn rollback"
                                            onClick={() => onRollback(version.version_number)}
                                            title={t('maintain.versions.rollback')}
                                        >
                                            <RollbackOutlined /> {t('maintain.versions.rollback')}
                                        </button>
                                    )}
                                </div>
                            )}
                        </div>
                    </div>
                ))}
            </div>
        </div>
    );
}

VersionTimeline.propTypes = {
    versions: PropTypes.arrayOf(PropTypes.shape({
        version_number: PropTypes.number.isRequired,
        commit_message: PropTypes.string,
        lines_added: PropTypes.number,
        lines_removed: PropTypes.number,
        created_at: PropTypes.string.isRequired,
    })).isRequired,
    loading: PropTypes.bool,
    onVersionSelect: PropTypes.func.isRequired,
    onCompare: PropTypes.func.isRequired,
    onRollback: PropTypes.func.isRequired,
    selectedForCompare: PropTypes.arrayOf(PropTypes.number),
    t: PropTypes.func.isRequired,
};

VersionTimeline.defaultProps = {
    loading: false,
    selectedForCompare: [],
};

export default VersionTimeline;
