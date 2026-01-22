#!/usr/bin/env python3
"""
简单测试脚本 - 避免命令行转义问题
"""
import sys
import os
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from src.data.fetcher import get_stock_data

def main():
    print("🧪 简单数据获取测试")
    print("=" * 40)
    
    # 使用模拟数据模式（避免频率限制）
    df = get_stock_data('AAPL', '5d', use_mock=True)
    
    if df is not None:
        print("✅ 成功获取 AAPL 数据 (模拟模式)")
        print(f"   数据行数: {len(df)}")
        print(f"   最新收盘价: ${df['收盘'].iloc[-1]:.2f}")
        print(f"   最高价: ${df['最高'].max():.2f}")
        print(f"   最低价: ${df['最低'].min():.2f}")
        print(f"   时间范围: {df.index[0].date()} 到 {df.index[-1].date()}")
    else:
        print("❌ 获取数据失败")
    
    print("=" * 40)

if __name__ == "__main__":
    main()
