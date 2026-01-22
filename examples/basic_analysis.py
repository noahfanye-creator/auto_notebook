#!/usr/bin/env python3
"""
基础股票分析示例 - 改进版
"""
import sys
import os
import time
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from src.data.fetcher import get_stock_data, StockDataFetcher

def analyze_stock(symbol, period="1mo"):
    """分析单个股票"""
    print(f"\n🔍 分析 {symbol}:")
    print("-" * 30)
    
    try:
        # 使用带延迟的获取器
        fetcher = StockDataFetcher(delay_between_requests=1.5)
        df = fetcher.get_stock_data(symbol, period)
        
        if df is not None and not df.empty:
            latest_price = df['收盘'].iloc[-1]
            highest = df['最高'].max()
            lowest = df['最低'].min()
            avg_volume = df['成交量'].mean()
            
            # 计算涨跌幅
            if len(df) > 1:
                first_price = df['收盘'].iloc[0]
                change_percent = ((latest_price - first_price) / first_price) * 100
                change_text = f"{change_percent:+.2f}%"
            else:
                change_text = "N/A"
            
            print(f"  最新价格: ${latest_price:.2f}")
            print(f"  价格变化: {change_text}")
            print(f"  最高价: ${highest:.2f}")
            print(f"  最低价: ${lowest:.2f}")
            print(f"  平均成交量: {avg_volume:,.0f}")
            print(f"  数据天数: {len(df)}")
            
            return True
        else:
            print(f"  ⚠️  未获取到数据")
            return False
            
    except Exception as e:
        print(f"  ❌ 分析失败: {e}")
        return False

def main():
    print("📊 股票分析示例 - 改进版")
    print("=" * 50)
    print("注意: 为避免频率限制，每个请求间有1.5秒延迟")
    print("=" * 50)
    
    # 股票列表（分批处理）
    symbols_batch_1 = ["AAPL"]  # 先测试一个
    symbols_batch_2 = ["MSFT", "GOOGL", "TSLA"]  # 后续批次
    
    successful = 0
    total = len(symbols_batch_1) + len(symbols_batch_2)
    
    # 第一批
    for symbol in symbols_batch_1:
        if analyze_stock(symbol, "5d"):
            successful += 1
    
    print(f"\n⏳ 等待3秒避免频率限制...")
    time.sleep(3)
    
    # 第二批
    for symbol in symbols_batch_2:
        if analyze_stock(symbol, "5d"):
            successful += 1
        time.sleep(1)  # 批次间额外延迟
    
    print("-" * 50)
    print(f"✅ 分析完成! 成功: {successful}/{total}")
    print("\n💡 提示:")
    print("1. 如果遇到频率限制，请等待几分钟再试")
    print("2. 可以使用更长的延迟时间 (修改 delay_between_requests)")
    print("3. 考虑使用缓存减少请求")

if __name__ == "__main__":
    main()
