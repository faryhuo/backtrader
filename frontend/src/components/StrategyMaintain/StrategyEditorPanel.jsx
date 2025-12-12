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
    t
}) {
    return (
        <div className="editor-workspace">
            <div className="editor-toolbar">
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
            </div>

            <div className="code-editor-wrapper">
                <Editor
                    height="100%"
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
                        padding: { top: 16 }
                    }}
                />
            </div>
            
            <div className="editor-footer">
                <EditorActions
                    onSave={saveStrategy}
                    loading={codeLoading}
                    t={t}
                />
            </div>
        </div>
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
    t: PropTypes.func.isRequired
};

export default StrategyEditorPanel;
