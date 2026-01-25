# 🚀 快速开始指南

## 在另一台电脑上打开项目后

### 方法一：使用 Cursor 任务（推荐）

1. 在 Cursor 中按 `Cmd+Shift+P`（macOS）或 `Ctrl+Shift+P`（Windows/Linux）
2. 输入 `Tasks: Run Task`
3. 选择 **"🔄 自动恢复 Agent 配置（需确认）"**
4. 在终端中确认是否恢复（输入 `y` 确认，`N` 取消）

### 方法二：在终端中运行

```bash
cd .cursor
./auto_restore_agent_config.sh
```

然后根据提示确认是否恢复。

### 方法三：直接恢复（不提示）

```bash
cd .cursor
./restore_agent_config.sh
```

## 在当前电脑上更新配置后

当 Agent 配置有更新时（比如新增了对话），运行：

```bash
cd .cursor
./sync_agent_config.sh
```

配置会自动同步到另一台电脑。

## 提示

- ✅ 自动恢复脚本会智能检测是否需要恢复
- ✅ 恢复前会显示详细信息并要求确认
- ✅ 避免意外覆盖现有配置
- ✅ 支持时间戳比较，只在新配置时提示
