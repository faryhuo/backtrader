# 认证禁用后的响应格式差异总结

## 问题发现

禁用后端认证后，多个 API 端点返回不同的响应格式。

## 已知差异

### 1. 列表响应包装

**启用认证：**
```json
["item1", "item2"]
```

**禁用认证：**
```json
{
  "strategies": ["item1", "item2"]
}
```

**影响的端点：**
- `/api/strategies` - 包装为 `{"strategies": [...]}`
- `/api/templates` - 包装为 `{"templates": [...]}`
- `/api/live/exchanges` - 包装为 `{"exchanges": [...]}`

### 2. Backtest响应字段变化

**问题：** `metrics` 字段内容不同

**错误信息：**
```
AssertionError: Missing required metric: total_return
```

**可能原因：**
- `metrics` 字段结构改变
- 字段名称改变（如：`total_return` vs `totalReturn`）
- 某些字段缺失

## 修复状态

### ✅ 已修复
- `test_list_strategies` 
- `test_template_list`
- `test_get_exchanges` (代码已更新)
- `test_list_sessions` (代码已更新)

### ❌ 需要修复
- Backtest API 所有测试
- 其他可能受影响的 API

## 建议解决方案

### 选项 A：修复测试（当前进行中）
- ✅ 创建了 `response_normalizer.py`
- ✅ 修复了列表包装问题
- ❌ 需要处理更复杂的字段差异
- ⏰ 预计需要较长时间

### 选项 B：统一后端响应（推荐）  
- 修改后端让禁用认证时也返回相同格式
- 测试代码保持简单
- 只需修改几个 route 文件
- ⏰ 更快更简洁

## 下一步

等待用户决定采用哪种方案。
