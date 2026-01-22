#!/usr/bin/env python3
"""
测试技术分析模块
"""
import sys
sys.path.append('.')

from src.data.reliable_fetcher import get_stock_data
from src.analysis.technical import TechnicalAnalyzer

def main():
    print("📈 技术分析测试")
    print("=" * 50)
    
    # 获取数据（使用模拟模式确保成功）
    symbol = "AAPL"
    print(f"获取 {symbol} 数据...")
    df = get_stock_data(symbol, "1mo", mode='mock')
    
    if df.empty:
        print("❌ 数据获取失败")
        return
    
    print(f"✅ 获取到 {len(df)} 条数据")
    
    # 技术分析
    print(f"\n🔧 进行技术分析...")
    analyzer = TechnicalAnalyzer(df)
    
    # 计算指标
    rsi = analyzer.calculate_rsi()
    macd = analyzer.calculate_macd()
    bb = analyzer.calculate_bollinger_bands()
    
    # 生成信号
    signals = analyzer.generate_signals()
    summary = analyzer.get_summary()
    
    # 显示结果
    print(f"\n📊 技术分析结果 ({symbol}):")
    print("-" * 40)
    
    for key, value in summary.items():
        if key == '交易信号':
            print(f"{key}:")
            for signal_key, signal_value in value.items():
                print(f"  {signal_key}: {signal_value}")
        elif isinstance(value, float):
            print(f"{key}: {value:.2f}")
        else:
            print(f"{key}: {value}")
    
    print("\n" + "=" * 50)
    print("✅ 技术分析测试完成!")

if __name__ == "__main__":
    main()
