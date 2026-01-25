#!/bin/bash
# 第 10 组行业报告生成脚本
# 包含 5 个行业

cd "$(dirname "$0")"
python3 generate_sector_reports.py --sectors "BK0437 BK0475 BK0729 BK0420 BK0474"

echo ""
echo "第 10 组报告生成完成！"
