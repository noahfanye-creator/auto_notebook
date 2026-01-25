#!/bin/bash
# 第 6 组行业报告生成脚本
# 包含 9 个行业

cd "$(dirname "$0")"
python3 generate_sector_reports.py --sectors "BK0738 BK1040 BK1037 BK0740 BK0451 BK0425 BK0470 BK0428 BK0482"

echo ""
echo "第 6 组报告生成完成！"
