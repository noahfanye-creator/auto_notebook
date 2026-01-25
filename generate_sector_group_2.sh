#!/bin/bash
# 第 2 组行业报告生成脚本
# 包含 9 个行业

cd "$(dirname "$0")"
python3 generate_sector_reports.py --sectors "BK1027 BK0479 BK1038 BK0486 BK0448 BK0546 BK0447 BK0727 BK0457"

echo ""
echo "第 2 组报告生成完成！"
