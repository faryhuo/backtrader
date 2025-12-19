import PropTypes from 'prop-types';
import { useTranslation } from 'react-i18next';
import { TagOutlined, RocketOutlined, GlobalOutlined } from '@ant-design/icons';

function TemplateCard({ template, isZh, getDifficultyName, getCategoryName, onSelect }) {
    const { t } = useTranslation();

    const difficultyClass = {
        beginner: 'difficulty-beginner',
        intermediate: 'difficulty-intermediate',
        advanced: 'difficulty-advanced',
    }[template.difficulty] || '';

    return (
        <div className="template-card" onClick={onSelect}>
            <div className="template-card-header">
                <h3 className="template-name">
                    {isZh ? template.name_zh : template.name}
                </h3>
                <span className={`difficulty-badge ${difficultyClass}`}>
                    {getDifficultyName(template.difficulty)}
                </span>
            </div>

            <div className="template-category">
                <TagOutlined /> {getCategoryName(template.category)}
            </div>

            <p className="template-description">
                {isZh ? template.description_zh : template.description}
            </p>

            <div className="template-meta">
                <div className="template-markets">
                    <GlobalOutlined />
                    <span>{template.markets?.slice(0, 3).join(', ')}</span>
                </div>

                <div className="template-tags">
                    {template.tags?.slice(0, 3).map(tag => (
                        <span key={tag} className="template-tag">{tag}</span>
                    ))}
                </div>
            </div>

            <div className="template-params">
                <RocketOutlined /> {template.params?.length || 0} {t('maintain.parameters')}
            </div>

            <button className="import-btn">
                {t('maintain.import_template')}
            </button>
        </div>
    );
}

TemplateCard.propTypes = {
    template: PropTypes.object.isRequired,
    isZh: PropTypes.bool,
    getDifficultyName: PropTypes.func.isRequired,
    getCategoryName: PropTypes.func.isRequired,
    onSelect: PropTypes.func.isRequired,
};

export default TemplateCard;
