import ReactMarkdown from 'react-markdown';

const AnalysisModal = ({ isOpen, onClose, content, title, t }) => {
    if (!isOpen) return null;

    return (
        <div className="modal-overlay" onClick={onClose}>
            <div className="modal-content" style={{ maxWidth: '800px', width: '90%', maxHeight: '85vh', display: 'flex', flexDirection: 'column' }} onClick={(e) => e.stopPropagation()}>
                <div className="modal-header">
                    <h3>{title}</h3>
                    <button type="button" className="btn-ghost" onClick={onClose} style={{ fontSize: '1.5rem', lineHeight: 1, padding: '0 0.5rem' }}>
                        &times;
                    </button>
                </div>
                <div className="modal-body" style={{ overflowY: 'auto', flex: 1, padding: '1rem' }}>
                    <div className="markdown-body">
                        <ReactMarkdown>{content}</ReactMarkdown>
                    </div>
                </div>
                <div className="modal-actions">
                    <button className="btn-primary" onClick={onClose}>
                        {t('common.close') || 'Close'}
                    </button>
                </div>
            </div>
        </div>
    );
};

export default AnalysisModal;
