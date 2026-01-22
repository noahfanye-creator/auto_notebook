#!/usr/bin/env python3
"""
增强版股票分析机器人
"""
import argparse
import sys
from pathlib import Path

def main():
    parser = argparse.ArgumentParser(
        description='增强版股票分析机器人',
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
示例:
  %(prog)s AAPL                   # 分析AAPL股票
  %(prog)s MSFT --period 1mo      # 分析1个月数据
  %(prog)s TSLA --technical       # 进行技术分析
  %(prog)s AAPL --plot            # 生成图表
  %(prog)s --watchlist            # 分析监控列表
  %(prog)s --mode mock            # 使用模拟数据
        """
    )
    
    parser.add_argument('symbol', nargs='?', help='股票代码')
    parser.add_argument('--period', default='1mo', help='数据周期')
    parser.add_argument('--mode', choices=['auto', 'mock', 'real'], 
                       default='auto', help='数据模式')
    parser.add_argument('--technical', action='store_true', help='进行技术分析')
    parser.add_argument('--plot', action='store_true', help='生成图表')
    parser.add_argument('--watchlist', action='store_true', help='分析监控列表')
    
    args = parser.parse_args()
    
    print("=" * 60)
    print("🚀 增强版股票分析机器人")
    print("=" * 60)
    
    if args.symbol:
        analyze_single_stock(args)
    elif args.watchlist:
        analyze_watchlist(args)
    else:
        print("请指定股票代码或使用 --watchlist")
        print("示例: python main_advanced.py AAPL --technical")
    
    print("=" * 60)

def analyze_single_stock(args):
    """分析单个股票"""
    try:
        from src.data.reliable_fetcher import get_stock_data
        
        print(f"📊 分析股票: {args.symbol}")
        print(f"📅 数据周期: {args.period}")
        print(f"🔧 数据模式: {args.mode}")
        print("-" * 40)
        
        # 获取数据
        df = get_stock_data(args.symbol, args.period, args.mode)
        
        if df.empty:
            print("❌ 数据获取失败")
            return
        
        # 基础分析
        print(f"✅ 获取 {len(df)} 条数据")
        print(f"💰 当前价格: ${df['收盘'].iloc[-1]:.2f}")
        
        price_change = ((df['收盘'].iloc[-1] - df['收盘'].iloc[0]) / df['收盘'].iloc[0] * 100)
        print(f"📈 价格变化: {price_change:+.2f}%")
        
        # 技术分析
        if args.technical:
            try:
                from src.analysis.technical import TechnicalAnalyzer
                
                print("\n🔬 技术分析:")
                print("-" * 30)
                
                analyzer = TechnicalAnalyzer(df)
                summary = analyzer.get_summary()
                
                for key, value in summary.items():
                    if key == '交易信号':
                        print(f"{key}:")
                        for signal_key, signal_value in value.items():
                            print(f"  📢 {signal_key}: {signal_value}")
                    elif isinstance(value, float):
                        print(f"  📊 {key}: {value:.2f}")
                    else:
                        print(f"  📊 {key}: {value}")
                        
            except ImportError:
                print("⚠️  技术分析模块未找到，跳过技术分析")
        
        # 生成图表
        if args.plot:
            try:
                from src.visualization.charts import StockChart
                import matplotlib.pyplot as plt
                
                print("\n🎨 生成图表...")
                chart = StockChart()
                
                # 创建图表目录
                charts_dir = Path("charts")
                charts_dir.mkdir(exist_ok=True)
                
                # 保存图表
                chart_path = charts_dir / f"{args.symbol}_chart.png"
                chart.plot_price(df, args.symbol, save_path=str(chart_path))
                
                print(f"✅ 图表已保存: {chart_path}")
                
            except ImportError:
                print("⚠️  可视化模块未找到，跳过图表生成")
        
    except Exception as e:
        print(f"❌ 分析失败: {e}")

def analyze_watchlist(args):
    """分析监控列表"""
    print("📋 分析监控列表...")
    
    # 默认监控列表
    watchlist = ['AAPL', 'MSFT', 'GOOGL', 'TSLA', 'AMZN']
    
    try:
        from src.data.reliable_fetcher import get_stock_data
        
        results = []
        for symbol in watchlist:
            print(f"\n🔍 {symbol}:")
            
            df = get_stock_data(symbol, args.period, args.mode)
            if not df.empty:
                price = df['收盘'].iloc[-1]
                change = ((df['收盘'].iloc[-1] - df['收盘'].iloc[0]) / df['收盘'].iloc[0] * 100)
                results.append((symbol, price, change, len(df)))
        
        # 显示总结
        print("\n" + "=" * 40)
        print("📈 监控列表总结:")
        print("=" * 40)
        
        for symbol, price, change, count in results:
            trend = "📈" if change > 0 else "📉"
            print(f"{trend} {symbol:10} ${price:8.2f} ({change:+.2f}%) - {count}天数据")
        
    except Exception as e:
        print(f"❌ 监控列表分析失败: {e}")

if __name__ == "__main__":
    main()
