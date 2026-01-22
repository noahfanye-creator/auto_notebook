#!/usr/bin/env python3
"""
离线测试 - 使用模拟数据进行开发和测试
"""
import sys
import os
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from src.data.fetcher import get_stock_data, StockDataFetcher
import pandas as pd

def test_mock_data():
    """测试模拟数据"""
    print("🧪 测试模拟数据模式")
    print("=" * 50)
    
    # 使用模拟数据
    fetcher = StockDataFetcher(use_mock=True, cache_enabled=True)
    
    symbols = ["AAPL", "MSFT", "GOOGL", "TSLA", "000001.SZ", "600519.SH"]
    
    for symbol in symbols:
        print(f"\n📊 分析 {symbol}:")
        print("-" * 30)
        
        df = fetcher.get_stock_data(symbol, "1mo")
        
        if df is not None and not df.empty:
            latest_price = df['收盘'].iloc[-1]
            first_price = df['收盘'].iloc[0]
            change_pct = ((latest_price - first_price) / first_price * 100)
            
            print(f"  模拟价格: ${latest_price:.2f}")
            print(f"  价格变化: {change_pct:+.2f}%")
            print(f"  最高价: ${df['最高'].max():.2f}")
            print(f"  最低价: ${df['最低'].min():.2f}")
            print(f"  平均成交量: {df['成交量'].mean():,.0f}")
            print(f"  数据天数: {len(df)}")
        else:
            print("  ❌ 获取数据失败")
    
    print("\n" + "=" * 50)
    print("✅ 模拟数据测试完成!")
    print("💡 可以在没有网络或避免频率限制时使用模拟数据")

def test_mixed_mode():
    """测试混合模式（优先真实数据，失败时使用模拟）"""
    print("\n\n🧪 测试混合模式")
    print("=" * 50)
    print("尝试获取真实数据，失败时使用模拟数据")
    print("=" * 50)
    
    # 尝试获取真实数据（可能因频率限制失败）
    try:
        print("尝试获取真实 AAPL 数据（可能需要等待）...")
        fetcher = StockDataFetcher(
            delay_between_requests=5.0,  # 5秒延迟
            use_mock=False
        )
        
        df = fetcher.get_stock_data("AAPL", "5d")
        
        if df is not None:
            print(f"✅ 成功获取真实数据!")
            source = "真实数据"
        else:
            print("⚠️  真实数据获取失败，使用模拟数据")
            fetcher.use_mock = True
            df = fetcher.get_stock_data("AAPL", "5d")
            source = "模拟数据"
            
    except Exception as e:
        print(f"❌ 获取失败: {e}")
        print("使用模拟数据...")
        fetcher = StockDataFetcher(use_mock=True)
        df = fetcher.get_stock_data("AAPL", "5d")
        source = "模拟数据"
    
    if df is not None:
        print(f"\n📈 {source} - AAPL:")
        print(f"  数据来源: {source}")
        print(f"  最新价格: ${df['收盘'].iloc[-1]:.2f}")
        print(f"  数据范围: {df.index[0].date()} 到 {df.index[-1].date()}")
        print(f"  数据点数: {len(df)}")
    
    print("\n" + "=" * 50)
    print("✅ 混合模式测试完成!")

if __name__ == "__main__":
    test_mock_data()
    test_mixed_mode()
