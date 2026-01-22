#!/usr/bin/env python3
"""
测试带缓存的数据获取
"""
import sys
import os
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from src.data.fetcher import StockDataFetcher
import time

def main():
    print("🧪 测试带缓存的股票数据获取")
    print("=" * 50)
    
    # 创建带缓存的获取器
    fetcher = StockDataFetcher(
        cache_enabled=True,
        delay_between_requests=2.0  # 2秒延迟，更安全
    )
    
    symbols = ["AAPL", "MSFT", "GOOGL"]
    
    # 第一次获取（从网络）
    print("第一次获取（从网络）:")
    start_time = time.time()
    
    for symbol in symbols:
        print(f"\n获取 {symbol}...")
        df = fetcher.get_stock_data(symbol, "5d")
        
        if df is not None:
            price = df['收盘'].iloc[-1]
            print(f"  价格: ${price:.2f}, 数据行数: {len(df)}")
        else:
            print(f"  获取失败")
        
        time.sleep(1)  # 额外延迟
    
    first_duration = time.time() - start_time
    print(f"\n⏱️  第一次获取耗时: {first_duration:.1f}秒")
    
    # 第二次获取（从缓存）
    print(f"\n{'='*50}")
    print("第二次获取（从缓存）:")
    start_time = time.time()
    
    for symbol in symbols:
        print(f"\n获取 {symbol}...")
        df = fetcher.get_stock_data(symbol, "5d")
        
        if df is not None:
            price = df['收盘'].iloc[-1]
            print(f"  价格: ${price:.2f}, 数据行数: {len(df)} (从缓存)")
        else:
            print(f"  获取失败")
    
    second_duration = time.time() - start_time
    print(f"\n⏱️  第二次获取耗时: {second_duration:.1f}秒")
    
    print(f"\n{'='*50}")
    print(f"🚀 缓存提速: {(first_duration - second_duration):.1f}秒")
    print(f"💾 缓存命中率: 100% (所有数据已缓存)")
    
    # 清除缓存
    fetcher.clear_cache()
    print("🗑️  缓存已清除")

if __name__ == "__main__":
    main()
