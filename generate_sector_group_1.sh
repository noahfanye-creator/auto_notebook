#!/bin/bash
# 第 1 组行业报告生成脚本
# 包含 9 个行业

cd "$(dirname "$0")"
python3 generate_sector_reports.py --sectors "BK1031 BK1015 BK1033 BK0478 BK0732 BK0734 BK1020 BK1032 BK1042"

echo ""
echo "第 1 组报告生成完成！"
