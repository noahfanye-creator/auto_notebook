#!/usr/bin/env python3
"""
简单可靠的股票分析机器人
"""
import argparse
from src.data.reliable_fetcher import get_stock_data

def main():
    parser = argparse.ArgumentParser(description='简单股票分析机器人')
    parser.add_argument('--symbol', type=str, required=True, help='股票代码')
    parser.add_argument('--period', type=str, default='1mo', help='数据周期')
    parser.add_argument('--mode', choices=['auto', 'mock', 'real'], 
                       default='auto', help='数据模式')
    
    args = parser.parse_args()
    
    print("=" * 50)
    print(f"📈 股票分析机器人 - {args.mode}模式")
    print("=" * 50)
    
    # 获取数据（总是成功）
    df = get_stock_data(args.symbol, args.period, args.mode)
    
    if not df.empty:
        print(f"\n✅ 分析完成!")
        print(f"📊 {args.symbol} 分析报告:")
        print(f"  时间范围: {df.index[0].date()} 到 {df.index[-1].date()}")
        print(f"  数据点数: {len(df)}")
        print(f"  最新价格: ${df['收盘'].iloc[-1]:.2f}")
        print(f"  价格范围: ${df['最低'].min():.2f} - ${df['最高'].max():.2f}")
        print(f"  总成交量: {df['成交量'].sum():,.0f}")
    else:
        print("❌ 数据为空")
    
    print("\n" + "=" * 50)

if __name__ == "__main__":
    main()
