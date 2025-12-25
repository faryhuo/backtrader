import ReactMarkdown from 'react-markdown';
import { CloseOutlined } from '@ant-design/icons';
import './AnalysisModal.css';

const AnalysisModal = ({ isOpen, onClose, content, title, t }) => {
    if (!isOpen) return null;

    return (
        <div className="analysis-modal-overlay" onClick={onClose}>
            <div className="analysis-modal-content" onClick={(e) => e.stopPropagation()}>
                <div className="analysis-modal-header">
                    <h3>{title}</h3>
                    <button
                        type="button"
                        className="analysis-modal-close-btn"
                        onClick={onClose}
                        aria-label="Close"
                    >
                        <CloseOutlined />
                    </button>
                </div>
                <div className="analysis-modal-body">
                    <div className="analysis-markdown-body">
                        <ReactMarkdown>{content}</ReactMarkdown>
                    </div>
                </div>
                <div className="analysis-modal-footer">
                    <button className="btn-primary" onClick={onClose}>
                        {t('common.close')}
                    </button>
                </div>
            </div>
        </div>
    );
};

export default AnalysisModal;
