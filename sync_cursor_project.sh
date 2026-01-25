#!/bin/bash
# sync_cursor_project.sh - 同步 Cursor 项目配置和 Agent 设置

PROJECT_ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_NAME=$(echo "$PROJECT_ROOT" | tr '/' '-' | sed 's/^-//')

echo "🔄 Cursor 项目配置同步工具"
echo "项目路径: $PROJECT_ROOT"
echo "项目配置名: $PROJECT_NAME"
echo ""

# 备份当前项目的 Cursor 配置
BACKUP_DIR="$HOME/cursor-project-backup-$(date +%Y%m%d)"
mkdir -p "$BACKUP_DIR"

# 1. 备份全局项目配置
if [ -d ~/.cursor/projects/$PROJECT_NAME ]; then
    echo "📦 备份项目配置..."
    cp -r ~/.cursor/projects/$PROJECT_NAME "$BACKUP_DIR/" 2>/dev/null
    echo "   ✅ 项目配置已备份到: $BACKUP_DIR/$PROJECT_NAME"
    
    # 显示备份的内容
    echo ""
    echo "📋 备份内容："
    find "$BACKUP_DIR/$PROJECT_NAME" -type f | head -10
else
    echo "⚠️  未找到项目配置: ~/.cursor/projects/$PROJECT_NAME"
fi

# 2. 检查项目中的 .cursor/ 目录
if [ -d "$PROJECT_ROOT/.cursor" ]; then
    echo ""
    echo "📁 项目级 .cursor/ 目录存在"
    echo "   💡 提示：可以通过 Git 同步项目级设置"
    echo "   git add .cursor/"
    echo "   git commit -m 'Add Cursor project settings'"
    echo "   git push"
else
    echo ""
    echo "💡 提示：可以在项目中创建 .cursor/ 目录来存储项目级设置"
    echo "   mkdir -p .cursor"
    echo "   # 然后可以创建 .cursor/rules.md 等文件"
fi

# 3. 检查是否需要提交到 Git
if [ -d "$PROJECT_ROOT/.cursor" ] && [ -d "$PROJECT_ROOT/.git" ]; then
    if git ls-files --error-unmatch .cursor/ >/dev/null 2>&1; then
        echo ""
        echo "✅ .cursor/ 目录已在 Git 中跟踪"
    else
        echo ""
        echo "⚠️  .cursor/ 目录未在 Git 中跟踪"
        echo "   运行以下命令添加到 Git："
        echo "   git add .cursor/"
        echo "   git commit -m 'Add Cursor project settings'"
    fi
fi

echo ""
echo "📤 在另一台电脑上恢复："
echo "   1. 将 $BACKUP_DIR 复制到目标电脑"
echo "   2. 根据目标电脑的项目路径调整目录名"
echo "   3. 复制到 ~/.cursor/projects/<目标项目路径>/"
echo ""
echo "   示例："
echo "   cp -r $BACKUP_DIR/$PROJECT_NAME ~/.cursor/projects/<目标项目路径>/"
