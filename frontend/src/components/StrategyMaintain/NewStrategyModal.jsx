import React, { useState } from 'react'

const NewStrategyModal = ({ isOpen, onClose, onCreate, t }) => {
    const [name, setName] = useState('')

    if (!isOpen) return null

    const handleCreate = () => {
        if (name.trim()) {
            onCreate(name.trim())
            setName('')
        }
    }

    const handleClose = () => {
        setName('')
        onClose()
    }

    return (
        <div className="modal-overlay" onClick={handleClose}>
            <div className="modal-content" onClick={(e) => e.stopPropagation()}>
                <div className="modal-header">
                    <h3>{t('maintain.create_new_strategy')}</h3>
                </div>
                <div className="form-group">
                    <label htmlFor="modal-new-strategy-name">{t('maintain.strategy_name')}</label>
                    <input
                        id="modal-new-strategy-name"
                        type="text"
                        value={name}
                        onChange={(e) => setName(e.target.value)}
                        placeholder={t('maintain.placeholder_name')}
                        autoFocus
                        onKeyDown={(e) => {
                            if (e.key === 'Enter') handleCreate()
                            if (e.key === 'Escape') handleClose()
                        }}
                    />
                </div>
                <div className="modal-actions">
                    <button
                        className="btn-ghost"
                        onClick={handleClose}
                    >
                        {t('common.cancel')}
                    </button>
                    <button
                        className="btn-primary"
                        onClick={handleCreate}
                        disabled={!name.trim()}
                    >
                        {t('maintain.create')}
                    </button>
                </div>
            </div>
        </div>
    )
}

export default NewStrategyModal
