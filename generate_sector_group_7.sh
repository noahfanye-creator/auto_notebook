#!/bin/bash
# 第 7 组行业报告生成脚本
# 包含 9 个行业

cd "$(dirname "$0")"
python3 generate_sector_reports.py --sectors "BK0739 BK0436 BK0539 BK0456 BK1029 BK0730 BK0471 BK0440 BK0429"

echo ""
echo "第 7 组报告生成完成！"
