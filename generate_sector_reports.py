#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
生成行业板块指数报告
支持批量生成多个行业的报告
"""
import os
import sys
import json
import argparse
import time
import pandas as pd
from datetime import datetime

# 添加项目路径
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from github_stock_bot import (
    get_sector_indices_data,
    create_indices_charts,
    create_pdf_with_market_analysis,
    calculate_technical_indicators,
    load_sector_index_map
)

def generate_sector_report(sector_code, output_folder, use_dummy_stock=True):
    """
    生成单个行业板块指数报告
    
    Args:
        sector_code: 行业代码（如BK1031）
        output_folder: 输出文件夹
        use_dummy_stock: 是否使用虚拟股票代码（用于兼容现有报告格式）
    """
    sector_map = load_sector_index_map()
    code_to_name = sector_map.get('code_to_name', {})
    sector_name = code_to_name.get(sector_code, sector_code)
    
    print(f"\n{'='*70}")
    print(f"生成行业报告: {sector_name} ({sector_code})")
    print(f"{'='*70}")
    
    # 创建临时目录
    timestamp = datetime.now().strftime('%H%M%S')
    temp_dir = os.path.join(output_folder, f"temp_{sector_code}_{timestamp}")
    os.makedirs(temp_dir, exist_ok=True)
    print(f"📁 临时目录: {temp_dir}")
    
    # 获取行业指数数据（带重试机制）
    print(f"\n1️⃣  获取行业板块指数数据...")
    max_retries = 3
    retry_delay = 5  # 秒
    sector_indices_data = {}
    
    for attempt in range(max_retries):
        try:
            sector_indices_data = get_sector_indices_data(sector_code, count=150)
            if sector_indices_data:
                break
        except Exception as e:
            if attempt < max_retries - 1:
                print(f"    ⚠️  获取失败，{retry_delay}秒后重试 ({attempt + 1}/{max_retries})...")
                time.sleep(retry_delay)
            else:
                print(f"    ❌ 重试{max_retries}次后仍失败: {e}")
    
    if not sector_indices_data:
        print(f"❌ 无法获取行业指数数据，跳过")
        try:
            os.rmdir(temp_dir)
        except:
            pass
        return False
    
    print(f"✅ 获取到 {len(sector_indices_data)} 个行业指数数据")
    
    # 生成行业指数图表（日线）
    print(f"\n2️⃣  生成图表...")
    charts_count = create_indices_charts(sector_indices_data, temp_dir)
    print(f"✅ 生成 {charts_count} 个行业指数图表")
    
    # 创建虚拟股票数据（用于兼容报告格式）
    stock_data_map = {}
    if use_dummy_stock:
        # 使用行业指数的第一个数据作为虚拟股票数据
        first_sector = list(sector_indices_data.values())[0]
        df_day = first_sector['data'].copy()
        stock_data_map['day'] = df_day
        
        # 生成周线和月线数据
        if df_day is not None and not df_day.empty:
            from github_stock_bot import resample_kline_data, calculate_technical_indicators
            print("  生成周线数据...")
            df_week = resample_kline_data(df_day, 'W')
            if df_week is not None:
                stock_data_map['week'] = df_week
                print(f"    ✓ 周线: {len(df_week)} 条数据")
            
            print("  生成月线数据...")
            df_month = resample_kline_data(df_day, 'M')
            if df_month is not None:
                stock_data_map['month'] = df_month
                print(f"    ✓ 月线: {len(df_month)} 条数据")
        
        # 尝试获取30分钟和5分钟数据
        try:
            import akshare as ak
            print("  获取30分钟数据...")
            try:
                df_30m = ak.stock_board_industry_hist_min_em(symbol=sector_name, period="30")
                if df_30m is not None and not df_30m.empty:
                    # 标准化列名
                    df_30m = df_30m.rename(columns={
                        '时间': 'Date',
                        '开盘': 'Open',
                        '收盘': 'Close',
                        '最高': 'High',
                        '最低': 'Low',
                        '成交量': 'Volume'
                    })
                    df_30m['Date'] = pd.to_datetime(df_30m['Date'])
                    df_30m.set_index('Date', inplace=True)
                    df_30m.sort_index(inplace=True)
                    df_30m = df_30m.tail(100)  # 限制数据量
                    df_30m = calculate_technical_indicators(df_30m)
                    stock_data_map['30m'] = df_30m
                    print(f"    ✓ 30分钟: {len(df_30m)} 条数据")
                else:
                    print("    ⚠️  30分钟数据为空")
            except Exception as e:
                print(f"    ⚠️  30分钟数据获取失败: {str(e)[:50]}")
            
            print("  获取5分钟数据...")
            try:
                df_5m = ak.stock_board_industry_hist_min_em(symbol=sector_name, period="5")
                if df_5m is not None and not df_5m.empty:
                    # 标准化列名
                    df_5m = df_5m.rename(columns={
                        '时间': 'Date',
                        '开盘': 'Open',
                        '收盘': 'Close',
                        '最高': 'High',
                        '最低': 'Low',
                        '成交量': 'Volume'
                    })
                    df_5m['Date'] = pd.to_datetime(df_5m['Date'])
                    df_5m.set_index('Date', inplace=True)
                    df_5m.sort_index(inplace=True)
                    df_5m = df_5m.tail(100)  # 限制数据量
                    df_5m = calculate_technical_indicators(df_5m)
                    stock_data_map['5m'] = df_5m
                    print(f"    ✓ 5分钟: {len(df_5m)} 条数据")
                else:
                    print("    ⚠️  5分钟数据为空")
            except Exception as e:
                print(f"    ⚠️  5分钟数据获取失败: {str(e)[:50]}")
        except Exception as e:
            print(f"  ⚠️  分钟数据接口不可用: {str(e)[:50]}")
        
        # 创建元数据
        stock_data_map['_meta'] = {
            'generated_at': datetime.now().strftime('%Y-%m-%d %H:%M:%S'),
            'data_source': 'AKShare(同花顺行业板块)',
            'index_source': 'AKShare(同花顺行业板块)',
            'one_min_source': '无数据',
            'indicator_params': {
                'ma_windows': [5, 10, 20, 60, 250],
                'macd': [12, 26, 9],
                'rsi': 14,
                'boll': 20,
                'kdj': 9,
                'wr': 14,
                'volume_ma': [5, 10]
            }
        }
        
        # 生成行业指数的日线、周线、月线图表
        if stock_data_map.get('day'):
            from github_stock_bot import create_candle_chart
            sector_charts_count = 0
            
            chart_configs = [
                ('day', stock_data_map.get('day'), f"{sector_name} 日线", 60),
                ('week', stock_data_map.get('week'), f"{sector_name} 周线", 60),
                ('month', stock_data_map.get('month'), f"{sector_name} 月线", 60),
                ('30m', stock_data_map.get('30m'), f"{sector_name} 30分钟", 100),
                ('5m', stock_data_map.get('5m'), f"{sector_name} 5分钟", 100),
            ]
            
            for key, df, title, max_points in chart_configs:
                if df is not None and len(df) >= 5:
                    img_path = os.path.join(temp_dir, f"{key}.png")
                    if create_candle_chart(df, title, img_path, max_points=max_points):
                        sector_charts_count += 1
            
            print(f"✅ 生成 {sector_charts_count} 个行业指数K线图表（日线/周线/月线）")
    
    # 生成PDF报告
    print(f"\n3️⃣  生成PDF报告...")
    safe_name = sector_name.replace('/', '_').replace('\\', '_')
    pdf_filename = f"{safe_name}_{sector_code}_行业指数分析报告.pdf"
    pdf_path = os.path.join(output_folder, pdf_filename)
    
    # 使用行业代码作为股票代码，行业名称作为股票名称
    success = create_pdf_with_market_analysis(
        sector_code, sector_name, stock_data_map, sector_indices_data, pdf_path, temp_dir
    )
    
    if success:
        file_size = os.path.getsize(pdf_path) / 1024
        print(f"✅ PDF生成成功: {pdf_filename}")
        print(f"📏 文件大小: {file_size:.1f} KB")
        
        # 清理临时目录
        try:
            import shutil
            shutil.rmtree(temp_dir)
            print(f"🧹 已清理临时目录")
        except:
            pass
        
        return True
    else:
        print(f"❌ PDF生成失败")
        return False

def main():
    parser = argparse.ArgumentParser(description='生成行业板块指数报告')
    parser.add_argument('--sectors', type=str, required=True, 
                       help='行业代码列表，用逗号或空格分隔，如: BK1031,BK1015 或 BK1031 BK1015')
    parser.add_argument('--output', type=str, default=None,
                       help='输出文件夹，默认为 reports/sector_reports_YYYYMMDD_HHMMSS')
    
    args = parser.parse_args()
    
    # 解析行业代码列表
    sectors = args.sectors.replace(',', ' ').split()
    sectors = [s.strip() for s in sectors if s.strip()]
    
    if not sectors:
        print("❌ 未指定行业代码")
        return
    
    print(f"📊 准备生成 {len(sectors)} 个行业报告")
    
    # 创建输出文件夹
    if args.output:
        output_folder = args.output
    else:
        timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
        current_dir = os.path.dirname(os.path.abspath(__file__))
        output_folder = os.path.join(current_dir, "reports", f"sector_reports_{timestamp}")
    
    os.makedirs(output_folder, exist_ok=True)
    print(f"📁 输出文件夹: {output_folder}")
    
    # 生成报告
    successful = []
    failed = []
    
    for sector_code in sectors:
        try:
            if generate_sector_report(sector_code, output_folder):
                successful.append(sector_code)
            else:
                failed.append(sector_code)
        except Exception as e:
            print(f"❌ 生成 {sector_code} 报告时出错: {e}")
            import traceback
            traceback.print_exc()
            failed.append(sector_code)
    
    # 总结
    print(f"\n{'='*70}")
    print(f"📊 批量生成完成!")
    print(f"{'='*70}")
    print(f"✅ 成功: {len(successful)} 个")
    print(f"❌ 失败: {len(failed)} 个")
    
    if failed:
        print(f"\n失败的行业:")
        for code in failed:
            print(f"  - {code}")

if __name__ == "__main__":
    main()
