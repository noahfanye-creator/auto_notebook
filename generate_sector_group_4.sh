#!/bin/bash
# 第 4 组行业报告生成脚本
# 包含 9 个行业

cd "$(dirname "$0")"
python3 generate_sector_reports.py --sectors "BK0545 BK0481 BK1016 BK0538 BK0736 BK0465 BK0480 BK0728 BK0733"

echo ""
echo "第 4 组报告生成完成！"
