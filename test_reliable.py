#!/usr/bin/env python3
"""
可靠测试脚本 - 不会卡住或无限循环
"""
import sys
import os
sys.path.append('.')

print("=" * 60)
print("🧪 可靠股票分析测试")
print("=" * 60)

# 测试1: 模拟数据模式（保证工作）
print("\n1. 测试模拟数据模式 (保证工作):")
print("-" * 40)

from src.data.reliable_fetcher import get_stock_data

# 使用模拟数据
print("🎮 模式: 模拟数据")
df_mock = get_stock_data('AAPL', '5d', mode='mock')

if not df_mock.empty:
    print(f"✅ 模拟数据测试成功!")
    print(f"📊 生成 {len(df_mock)} 条模拟数据")
    print(f"💰 模拟价格: ${df_mock['收盘'].iloc[-1]:.2f}")

# 测试2: 自动模式
print("\n\n2. 测试自动模式 (尝试真实，失败用模拟):")
print("-" * 40)

print("🤖 模式: 自动 (推荐)")
df_auto = get_stock_data('MSFT', '5d', mode='auto')

# 测试3: 多个股票
print("\n\n3. 测试多个股票分析:")
print("-" * 40)

symbols = ['AAPL', 'GOOGL', 'TSLA', '000001.SZ', '600519.SH']
print(f"分析 {len(symbols)} 个股票:")

for symbol in symbols:
    df = get_stock_data(symbol, '5d', mode='auto')
    if not df.empty:
        price = df['收盘'].iloc[-1]
        change = ((df['收盘'].iloc[-1] - df['收盘'].iloc[0]) / df['收盘'].iloc[0] * 100)
        print(f"  {symbol}: ${price:.2f} ({change:+.2f}%)")

print("\n" + "=" * 60)
print("🎉 所有测试完成!")
print("💡 提示:")
print("  - 使用 mode='mock' 进行开发测试")
print("  - 使用 mode='auto' 进行生产环境")
print("  - 使用 mode='real' 强制尝试真实数据")
print("=" * 60)
