#!/bin/bash
# 第 8 组行业报告生成脚本
# 包含 9 个行业

cd "$(dirname "$0")"
python3 generate_sector_reports.py --sectors "BK0459 BK1035 BK0421 BK0725 BK0424 BK0433 BK0450 BK1045 BK0422"

echo ""
echo "第 8 组报告生成完成！"
