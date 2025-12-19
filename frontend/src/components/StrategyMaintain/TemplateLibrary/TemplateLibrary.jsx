import { useState, useEffect } from 'react';
import PropTypes from 'prop-types';
import { useTranslation } from 'react-i18next';
import { api } from '../../../services/api';
import TemplateCard from './TemplateCard';
import TemplateImportModal from './TemplateImportModal';
import './TemplateLibrary.css';

function TemplateLibrary({ onImport, onClose }) {
    const { t, i18n } = useTranslation();
    const isZh = i18n.language?.startsWith('zh');

    const [templates, setTemplates] = useState([]);
    const [categories, setCategories] = useState([]);
    const [difficulties, setDifficulties] = useState([]);
    const [loading, setLoading] = useState(true);
    const [selectedCategory, setSelectedCategory] = useState('all');
    const [selectedTemplate, setSelectedTemplate] = useState(null);
    const [showImportModal, setShowImportModal] = useState(false);
    const [importLoading, setImportLoading] = useState(false);

    useEffect(() => {
        fetchTemplates();
    }, []);

    const fetchTemplates = async () => {
        try {
            setLoading(true);
            const data = await api.getTemplates();
            setTemplates(data.templates || []);
            setCategories(data.categories || []);
            setDifficulties(data.difficulties || []);
        } catch (err) {
            console.error('Failed to load templates:', err);
        } finally {
            setLoading(false);
        }
    };

    const filteredTemplates = selectedCategory === 'all'
        ? templates
        : templates.filter(t => t.category === selectedCategory);

    const handleSelectTemplate = (template) => {
        setSelectedTemplate(template);
        setShowImportModal(true);
    };

    const handleImport = async (templateId, name) => {
        try {
            setImportLoading(true);
            await api.importTemplate(templateId, name);
            setShowImportModal(false);
            if (onImport) {
                onImport(name);
            }
        } catch (err) {
            alert(t('maintain.import_failed') + ': ' + err.message);
        } finally {
            setImportLoading(false);
        }
    };

    const getCategoryName = (categoryId) => {
        const cat = categories.find(c => c.id === categoryId);
        return cat ? (isZh ? cat.name_zh : cat.name) : categoryId;
    };

    const getDifficultyName = (difficultyId) => {
        const diff = difficulties.find(d => d.id === difficultyId);
        return diff ? (isZh ? diff.name_zh : diff.name) : difficultyId;
    };

    return (
        <div className="template-library-overlay" onClick={onClose}>
            <div className="template-library-container" onClick={e => e.stopPropagation()}>
                <div className="template-library-header">
                    <h2>{t('maintain.template_library')}</h2>
                    <button className="close-btn" onClick={onClose}>&times;</button>
                </div>

                <div className="template-library-content">
                    {/* Category Filter */}
                    <div className="template-categories">
                        <button
                            className={`category-btn ${selectedCategory === 'all' ? 'active' : ''}`}
                            onClick={() => setSelectedCategory('all')}
                        >
                            {t('maintain.all_categories')}
                        </button>
                        {categories.map(cat => (
                            <button
                                key={cat.id}
                                className={`category-btn ${selectedCategory === cat.id ? 'active' : ''}`}
                                onClick={() => setSelectedCategory(cat.id)}
                            >
                                {isZh ? cat.name_zh : cat.name}
                            </button>
                        ))}
                    </div>

                    {/* Template Grid */}
                    {loading ? (
                        <div className="template-loading">{t('common.loading')}</div>
                    ) : (
                        <div className="template-grid">
                            {filteredTemplates.map(template => (
                                <TemplateCard
                                    key={template.id}
                                    template={template}
                                    isZh={isZh}
                                    getDifficultyName={getDifficultyName}
                                    getCategoryName={getCategoryName}
                                    onSelect={() => handleSelectTemplate(template)}
                                />
                            ))}
                            {filteredTemplates.length === 0 && (
                                <div className="no-templates">{t('maintain.no_templates')}</div>
                            )}
                        </div>
                    )}
                </div>

                {showImportModal && selectedTemplate && (
                    <TemplateImportModal
                        template={selectedTemplate}
                        isZh={isZh}
                        loading={importLoading}
                        onImport={handleImport}
                        onClose={() => setShowImportModal(false)}
                    />
                )}
            </div>
        </div>
    );
}

TemplateLibrary.propTypes = {
    onImport: PropTypes.func,
    onClose: PropTypes.func.isRequired,
};

export default TemplateLibrary;
