#!/usr/bin/env python3
"""
测试真实数据获取（带重试和回退）
"""
import sys
import os
import time
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from src.data.fetcher import StockDataFetcher

def test_with_retry(symbol, max_attempts=3):
    """带重试的数据获取"""
    for attempt in range(max_attempts):
        print(f"\n尝试 {attempt + 1}/{max_attempts}...")
        
        # 每次增加延迟
        delay = 5.0 * (attempt + 1)
        fetcher = StockDataFetcher(
            delay_between_requests=delay,
            use_mock=False  # 尝试真实数据
        )
        
        try:
            df = fetcher.get_stock_data(symbol, '5d')
            if df is not None and not df.empty:
                return df, "真实数据"
        except Exception as e:
            print(f"  尝试失败: {e}")
        
        time.sleep(delay)  # 等待后重试
    
    # 所有重试失败，使用模拟数据
    print("\n所有重试失败，使用模拟数据...")
    fetcher = StockDataFetcher(use_mock=True)
    df = fetcher.get_stock_data(symbol, '5d')
    return df, "模拟数据"

def main():
    print("📡 测试真实股票数据获取")
    print("=" * 50)
    print("注意: 如果遇到频率限制，将使用模拟数据")
    print("=" * 50)
    
    symbol = "AAPL"
    print(f"测试股票: {symbol}")
    
    df, source = test_with_retry(symbol)
    
    if df is not None:
        print(f"\n✅ 成功! 数据来源: {source}")
        print(f"📊 {symbol} 数据:")
        print(f"  最新价格: ${df['收盘'].iloc[-1]:.2f}")
        print(f"  价格范围: ${df['最低'].min():.2f} - ${df['最高'].max():.2f}")
        print(f"  数据天数: {len(df)}")
        print(f"  总成交量: {df['成交量'].sum():,.0f}")
    else:
        print("\n❌ 完全失败，无法获取数据")
    
    print("\n" + "=" * 50)
    print("💡 提示: 如果频繁遇到频率限制，可以:")
    print("1. 等待一段时间后再试")
    print("2. 使用模拟数据进行开发测试")
    print("3. 实现数据缓存减少请求")

if __name__ == "__main__":
    main()
