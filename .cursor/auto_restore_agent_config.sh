#!/bin/bash
# auto_restore_agent_config.sh - 自动检测并提示恢复 Agent 配置（需要确认）

# 获取项目根目录
PROJECT_ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
CURSOR_DIR="$PROJECT_ROOT/.cursor"
AGENT_CONFIG_DIR="$CURSOR_DIR/agent-config"

# 获取当前电脑的项目配置路径
PROJECT_NAME=$(echo "$PROJECT_ROOT" | tr '/' '-' | sed 's/^-//')
CURSOR_PROJECT_DIR="$HOME/.cursor/projects/$PROJECT_NAME"

echo "🔍 检查 Agent 配置同步状态..."
echo ""

# 检查源配置是否存在
if [ ! -d "$AGENT_CONFIG_DIR" ]; then
    echo "ℹ️  未找到项目中的 Agent 配置目录"
    echo "   这可能是首次在此电脑上打开项目"
    exit 0
fi

# 检查目标目录是否存在配置
LOCAL_CONFIG_EXISTS=false
if [ -d "$CURSOR_PROJECT_DIR/mcps" ] || [ -d "$CURSOR_PROJECT_DIR/agent-transcripts" ]; then
    LOCAL_CONFIG_EXISTS=true
fi

# 比较时间戳，判断是否需要恢复
NEEDS_RESTORE=false

if [ "$LOCAL_CONFIG_EXISTS" = false ]; then
    # 本地没有配置，需要恢复
    NEEDS_RESTORE=true
    echo "📋 检测结果：本地未找到 Agent 配置"
    echo "   项目目录中有可用的配置"
elif [ -d "$AGENT_CONFIG_DIR/mcps" ] || [ -d "$AGENT_CONFIG_DIR/agent-transcripts" ]; then
    # 检查源配置是否比本地更新
    if [ -d "$AGENT_CONFIG_DIR/agent-transcripts" ]; then
        SOURCE_LATEST=$(find "$AGENT_CONFIG_DIR/agent-transcripts" -type f -exec stat -f "%m" {} \; 2>/dev/null | sort -n | tail -1)
        if [ -d "$CURSOR_PROJECT_DIR/agent-transcripts" ]; then
            LOCAL_LATEST=$(find "$CURSOR_PROJECT_DIR/agent-transcripts" -type f -exec stat -f "%m" {} \; 2>/dev/null | sort -n | tail -1)
            if [ -n "$SOURCE_LATEST" ] && [ -n "$LOCAL_LATEST" ]; then
                if [ "$SOURCE_LATEST" -gt "$LOCAL_LATEST" ]; then
                    NEEDS_RESTORE=true
                    echo "📋 检测结果：项目中的配置比本地更新"
                fi
            fi
        else
            NEEDS_RESTORE=true
            echo "📋 检测结果：项目中有配置，但本地缺少部分配置"
        fi
    fi
fi

if [ "$NEEDS_RESTORE" = false ]; then
    echo "✅ Agent 配置已是最新，无需恢复"
    exit 0
fi

echo ""
echo "═══════════════════════════════════════════════════════════"
echo "🤖 Agent 配置恢复提示"
echo "═══════════════════════════════════════════════════════════"
echo ""
echo "检测到项目目录中有 Agent 配置需要恢复到本地 Cursor。"
echo ""
echo "📦 将恢复以下内容："
if [ -d "$AGENT_CONFIG_DIR/mcps" ]; then
    MCP_COUNT=$(find "$AGENT_CONFIG_DIR/mcps" -type f | wc -l | tr -d ' ')
    echo "   • MCP 服务器配置 ($MCP_COUNT 个文件)"
fi
if [ -d "$AGENT_CONFIG_DIR/agent-transcripts" ]; then
    TRANS_COUNT=$(find "$AGENT_CONFIG_DIR/agent-transcripts" -type f | wc -l | tr -d ' ')
    echo "   • Agent 对话历史 ($TRANS_COUNT 个对话)"
fi
echo ""
echo "📍 目标位置: $CURSOR_PROJECT_DIR"
echo ""
if [ "$LOCAL_CONFIG_EXISTS" = true ]; then
    echo "⚠️  警告：本地已存在配置，恢复将覆盖现有配置！"
    echo ""
fi
echo "═══════════════════════════════════════════════════════════"
echo ""
read -p "是否要恢复 Agent 配置？(y/N): " -n 1 -r
echo ""

if [[ ! $REPLY =~ ^[Yy]$ ]]; then
    echo "❌ 已取消恢复操作"
    echo ""
    echo "💡 提示："
    echo "   • 可以稍后手动运行: cd .cursor && ./restore_agent_config.sh"
    echo "   • 或者下次打开项目时会再次提示"
    exit 0
fi

echo ""
echo "🔄 开始恢复 Agent 配置..."
echo ""

# 调用恢复脚本
bash "$CURSOR_DIR/restore_agent_config.sh"

RESTORE_EXIT_CODE=$?

if [ $RESTORE_EXIT_CODE -eq 0 ]; then
    echo ""
    echo "✅ Agent 配置恢复完成！"
    echo ""
    echo "💡 提示：请重启 Cursor 以使配置生效"
else
    echo ""
    echo "❌ 恢复过程中出现错误，退出码: $RESTORE_EXIT_CODE"
    exit $RESTORE_EXIT_CODE
fi
