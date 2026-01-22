#!/usr/bin/env python3
"""
快速开始示例
"""
import sys
sys.path.append('.')

from src.data.reliable_fetcher import ReliableStockFetcher

def main():
    print("🚀 股票分析机器人 - 快速开始")
    print("=" * 50)
    
    # 创建分析器
    print("1. 创建股票数据获取器...")
    fetcher = ReliableStockFetcher(mode='auto')  # 自动模式
    
    # 分析几个股票
    symbols = ['AAPL', 'MSFT', 'TSLA']
    
    print(f"\n2. 分析 {len(symbols)} 个热门股票:")
    print("-" * 50)
    
    results = []
    for symbol in symbols:
        print(f"\n📊 {symbol}:")
        df = fetcher.get_stock_data(symbol, '5d')
        
        if not df.empty:
            current = df['收盘'].iloc[-1]
            change = ((current - df['收盘'].iloc[0]) / df['收盘'].iloc[0] * 100)
            results.append((symbol, current, change))
    
    # 显示总结
    print("\n" + "=" * 50)
    print("📈 分析总结:")
    print("-" * 50)
    
    for symbol, price, change in results:
        trend = "📈" if change > 0 else "📉"
        print(f"{trend} {symbol}: ${price:.2f} ({change:+.2f}%)")
    
    print("\n" + "=" * 50)
    print("✅ 快速开始示例完成!")
    print("\n💡 下一步:")
    print("  运行: python main_simple.py --symbol AAPL")
    print("  运行: python main_simple.py --symbol MSFT --mode mock")
    print("=" * 50)

if __name__ == "__main__":
    main()
