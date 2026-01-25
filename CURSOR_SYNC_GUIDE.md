# Cursor 设置同步指南

## 📋 需要同步的配置文件

### 1. 用户设置文件（macOS）
位置：`~/Library/Application Support/Cursor/User/`

需要同步的文件：
- `settings.json` - 编辑器设置
- `keybindings.json` - 快捷键绑定
- `snippets/` - 代码片段目录（如果有）

### 2. Cursor 全局配置（macOS）
位置：`~/.cursor/`

需要同步的内容：
- `skills-cursor/` - Cursor Skills 目录（自定义技能）
- `argv.json` - 启动参数配置（可选）

## 🔄 同步方法

### 方法一：手动复制（推荐）

#### 在源电脑（当前电脑）：
```bash
# 1. 创建备份目录
mkdir -p ~/cursor-settings-backup

# 2. 备份用户设置
cp -r ~/Library/Application\ Support/Cursor/User/* ~/cursor-settings-backup/

# 3. 备份 Cursor 全局配置（特别是 skills）
cp -r ~/.cursor/skills-cursor ~/cursor-settings-backup/ 2>/dev/null || true

# 4. 打包（可选）
cd ~/cursor-settings-backup
tar -czf cursor-settings-backup.tar.gz .
```

#### 在目标电脑（另一台电脑）：
```bash
# 1. 解压或复制文件到临时目录
# 假设你已经通过云盘/邮件等方式传输了文件

# 2. 恢复用户设置
cp -r ~/cursor-settings-backup/* ~/Library/Application\ Support/Cursor/User/

# 3. 恢复 Skills（如果存在）
cp -r ~/cursor-settings-backup/skills-cursor ~/.cursor/ 2>/dev/null || true

# 4. 重启 Cursor
```

### 方法二：使用云存储同步（推荐）

#### 使用 iCloud、Dropbox、OneDrive 等：

1. **创建符号链接**（在源电脑）：
```bash
# 创建同步目录
mkdir -p ~/iCloud/CursorSettings

# 移动设置文件到云盘
mv ~/Library/Application\ Support/Cursor/User/settings.json ~/iCloud/CursorSettings/
mv ~/Library/Application\ Support/Cursor/User/keybindings.json ~/iCloud/CursorSettings/

# 创建符号链接
ln -s ~/iCloud/CursorSettings/settings.json ~/Library/Application\ Support/Cursor/User/settings.json
ln -s ~/iCloud/CursorSettings/keybindings.json ~/Library/Application\ Support/Cursor/User/keybindings.json
```

2. **在目标电脑上**：
```bash
# 等待云盘同步完成后，创建符号链接
ln -s ~/iCloud/CursorSettings/settings.json ~/Library/Application\ Support/Cursor/User/settings.json
ln -s ~/iCloud/CursorSettings/keybindings.json ~/Library/Application\ Support/Cursor/User/keybindings.json
```

### 方法三：使用 Git 同步项目级设置和 Agent 配置（⭐推荐）

这是**最推荐的方法**，可以让同一项目在不同电脑上保持完全一致的 Cursor 设置和 Agent 配置。

#### 1. 项目级 Cursor 配置位置

Cursor 的项目级配置存储在：
- **项目内**：`.cursor/` 目录（可以提交到 Git）
- **全局项目配置**：`~/.cursor/projects/<项目路径>/`（需要手动同步）

#### 2. 需要同步的 Agent 和项目配置

**项目级配置**（可以提交到 Git）：
```bash
# 在项目根目录创建 .cursor 目录（如果不存在）
mkdir -p .cursor

# 可以在这里放置项目特定的 Cursor 配置
# 例如：.cursor/rules.md, .cursor/settings.json 等
```

**全局项目配置**（需要手动同步）：
位置：`~/.cursor/projects/Users-felix-Documents-stock-analysis-bot/`

包含：
- `mcps/` - MCP 服务器配置（如 cursor-ide-browser, cursor-browser-extension）
- `agent-transcripts/` - Agent 对话历史记录
- 其他项目特定的 Cursor 配置

#### 3. 同步步骤

**在源电脑（当前电脑）**：
```bash
# 1. 备份全局项目配置
PROJECT_NAME="Users-felix-Documents-stock-analysis-bot"
BACKUP_DIR="$HOME/cursor-project-backup"
mkdir -p "$BACKUP_DIR"

# 备份项目配置
cp -r ~/.cursor/projects/$PROJECT_NAME "$BACKUP_DIR/" 2>/dev/null

# 2. 如果项目中有 .cursor/ 目录，确保可以提交
# 检查 .gitignore 中是否忽略了 .cursor/
# 如果没有，可以添加到 Git
git add .cursor/
git commit -m "Add Cursor project settings"
```

**在目标电脑（另一台电脑）**：
```bash
# 1. 克隆项目（如果还没有）
git clone <your-repo-url>
cd stock-analysis-bot

# 2. 项目中的 .cursor/ 目录会自动同步（通过 Git）

# 3. 恢复全局项目配置
PROJECT_NAME="Users-felix-Documents-stock-analysis-bot"  # 根据实际路径调整
BACKUP_DIR="$HOME/cursor-project-backup"

# 创建目标目录（路径可能不同，需要根据实际项目路径调整）
mkdir -p ~/.cursor/projects/

# 复制配置（注意：路径可能需要根据目标电脑的实际路径调整）
cp -r "$BACKUP_DIR/$PROJECT_NAME" ~/.cursor/projects/ 2>/dev/null

# 或者，如果项目路径不同，需要手动调整目录名
# 例如：如果目标电脑项目路径是 /Users/username/projects/stock-analysis-bot
# 则目录名应该是 Users-username-projects-stock-analysis-bot
```

#### 4. 自动同步脚本

创建 `sync_cursor_project.sh`：
```bash
#!/bin/bash
# sync_cursor_project.sh - 同步 Cursor 项目配置

PROJECT_ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_NAME=$(echo "$PROJECT_ROOT" | tr '/' '-' | sed 's/^-//')

# 备份当前项目的 Cursor 配置
BACKUP_DIR="$HOME/cursor-project-backup-$(date +%Y%m%d)"
mkdir -p "$BACKUP_DIR"

if [ -d ~/.cursor/projects/$PROJECT_NAME ]; then
    cp -r ~/.cursor/projects/$PROJECT_NAME "$BACKUP_DIR/"
    echo "✅ 项目配置已备份到: $BACKUP_DIR/$PROJECT_NAME"
else
    echo "⚠️  未找到项目配置: ~/.cursor/projects/$PROJECT_NAME"
fi

# 如果项目中有 .cursor/ 目录，提示可以提交
if [ -d "$PROJECT_ROOT/.cursor" ]; then
    echo "📁 项目级 .cursor/ 目录存在，可以通过 Git 同步"
fi
```

#### 5. 使用 Git 同步项目级设置

**更新 .gitignore**：
```gitignore
# Cursor 项目级设置（允许提交到 Git，用于多设备同步）
# .cursor/  # 取消注释以允许项目级 Cursor 设置同步
```

**提交项目级设置**：
```bash
# 如果项目中有 .cursor/ 目录
git add .cursor/
git commit -m "Add Cursor project settings for multi-device sync"
git push
```

**在另一台电脑上**：
```bash
git pull  # 自动获取 .cursor/ 目录
```

## 📝 当前设置概览

### 用户设置 (`settings.json`)
```json
{
    "window.commandCenter": true
}
```

### 快捷键绑定 (`keybindings.json`)
- `Cmd+I` → 打开 Composer Mode Agent

### Skills 目录
位置：`~/.cursor/skills-cursor/`

包含的自定义技能：
- `create-rule/` - 创建 Cursor 规则
- `create-skill/` - 创建 Agent Skills
- `create-subagent/` - 创建子代理
- `migrate-to-skills/` - 迁移到技能
- `update-cursor-settings/` - 更新 Cursor 设置

### 项目级配置（当前项目）
位置：`~/.cursor/projects/Users-felix-Documents-stock-analysis-bot/`

包含：
- `mcps/` - MCP 服务器配置
  - `cursor-ide-browser/` - 浏览器 MCP 服务器
  - `cursor-browser-extension/` - 浏览器扩展 MCP 服务器
- `agent-transcripts/` - Agent 对话历史记录

## 🎯 项目级设置和 Agent 同步（重点）

### 为什么需要同步项目级设置？

当你在不同电脑上编辑同一个项目时，以下内容需要同步：
1. **项目特定的 Cursor 规则**（`.cursor/rules.md` 或 `.cursorrules`）
2. **Agent 配置和对话历史**
3. **MCP 服务器配置**（项目特定的 MCP 设置）
4. **工作区设置**（项目特定的编辑器设置）

### 最佳实践：使用 Git + 手动备份

**推荐方案**：
1. **项目级配置**（`.cursor/` 目录）→ 通过 Git 同步 ✅
2. **全局项目配置**（`~/.cursor/projects/`）→ 手动备份同步 📦
3. **Agent 对话历史** → 可选同步（通常不需要）

### 快速同步脚本（完整版）

创建 `sync_cursor_all.sh`：
```bash
#!/bin/bash
# sync_cursor_all.sh - 完整同步 Cursor 设置（用户设置 + 项目设置 + Agent）

BACKUP_DIR="$HOME/cursor-full-backup-$(date +%Y%m%d)"
mkdir -p "$BACKUP_DIR"

echo "📦 开始备份 Cursor 设置..."

# 1. 备份用户设置
echo "1️⃣  备份用户设置..."
cp -r ~/Library/Application\ Support/Cursor/User/* "$BACKUP_DIR/user-settings/" 2>/dev/null || mkdir -p "$BACKUP_DIR/user-settings"

# 2. 备份全局 Skills
echo "2️⃣  备份全局 Skills..."
if [ -d ~/.cursor/skills-cursor ]; then
    cp -r ~/.cursor/skills-cursor "$BACKUP_DIR/"
fi

# 3. 备份当前项目配置
echo "3️⃣  备份项目配置..."
PROJECT_ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_NAME=$(echo "$PROJECT_ROOT" | tr '/' '-' | sed 's/^-//')

if [ -d ~/.cursor/projects/$PROJECT_NAME ]; then
    cp -r ~/.cursor/projects/$PROJECT_NAME "$BACKUP_DIR/project-config/"
    echo "   ✅ 项目配置已备份: $PROJECT_NAME"
else
    echo "   ⚠️  未找到项目配置"
fi

# 4. 检查项目中的 .cursor/ 目录
if [ -d "$PROJECT_ROOT/.cursor" ]; then
    echo "4️⃣  项目级 .cursor/ 目录存在"
    echo "   💡 提示：可以通过 Git 同步项目级设置"
    echo "   git add .cursor/"
    echo "   git commit -m 'Add Cursor project settings'"
fi

echo ""
echo "✅ 备份完成！"
echo "📁 备份位置: $BACKUP_DIR"
echo ""
echo "📤 在另一台电脑上恢复："
echo "   1. 将 $BACKUP_DIR 复制到目标电脑"
echo "   2. 运行恢复脚本或手动复制文件"
```

## ⚠️ 注意事项

1. **不同操作系统路径不同**：
   - macOS: `~/Library/Application Support/Cursor/User/`
   - Windows: `%APPDATA%\Cursor\User\`
   - Linux: `~/.config/Cursor/User/`

2. **扩展插件**：
   - Cursor 的扩展插件通常需要单独安装
   - 可以通过 `code --list-extensions` 导出扩展列表（如果支持）

3. **敏感信息**：
   - 检查 `settings.json` 中是否包含 API Key 等敏感信息
   - 如有，请使用环境变量或加密存储

4. **版本兼容性**：
   - 确保两台电脑的 Cursor 版本相近
   - 某些设置可能在不同版本间不兼容

## 🚀 快速同步脚本

### macOS 备份脚本
```bash
#!/bin/bash
# backup_cursor_settings.sh

BACKUP_DIR="$HOME/cursor-settings-backup-$(date +%Y%m%d)"
mkdir -p "$BACKUP_DIR"

# 备份用户设置
cp -r ~/Library/Application\ Support/Cursor/User/* "$BACKUP_DIR/" 2>/dev/null

# 备份 Skills
if [ -d ~/.cursor/skills-cursor ]; then
    cp -r ~/.cursor/skills-cursor "$BACKUP_DIR/"
fi

echo "✅ 设置已备份到: $BACKUP_DIR"
```

### macOS 恢复脚本
```bash
#!/bin/bash
# restore_cursor_settings.sh

BACKUP_DIR="$1"

if [ -z "$BACKUP_DIR" ]; then
    echo "用法: $0 <备份目录路径>"
    exit 1
fi

# 恢复用户设置
cp -r "$BACKUP_DIR"/* ~/Library/Application\ Support/Cursor/User/ 2>/dev/null

# 恢复 Skills
if [ -d "$BACKUP_DIR/skills-cursor" ]; then
    cp -r "$BACKUP_DIR/skills-cursor" ~/.cursor/ 2>/dev/null
fi

echo "✅ 设置已恢复，请重启 Cursor"
```

## 📞 更多信息

- Cursor 官方文档：https://cursor.sh/docs
- 设置文件位置可能因版本而异，请以实际路径为准
