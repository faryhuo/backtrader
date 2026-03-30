import { useState } from 'react';
import PropTypes from 'prop-types';
import { useTranslation } from 'react-i18next';

const INVALID_STRATEGY_NAME_RE = /[<>:"/\\|?*\x00-\x1f]/;
const WINDOWS_RESERVED_NAMES = new Set([
    'CON', 'PRN', 'AUX', 'NUL',
    'COM1', 'COM2', 'COM3', 'COM4', 'COM5', 'COM6', 'COM7', 'COM8', 'COM9',
    'LPT1', 'LPT2', 'LPT3', 'LPT4', 'LPT5', 'LPT6', 'LPT7', 'LPT8', 'LPT9',
]);

function isValidStrategyName(name) {
    if (!name || name === '.' || name === '..') {
        return false;
    }

    if (name.endsWith('.') || name.endsWith(' ')) {
        return false;
    }

    if (INVALID_STRATEGY_NAME_RE.test(name)) {
        return false;
    }

    return !WINDOWS_RESERVED_NAMES.has(name.toUpperCase());
}

function TemplateImportModal({ template, isZh, loading, onImport, onClose }) {
    const { t } = useTranslation();
    const [name, setName] = useState('');
    const [error, setError] = useState('');

    const handleSubmit = (e) => {
        e.preventDefault();

        const trimmedName = name.trim();
        if (!trimmedName) {
            setError(t('maintain.name_required'));
            return;
        }

        if (!isValidStrategyName(trimmedName)) {
            setError(t('maintain.invalid_name_format'));
            return;
        }

        setError('');
        onImport(template.id, trimmedName);
    };

    return (
        <div className="import-modal-overlay" onClick={onClose}>
            <div className="import-modal" onClick={e => e.stopPropagation()}>
                <div className="import-modal-header">
                    <h3>{t('maintain.import_template')}</h3>
                    <button className="close-btn" onClick={onClose}>&times;</button>
                </div>

                <div className="import-modal-body">
                    <div className="template-preview">
                        <h4>{isZh ? template.name_zh : template.name}</h4>
                        <p>{isZh ? template.description_zh : template.description}</p>

                        {template.params && template.params.length > 0 && (
                            <div className="template-params-list">
                                <h5>{t('maintain.parameters')}:</h5>
                                <ul>
                                    {template.params.map(p => (
                                        <li key={p.name}>
                                            <code>{p.name}</code> = {p.default}
                                            <span className="param-desc">{p.description}</span>
                                        </li>
                                    ))}
                                </ul>
                            </div>
                        )}
                    </div>

                    <form onSubmit={handleSubmit}>
                        <div className="form-group">
                            <label htmlFor="strategy-name">{t('maintain.new_strategy_name')}</label>
                            <input
                                id="strategy-name"
                                type="text"
                                value={name}
                                onChange={(e) => setName(e.target.value)}
                                placeholder="my_strategy"
                                disabled={loading}
                                autoFocus
                            />
                            {error && <span className="error-text">{error}</span>}
                            <span className="hint-text">{t('maintain.name_hint')}</span>
                        </div>

                        <div className="import-modal-actions">
                            <button
                                type="button"
                                className="btn-secondary"
                                onClick={onClose}
                                disabled={loading}
                            >
                                {t('common.cancel')}
                            </button>
                            <button
                                type="submit"
                                className="btn-primary"
                                disabled={loading || !name.trim()}
                            >
                                {loading ? t('common.loading') : t('maintain.import')}
                            </button>
                        </div>
                    </form>
                </div>
            </div>
        </div>
    );
}

TemplateImportModal.propTypes = {
    template: PropTypes.object.isRequired,
    isZh: PropTypes.bool,
    loading: PropTypes.bool,
    onImport: PropTypes.func.isRequired,
    onClose: PropTypes.func.isRequired,
};

export default TemplateImportModal;
