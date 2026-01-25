#!/bin/bash
# 第 9 组行业报告生成脚本
# 包含 9 个行业

cd "$(dirname "$0")"
python3 generate_sector_reports.py --sectors "BK0438 BK1017 BK0473 BK0427 BK1030 BK0485 BK0726 BK0477 BK1028"

echo ""
echo "第 9 组报告生成完成！"
