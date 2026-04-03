# StrategyMaintain 目录说明

策略维护与管理模块组件。

## 组件文件
- `AnalysisModal.jsx`：AI 分析结果弹窗，展示策略分析建议。
- `EditorActions.jsx`：编辑器操作按钮组件，保存/运行/分析等操作。
- `NewStrategyModal.jsx`：新建策略弹窗，输入策略名称与初始代码。
- `StrategyEditorPanel.jsx`：Monaco 代码编辑器面板，支持语法高亮与自动补全。
- `StrategySelector.jsx`：策略选择器组件，列表展示与切换。
- `TemplateLibrary/`：策略模板库子目录，展示与选择内置策略模板。

## 功能职责（Functional）
- 策略列表、创建/编辑/删除、代码编辑与版本查看。
- 提供 AI 辅助分析/重写入口（与 `services/aiAnalysis.js` 交互）。

## 非功能性要求（Non-Functional）
- 可维护性：策略编辑器相关逻辑与展示分离，便于迭代。
- 安全：代码内容仅作为文本传输，不在前端执行不可信脚本。

## 约定与规范
- 与后端策略存储格式与校验规则保持同步。
# Recent Notes

- Strategy naming validation now allows Chinese and other Unicode characters, but must continue rejecting `\/:*?"<>|`, trailing dots/spaces, and reserved Windows device names so frontend behavior stays aligned with backend file storage rules.
- `TemplateLibrary/TemplateImportModal.jsx` now checks invalid filename characters and ASCII control characters with explicit character inspection instead of a control-character regex literal, keeping ESLint compatible with the existing validation rules.
- `StrategyMaintain.jsx` now keeps Monaco as an editor-owned model with throttled React state sync, and the workspace CSS constrains editor height/scrolling to prevent input lag and the editor region stretching the full page during typing.
- `StrategyMaintain.jsx` and `TemplateLibrary/TemplateLibrary.jsx` now use Ant Design modal/message feedback for rewrite, rollback, and import failures instead of browser-native dialogs.
