#!/bin/bash
# 批量运行所有行业报告生成脚本

cd "$(dirname "$0")"

echo "=========================================="
echo "开始批量生成行业板块指数报告"
echo "总共10组，86个行业"
echo "=========================================="
echo ""

# 记录开始时间
start_time=$(date +%s)

# 依次运行每组脚本
for i in {1..10}; do
    echo ""
    echo "=========================================="
    echo "正在运行第 $i 组..."
    echo "=========================================="
    echo ""
    
    ./generate_sector_group_${i}.sh
    
    if [ $? -eq 0 ]; then
        echo ""
        echo "✓ 第 $i 组完成"
    else
        echo ""
        echo "✗ 第 $i 组执行出错"
    fi
    
    echo ""
    echo "等待5秒后继续下一组..."
    sleep 5
done

# 计算总耗时
end_time=$(date +%s)
duration=$((end_time - start_time))
hours=$((duration / 3600))
minutes=$(((duration % 3600) / 60))
seconds=$((duration % 60))

echo ""
echo "=========================================="
echo "所有报告生成完成！"
echo "总耗时: ${hours}小时 ${minutes}分钟 ${seconds}秒"
echo "=========================================="
