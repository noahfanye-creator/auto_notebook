# Cursor 项目级设置

此目录用于存储项目特定的 Cursor 编辑器设置，可以通过文件同步服务自动同步到其他设备。

## 📁 目录说明

- `rules.md` 或 `.cursorrules` - 项目特定的 Cursor 规则
- `settings.json` - 项目特定的编辑器设置（可选）
- `agent-config/` - Agent 配置和对话历史（自动同步）
- `sync_agent_config.sh` - 同步 Agent 配置到项目目录
- `restore_agent_config.sh` - 恢复 Agent 配置到本地 Cursor
- `auto_restore_agent_config.sh` - 自动检测并提示恢复（需要确认）

## 🔄 同步说明

### ✅ 自动同步（如果项目目录已同步）

**如果你的项目目录已经通过文件同步服务（iCloud、Dropbox、OneDrive、rsync 等）在两台电脑间同步，那么 `.cursor/` 目录会自动同步！**

这意味着：
- ✅ 项目级 Cursor 设置会自动同步
- ✅ 项目规则文件会自动同步
- ✅ 项目特定的编辑器设置会自动同步
- ✅ Agent 配置和对话历史会自动同步

**无需额外操作**，只需确保项目目录同步正常即可。

### 🤖 Agent 配置自动恢复（推荐）

为了让另一台电脑上的 Cursor 也能使用相同的 Agent 配置和对话历史，可以使用自动恢复脚本：

#### 在项目打开时自动检查

运行自动恢复脚本（会提示确认）：

```bash
cd .cursor
./auto_restore_agent_config.sh
```

**功能特点**：
- ✅ 自动检测是否需要恢复配置
- ✅ 比较时间戳，只在新配置时提示
- ✅ 恢复前需要人工确认，避免意外覆盖
- ✅ 显示将恢复的内容详情

#### 手动同步流程

**首次设置（在当前电脑）**：

```bash
cd .cursor
./sync_agent_config.sh
```

这会将以下内容同步到 `.cursor/agent-config/`：
- MCP 服务器配置（`mcps/`）
- Agent 对话历史（`agent-transcripts/`）

**在另一台电脑上恢复**：

```bash
cd .cursor
./restore_agent_config.sh
```

或者使用自动恢复（推荐）：

```bash
cd .cursor
./auto_restore_agent_config.sh  # 会提示确认
```

### 📝 其他同步方式（如果项目目录未同步）

如果项目目录没有自动同步，可以使用以下方式：

#### 方法一：使用 Git
```bash
# 在另一台电脑上
git pull  # 拉取最新更改，包括 .cursor/ 目录
```

#### 方法二：手动复制
```bash
# 从源电脑复制 .cursor/ 目录到目标电脑的项目目录
cp -r /path/to/source/.cursor /path/to/target/
```

## 📝 使用建议

1. **项目规则**：可以在此目录创建 `rules.md` 文件，定义项目特定的 AI 助手行为规则
2. **编辑器设置**：可以创建 `settings.json` 覆盖全局设置
3. **定期同步**：当 Agent 配置有更新时，记得运行 `sync_agent_config.sh` 同步
4. **自动恢复**：在另一台电脑上打开项目时，运行 `auto_restore_agent_config.sh` 自动恢复配置

## ⚠️ 注意事项

- 不要在此目录存放敏感信息（API Key、密码等）
- 确保设置文件不包含个人隐私信息
- 大型文件建议使用 `.gitignore` 排除
- Agent 对话历史可能包含项目相关信息，请确保可以分享

## 🚀 快速开始

### 在当前电脑（首次设置）

```bash
# 同步 Agent 配置到项目目录
cd .cursor
./sync_agent_config.sh
```

### 在另一台电脑（打开项目后）

```bash
# 自动检测并恢复（推荐，会提示确认）
cd .cursor
./auto_restore_agent_config.sh

# 或直接恢复（不提示）
cd .cursor
./restore_agent_config.sh
```

然后重启 Cursor，Agent 配置和对话历史就会恢复。
