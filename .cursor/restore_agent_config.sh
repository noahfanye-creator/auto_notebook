#!/bin/bash
# restore_agent_config.sh - 从项目目录恢复 Agent 配置和对话历史

# 获取项目根目录
PROJECT_ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
CURSOR_DIR="$PROJECT_ROOT/.cursor"
AGENT_CONFIG_DIR="$CURSOR_DIR/agent-config"

# 获取当前电脑的项目配置路径
PROJECT_NAME=$(echo "$PROJECT_ROOT" | tr '/' '-' | sed 's/^-//')
CURSOR_PROJECT_DIR="$HOME/.cursor/projects/$PROJECT_NAME"

echo "🔄 恢复 Agent 配置和对话历史"
echo "项目路径: $PROJECT_ROOT"
echo "Cursor 项目配置: $CURSOR_PROJECT_DIR"
echo ""

# 检查源目录是否存在
if [ ! -d "$AGENT_CONFIG_DIR" ]; then
    echo "❌ 未找到 Agent 配置目录: $AGENT_CONFIG_DIR"
    echo "   请先在源电脑上运行 sync_agent_config.sh"
    exit 1
fi

# 创建目标目录
mkdir -p "$CURSOR_PROJECT_DIR/mcps"
mkdir -p "$CURSOR_PROJECT_DIR/agent-transcripts"

# 1. 恢复 MCP 配置
if [ -d "$AGENT_CONFIG_DIR/mcps" ]; then
    echo "📦 恢复 MCP 配置..."
    cp -r "$AGENT_CONFIG_DIR/mcps"/* "$CURSOR_PROJECT_DIR/mcps/" 2>/dev/null
    echo "   ✅ MCP 配置已恢复"
else
    echo "   ⚠️  未找到 MCP 配置"
fi

# 2. 恢复 Agent 对话历史
if [ -d "$AGENT_CONFIG_DIR/agent-transcripts" ]; then
    echo "💬 恢复 Agent 对话历史..."
    cp -r "$AGENT_CONFIG_DIR/agent-transcripts"/* "$CURSOR_PROJECT_DIR/agent-transcripts/" 2>/dev/null
    echo "   ✅ Agent 对话历史已恢复"
else
    echo "   ⚠️  未找到 Agent 对话历史"
fi

echo ""
echo "✅ 恢复完成！"
echo "🔄 请重启 Cursor 以使配置生效"
