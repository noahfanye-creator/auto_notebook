#!/bin/bash
# sync_agent_config.sh - 同步 Agent 配置和对话历史到项目目录

# 获取项目根目录
PROJECT_ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
CURSOR_DIR="$PROJECT_ROOT/.cursor"

# 获取当前电脑的项目配置路径
# macOS: ~/.cursor/projects/Users-username-path-to-project/
PROJECT_NAME=$(echo "$PROJECT_ROOT" | tr '/' '-' | sed 's/^-//')
CURSOR_PROJECT_DIR="$HOME/.cursor/projects/$PROJECT_NAME"

echo "🔄 同步 Agent 配置和对话历史"
echo "项目路径: $PROJECT_ROOT"
echo "Cursor 项目配置: $CURSOR_PROJECT_DIR"
echo ""

# 创建目标目录
mkdir -p "$CURSOR_DIR/agent-config/mcps"
mkdir -p "$CURSOR_DIR/agent-config/agent-transcripts"

# 1. 同步 MCP 配置
if [ -d "$CURSOR_PROJECT_DIR/mcps" ]; then
    echo "📦 同步 MCP 配置..."
    cp -r "$CURSOR_PROJECT_DIR/mcps"/* "$CURSOR_DIR/agent-config/mcps/" 2>/dev/null
    echo "   ✅ MCP 配置已同步到项目目录"
else
    echo "   ⚠️  未找到 MCP 配置"
fi

# 2. 同步 Agent 对话历史
if [ -d "$CURSOR_PROJECT_DIR/agent-transcripts" ]; then
    echo "💬 同步 Agent 对话历史..."
    cp -r "$CURSOR_PROJECT_DIR/agent-transcripts"/* "$CURSOR_DIR/agent-config/agent-transcripts/" 2>/dev/null
    echo "   ✅ Agent 对话历史已同步到项目目录"
else
    echo "   ⚠️  未找到 Agent 对话历史"
fi

echo ""
echo "✅ 同步完成！"
echo "📁 配置已保存到: $CURSOR_DIR/agent-config/"
echo ""
echo "💡 这些文件会随项目目录自动同步到另一台电脑"
echo "   在另一台电脑上运行 restore_agent_config.sh 来恢复配置"
