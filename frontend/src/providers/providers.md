# providers 目录说明

全局 Provider/Context 与状态容器目录。

## 功能职责（Functional）
- 提供全局状态、主题、权限、通知等上下文。
- 封装第三方库的 Provider，统一在应用入口注入。

## 非功能性要求（Non-Functional）
- 性能：避免 Provider 过度嵌套与大范围重渲染。
- 可维护性：Context 值结构需稳定，避免频繁破坏性变更。

## 约定与规范
- 仅存放跨页面共享的状态；页面私有状态放 `pages/` 或 Hook。

