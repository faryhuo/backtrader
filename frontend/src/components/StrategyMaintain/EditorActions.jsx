import React from 'react'

const EditorActions = ({ 
    onSave, 
    loading, 
    t 
}) => {
    return (
        <div className="form-actions">
            <button className="btn-primary" onClick={onSave} disabled={loading} style={{ marginLeft: 'auto' }}>
                {loading ? t('maintain.saving') : t('maintain.save_strategy')}
            </button>
        </div>
    )
}

export default EditorActions
