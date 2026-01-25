#!/bin/bash
# 第 5 组行业报告生成脚本
# 包含 9 个行业

cd "$(dirname "$0")"
python3 generate_sector_reports.py --sectors "BK0484 BK1018 BK0464 BK1043 BK0735 BK1036 BK1046 BK0476 BK1034"

echo ""
echo "第 5 组报告生成完成！"
