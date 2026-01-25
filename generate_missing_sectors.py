#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
生成缺失的行业报告
检查已生成的报告，只生成缺失的行业
"""
import os
import sys
import json
import glob
from generate_sector_reports import generate_sector_report

# 读取行业代码对照表
with open('config/sector_index_map.json', 'r', encoding='utf-8') as f:
    sector_map = json.load(f)

code_to_name = sector_map.get('code_to_name', {})
all_sectors = list(code_to_name.keys())

# 查找已生成的报告
existing_reports = set()
for pdf_file in glob.glob('reports/**/*行业指数分析报告.pdf', recursive=True):
    basename = os.path.basename(pdf_file)
    # 提取行业代码（格式：行业名称_BKXXXX_行业指数分析报告.pdf）
    parts = basename.split('_')
    if len(parts) >= 2:
        code = parts[1]
        if code.startswith('BK'):
            existing_reports.add(code)

print(f"已生成的报告: {len(existing_reports)} 个")
print(f"总行业数: {len(all_sectors)} 个")
print(f"缺失: {len(all_sectors) - len(existing_reports)} 个")

# 找出缺失的行业
missing_sectors = [s for s in all_sectors if s not in existing_reports]

if not missing_sectors:
    print("\n✓ 所有行业报告已生成！")
    sys.exit(0)

print(f"\n缺失的行业 ({len(missing_sectors)} 个):")
for code in missing_sectors[:10]:
    print(f"  - {code_to_name[code]} ({code})")
if len(missing_sectors) > 10:
    print(f"  ... 还有 {len(missing_sectors) - 10} 个")

# 创建输出文件夹
from datetime import datetime
timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
output_folder = os.path.join("reports", f"sector_reports_{timestamp}")
os.makedirs(output_folder, exist_ok=True)
print(f"\n输出文件夹: {output_folder}")

# 生成缺失的报告
print(f"\n开始生成 {len(missing_sectors)} 个缺失的行业报告...\n")

successful = []
failed = []

for i, sector_code in enumerate(missing_sectors, 1):
    print(f"\n[{i}/{len(missing_sectors)}] 生成 {code_to_name[sector_code]} ({sector_code})...")
    try:
        if generate_sector_report(sector_code, output_folder):
            successful.append(sector_code)
        else:
            failed.append(sector_code)
    except Exception as e:
        print(f"❌ 错误: {e}")
        failed.append(sector_code)
    
    # 每10个行业休息一下，避免API限流
    if i % 10 == 0:
        print("\n休息5秒...")
        import time
        time.sleep(5)

# 总结
print(f"\n{'='*70}")
print(f"📊 生成完成!")
print(f"{'='*70}")
print(f"✅ 成功: {len(successful)} 个")
print(f"❌ 失败: {len(failed)} 个")

if failed:
    print(f"\n失败的行业:")
    for code in failed:
        print(f"  - {code_to_name[code]} ({code})")
