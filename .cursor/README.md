# Cursor 项目级设置

此目录用于存储项目特定的 Cursor 编辑器设置，可以通过 Git 同步到其他设备。

## 📁 目录说明

- `rules.md` 或 `.cursorrules` - 项目特定的 Cursor 规则
- `settings.json` - 项目特定的编辑器设置（可选）
- 其他项目级配置文件

## 🔄 同步说明

### ✅ 自动同步（如果项目目录已同步）

**如果你的项目目录已经通过文件同步服务（iCloud、Dropbox、OneDrive、rsync 等）在两台电脑间同步，那么 `.cursor/` 目录会自动同步！**

这意味着：
- ✅ 项目级 Cursor 设置会自动同步
- ✅ 项目规则文件会自动同步
- ✅ 项目特定的编辑器设置会自动同步

**无需额外操作**，只需确保项目目录同步正常即可。

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

#### 方法三：使用同步脚本
```bash
# 使用项目根目录的 sync_cursor_project.sh 脚本
./sync_cursor_project.sh
```

### ⚠️ 重要提示：Agent 配置需要单独同步

**项目级设置**（`.cursor/` 目录）会随项目文件自动同步 ✅

**但是，Agent 配置和对话历史**存储在 `~/.cursor/projects/` 中，**不会自动同步**，需要手动处理：

```bash
# 使用同步脚本备份 Agent 配置
./sync_cursor_project.sh

# 然后在另一台电脑上恢复
# 根据实际项目路径调整目录名
cp -r ~/cursor-backup/Users-felix-Documents-stock-analysis-bot \
     ~/.cursor/projects/<目标项目路径>/
```

详细说明请参考项目根目录的 `CURSOR_SYNC_GUIDE.md`。

## 🤖 Agent 配置和对话历史同步

为了让另一台电脑上的 Cursor 也能使用相同的 Agent 配置和对话历史，需要同步这些内容：

### 首次设置（在当前电脑）

运行同步脚本，将 Agent 配置复制到项目目录：

```bash
cd .cursor
./sync_agent_config.sh
```

这会将以下内容同步到 `.cursor/agent-config/`：
- MCP 服务器配置（`mcps/`）
- Agent 对话历史（`agent-transcripts/`）

这些文件会随项目目录自动同步到另一台电脑。

### 在另一台电脑上恢复

当项目目录同步到另一台电脑后，运行恢复脚本：

```bash
cd .cursor
./restore_agent_config.sh
```

然后重启 Cursor，Agent 配置和对话历史就会恢复。

### 自动同步流程

1. **当前电脑**：运行 `sync_agent_config.sh` → 配置保存到项目目录
2. **文件同步**：项目目录自动同步（通过 iCloud/Dropbox 等）
3. **另一台电脑**：运行 `restore_agent_config.sh` → 配置恢复到 Cursor
4. **完成**：两台电脑的 Agent 配置和对话历史保持一致

## 📝 使用建议

1. **项目规则**：可以在此目录创建 `rules.md` 文件，定义项目特定的 AI 助手行为规则
2. **编辑器设置**：可以创建 `settings.json` 覆盖全局设置
3. **定期同步**：当 Agent 配置有更新时，记得运行 `sync_agent_config.sh` 同步

## ⚠️ 注意事项

- 不要在此目录存放敏感信息（API Key、密码等）
- 确保设置文件不包含个人隐私信息
- 大型文件建议使用 `.gitignore` 排除
