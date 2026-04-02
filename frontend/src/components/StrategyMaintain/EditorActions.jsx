import { SaveOutlined, LoadingOutlined } from '@ant-design/icons'

const EditorActions = ({ 
    onSave, 
    loading, 
    t 
}) => {
    return (
        <button 
            className="btn-primary" 
            onClick={onSave} 
            disabled={loading}
        >
            {loading ? <LoadingOutlined /> : <SaveOutlined />} 
            {loading ? t('maintain.saving') : t('maintain.save_strategy')}
        </button>
    )
}

export default EditorActions
