import PropTypes from 'prop-types';
import Editor from '@monaco-editor/react';
import StrategySelector from './StrategySelector';
import EditorActions from './EditorActions';

function StrategyEditorPanel({
    strategies,
    selectedStrategy,
    setSelectedStrategy,
    fetchStrategy,
    fetchStrategies,
    handleAIAnalysis,
    handleAIRewrite,
    codeLoading,
    code,
    setCode,
    saveStrategy,
    openNewStrategyModal,
    t
}) {
    return (
        <section className="card editor-card">
            <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: '1.5rem', borderBottom: '1px solid var(--border-color)', paddingBottom: '1rem' }}>
                <h2 style={{ margin: 0, border: 'none', padding: 0 }}>{t('maintain.editor_title')}</h2>
                <button
                    type="button"
                    className="btn-primary"
                    onClick={openNewStrategyModal}
                    disabled={codeLoading}
                    style={{ minWidth: '100px', padding: '0.5rem 1rem' }}
                >
                    {t('maintain.new')}
                </button>
            </div>
            <p className="subtitle">{t('maintain.subtitle')}</p>
            
            <StrategySelector
                strategies={strategies}
                selectedStrategy={selectedStrategy}
                onSelectStrategy={setSelectedStrategy}
                onReload={() => fetchStrategy(selectedStrategy)}
                onRefreshList={fetchStrategies}
                onAIAnalysis={handleAIAnalysis}
                onAIRewrite={handleAIRewrite}
                loading={codeLoading}
                t={t}
            />

            <div className="code-editor">
                <Editor
                    height="60vh"
                    defaultLanguage="python"
                    language="python"
                    theme="vs-dark"
                    value={code}
                    onChange={(value) => setCode(value ?? '')}
                    options={{
                        fontSize: 14,
                        minimap: { enabled: false },
                        scrollBeyondLastLine: false,
                        wordWrap: 'on',
                        roundedSelection: false,
                        automaticLayout: true,
                    }}
                />
            </div>
            
            <EditorActions
                onSave={saveStrategy}
                loading={codeLoading}
                t={t}
            />
        </section>
    );
}

StrategyEditorPanel.propTypes = {
    strategies: PropTypes.array.isRequired,
    selectedStrategy: PropTypes.string.isRequired,
    setSelectedStrategy: PropTypes.func.isRequired,
    fetchStrategy: PropTypes.func.isRequired,
    fetchStrategies: PropTypes.func.isRequired,
    handleAIAnalysis: PropTypes.func.isRequired,
    handleAIRewrite: PropTypes.func.isRequired,
    codeLoading: PropTypes.bool.isRequired,
    code: PropTypes.string.isRequired,
    setCode: PropTypes.func.isRequired,
    saveStrategy: PropTypes.func.isRequired,
    openNewStrategyModal: PropTypes.func.isRequired,
    t: PropTypes.func.isRequired
};

export default StrategyEditorPanel;
