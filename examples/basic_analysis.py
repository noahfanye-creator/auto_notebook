#!/usr/bin/env python3
"""
基础股票分析示例
"""
import sys
import os
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from src.data.fetcher import get_stock_data

def main():
    print("📊 股票分析示例")
    print("-" * 40)
    
    # 股票列表
    symbols = ["AAPL", "MSFT", "GOOGL"]
    
    for symbol in symbols:
        print(f"\n分析 {symbol}:")
        df = get_stock_data(symbol, "1mo")
        
        if df is not None and not df.empty:
            latest_price = df['Close'].iloc[-1]
            highest = df['High'].max()
            lowest = df['Low'].min()
            avg_volume = df['Volume'].mean()
            
            print(f"  最新价格: ${latest_price:.2f}")
            print(f"  最高价: ${highest:.2f}")
            print(f"  最低价: ${lowest:.2f}")
            print(f"  平均成交量: {avg_volume:,.0f}")
    
    print("-" * 40)
    print("✅ 示例完成!")

if __name__ == "__main__":
    main()
