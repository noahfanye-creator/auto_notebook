#!/bin/bash
# 第 3 组行业报告生成脚本
# 包含 9 个行业

cd "$(dirname "$0")"
python3 generate_sector_reports.py --sectors "BK1019 BK0737 BK0454 BK0910 BK0458 BK1039 BK1041 BK1044 BK0731"

echo ""
echo "第 3 组报告生成完成！"
