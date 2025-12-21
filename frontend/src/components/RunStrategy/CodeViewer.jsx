import { useState, useRef } from 'react';
import { Button, message, Tag } from 'antd';
import { CopyOutlined, CheckOutlined, ExpandOutlined, CompressOutlined, CodeOutlined } from '@ant-design/icons';
import Editor from '@monaco-editor/react';
import { useTranslation } from 'react-i18next';
import './CodeViewer.css';

/**
 * A beautiful code viewer component with syntax highlighting
 * @param {Object} props
 * @param {string} props.code - The source code to display
 * @param {string} props.language - The programming language (default: 'python')
 * @param {Object} props.params - Parameter overrides to display
 * @param {number} props.maxHeight - Maximum height of the editor (default: 500)
 * @param {boolean} props.showParams - Whether to show params section (default: true)
 */
function CodeViewer({
    code = '',
    language = 'python',
    params = {},
    maxHeight = 500,
    showParams = true
}) {
    const { t } = useTranslation();
    const [copied, setCopied] = useState(false);
    const [isExpanded, setIsExpanded] = useState(false);
    const editorRef = useRef(null);

    const handleCopy = async () => {
        try {
            await navigator.clipboard.writeText(code);
            setCopied(true);
            message.success(t('common.code_viewer.copied', 'Copied to clipboard!'));
            setTimeout(() => setCopied(false), 2000);
        } catch {
            message.error(t('common.code_viewer.copy_failed', 'Failed to copy'));
        }
    };

    const handleEditorDidMount = (editor) => {
        editorRef.current = editor;
    };

    const toggleExpand = () => {
        setIsExpanded(!isExpanded);
    };

    // Calculate line count for display
    const lineCount = code.split('\n').length;

    return (
        <div className={`code-viewer-container ${isExpanded ? 'expanded' : ''}`}>
            {/* Header */}
            <div className="code-viewer-header">
                <div className="code-viewer-title">
                    <CodeOutlined className="code-icon" />
                    <span className="code-language-badge">{language.toUpperCase()}</span>
                    <span className="code-line-count">
                        {lineCount} {t('common.code_viewer.lines', 'lines')}
                    </span>
                </div>
                <div className="code-viewer-actions">
                    <Button
                        type="text"
                        icon={isExpanded ? <CompressOutlined /> : <ExpandOutlined />}
                        onClick={toggleExpand}
                        className="code-action-btn"
                        title={isExpanded ? t('common.code_viewer.collapse', 'Collapse') : t('common.code_viewer.expand', 'Expand')}
                    />
                    <Button
                        type="text"
                        icon={copied ? <CheckOutlined style={{ color: '#22c55e' }} /> : <CopyOutlined />}
                        onClick={handleCopy}
                        className="code-action-btn"
                        title={t('common.code_viewer.copy', 'Copy code')}
                    />
                </div>
            </div>

            {/* Parameters Section */}
            {showParams && params && Object.keys(params).length > 0 && (
                <div className="code-viewer-params">
                    <div className="params-label">
                        {t('history.params_override', 'Parameter Overrides')}
                    </div>
                    <div className="params-tags">
                        {Object.entries(params).map(([key, value]) => (
                            <Tag key={key} className="param-tag">
                                <span className="param-key">{key}:</span>
                                <span className="param-value">
                                    {typeof value === 'number' ? value.toLocaleString() : String(value)}
                                </span>
                            </Tag>
                        ))}
                    </div>
                </div>
            )}

            {/* Code Editor */}
            <div
                className="code-viewer-editor"
                style={{ height: isExpanded ? '80vh' : `${maxHeight}px` }}
            >
                <Editor
                    height="100%"
                    language={language}
                    value={code}
                    theme="vs-dark"
                    onMount={handleEditorDidMount}
                    options={{
                        readOnly: true,
                        minimap: { enabled: isExpanded },
                        scrollBeyondLastLine: false,
                        fontSize: 13,
                        lineHeight: 20,
                        fontFamily: "'JetBrains Mono', 'Fira Code', 'Consolas', 'Monaco', monospace",
                        fontLigatures: true,
                        renderLineHighlight: 'line',
                        scrollbar: {
                            useShadows: false,
                            vertical: 'auto',
                            horizontal: 'auto',
                            verticalScrollbarSize: 8,
                            horizontalScrollbarSize: 8
                        },
                        padding: { top: 16, bottom: 16 },
                        lineNumbers: 'on',
                        glyphMargin: false,
                        folding: true,
                        lineDecorationsWidth: 0,
                        lineNumbersMinChars: 3,
                        renderWhitespace: 'selection',
                        bracketPairColorization: { enabled: true },
                        automaticLayout: true,
                        wordWrap: 'off',
                        contextmenu: false,
                        cursorStyle: 'line-thin',
                        cursorBlinking: 'smooth'
                    }}
                />
            </div>

            {/* Footer */}
            {!isExpanded && (
                <div className="code-viewer-footer">
                    <Button
                        type="text"
                        onClick={toggleExpand}
                        className="expand-hint"
                    >
                        <ExpandOutlined /> {t('common.code_viewer.click_expand', 'Click to expand')}
                    </Button>
                </div>
            )}
        </div>
    );
}

export default CodeViewer;

