import PropTypes from 'prop-types';
import { DiffEditor } from '@monaco-editor/react';
import { CloseOutlined, SwapOutlined } from '@ant-design/icons';
import './VersionDiffViewer.css';

/**
 * VersionDiffViewer - Monaco Editor diff view for comparing strategy versions
 * 
 * Displays side-by-side comparison of two code versions with
 * syntax highlighting and change indicators.
 */
function VersionDiffViewer({
    isOpen,
    onClose,
    oldCode,
    newCode,
    oldVersion,
    newVersion,
    linesAdded,
    linesRemoved,
    t
}) {
    if (!isOpen) return null;

    return (
        <div className="version-diff-overlay">
            <div className="version-diff-modal">
                <div className="diff-header">
                    <div className="diff-title">
                        <SwapOutlined />
                        <h2>{t('maintain.versions.comparing')}</h2>
                    </div>
                    <div className="diff-versions">
                        <span className="version-badge old">v{oldVersion}</span>
                        <span className="arrow">→</span>
                        <span className="version-badge new">v{newVersion}</span>
                    </div>
                    <div className="diff-stats">
                        {linesAdded > 0 && (
                            <span className="stat added">+{linesAdded}</span>
                        )}
                        {linesRemoved > 0 && (
                            <span className="stat removed">-{linesRemoved}</span>
                        )}
                    </div>
                    <button className="close-btn" onClick={onClose}>
                        <CloseOutlined />
                    </button>
                </div>

                <div className="diff-legend">
                    <div className="legend-item">
                        <span className="legend-color removed"></span>
                        <span>{t('maintain.versions.removed')}</span>
                    </div>
                    <div className="legend-item">
                        <span className="legend-color added"></span>
                        <span>{t('maintain.versions.added')}</span>
                    </div>
                </div>

                <div className="diff-editor-container">
                    <DiffEditor
                        height="100%"
                        language="python"
                        theme="vs-dark"
                        original={oldCode || ''}
                        modified={newCode || ''}
                        options={{
                            readOnly: true,
                            renderSideBySide: true,
                            fontSize: 14,
                            minimap: { enabled: false },
                            scrollBeyondLastLine: false,
                            wordWrap: 'on',
                            automaticLayout: true,
                            originalEditable: false,
                            renderIndicators: true,
                            renderOverviewRuler: true,
                            diffWordWrap: 'on',
                        }}
                    />
                </div>
            </div>
        </div>
    );
}

VersionDiffViewer.propTypes = {
    isOpen: PropTypes.bool.isRequired,
    onClose: PropTypes.func.isRequired,
    oldCode: PropTypes.string,
    newCode: PropTypes.string,
    oldVersion: PropTypes.number,
    newVersion: PropTypes.number,
    linesAdded: PropTypes.number,
    linesRemoved: PropTypes.number,
    t: PropTypes.func.isRequired,
};

VersionDiffViewer.defaultProps = {
    oldCode: '',
    newCode: '',
    oldVersion: 0,
    newVersion: 0,
    linesAdded: 0,
    linesRemoved: 0,
};

export default VersionDiffViewer;
