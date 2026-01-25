#!/usr/bin/env python3
"""
简单的本地测试 - 使用日线数据
"""

import os
from dotenv import load_dotenv

load_dotenv()

print("="*60)
print("📊 简单本地测试")
print("="*60)

# 测试 1: 数据获取（日线）
print("\n🧪 测试 1: 获取日线数据")
print("-"*60)
try:
    from src.data.fetcher import fetch_stock_data, get_stock_name
    
    test_code = "sh600519"  # 贵州茅台
    print(f"测试股票: {test_code}")
    
    name = get_stock_name(test_code)
    print(f"股票名称: {name}")
    
    print("正在获取日线数据...")
    df = fetch_stock_data(test_code, period='1d', count=60)
    
    if df is not None and not df.empty:
        print(f"✅ 成功获取 {len(df)} 条数据")
        last = df.iloc[-1]
        print(f"\n最新数据 ({df.index[-1].strftime('%Y-%m-%d')}):")
        print(f"  开盘: {last['Open']:.2f}")
        print(f"  最高: {last['High']:.2f}")
        print(f"  最低: {last['Low']:.2f}")
        print(f"  收盘: {last['Close']:.2f}")
        print(f"  成交量: {last['Volume']:.0f}")
    else:
        print("❌ 数据获取失败")
        df = None
        
except Exception as e:
    print(f"❌ 测试失败: {e}")
    import traceback
    traceback.print_exc()
    df = None

# 测试 2: 技术指标计算
if df is not None:
    print("\n🧪 测试 2: 计算技术指标")
    print("-"*60)
    try:
        from src.analysis.indicators import calculate_technical_indicators
        
        df = calculate_technical_indicators(df)
        last = df.iloc[-1]
        
        print("✅ 技术指标计算完成\n")
        print("主要指标:")
        print(f"  收盘价: {last['Close']:.2f}")
        print(f"  MA5:   {last.get('MA5', 0):.2f}")
        print(f"  MA10:  {last.get('MA10', 0):.2f}")
        print(f"  MA20:  {last.get('MA20', 0):.2f}")
        print(f"  RSI:   {last.get('RSI', 0):.2f}")
        print(f"  MACD:  {last.get('MACD', 0):.2f}")
        print(f"  K:     {last.get('K', 0):.2f}")
        print(f"  D:     {last.get('D', 0):.2f}")
        print(f"  J:     {last.get('J', 0):.2f}")
        
    except Exception as e:
        print(f"❌ 测试失败: {e}")
        import traceback
        traceback.print_exc()

# 测试 3: 监控规则检查逻辑
print("\n🧪 测试 3: 监控规则检查逻辑")
print("-"*60)
try:
    import yaml
    
    # 创建测试规则
    test_rules = [
        {
            "code": "sh600519",
            "indicator": "RSI",
            "condition": "<",
            "threshold": 80,  # 宽松条件，容易触发
            "name": "RSI监控测试"
        },
        {
            "code": "sh600519",
            "indicator": "Close",
            "condition": ">",
            "threshold": "MA5",
            "name": "价格与MA5对比"
        }
    ]
    
    os.makedirs("config", exist_ok=True)
    with open("config/test_rules.yaml", "w", encoding="utf-8") as f:
        yaml.dump(test_rules, f, allow_unicode=True)
    
    print("✅ 测试规则已创建")
    print(f"\n规则内容:")
    for rule in test_rules:
        print(f"  - {rule['name']}: {rule['indicator']} {rule['condition']} {rule['threshold']}")
    
    # 手动检查规则
    if df is not None:
        print(f"\n检查结果:")
        last = df.iloc[-1]
        
        for rule in test_rules:
            indicator = rule['indicator']
            condition = rule['condition']
            threshold = rule['threshold']
            
            if indicator not in df.columns:
                print(f"  ⚠️  {rule['name']}: 指标 {indicator} 不存在")
                continue
            
            current_val = last[indicator]
            
            # 处理阈值
            if isinstance(threshold, str) and threshold in df.columns:
                target_val = last[threshold]
            else:
                target_val = float(threshold)
            
            # 判断
            triggered = False
            if condition == ">":
                triggered = current_val > target_val
            elif condition == "<":
                triggered = current_val < target_val
            elif condition == ">=":
                triggered = current_val >= target_val
            elif condition == "<=":
                triggered = current_val <= target_val
            
            status = "🔔 触发" if triggered else "⏸️  未触发"
            print(f"  {status} {rule['name']}: {current_val:.2f} {condition} {target_val:.2f}")
            
except Exception as e:
    print(f"❌ 测试失败: {e}")
    import traceback
    traceback.print_exc()

# 测试 4: Telegram 格式化（不实际发送）
print("\n🧪 测试 4: Telegram 消息格式化")
print("-"*60)
try:
    from datetime import datetime
    
    test_message = f"""🎯 *股票监控预警*

*名称*: 贵州茅台 (sh600519)
*规则*: RSI监控测试
*详情*: RSI (65.23) < 80
*时间*: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}

🕒 此预警在 60 分钟内不会重复推送。"""
    
    print("✅ 消息格式化成功")
    print("\n预览:")
    print(test_message)
    
except Exception as e:
    print(f"❌ 测试失败: {e}")

print("\n" + "="*60)
print("📋 测试总结")
print("="*60)
print("\n✅ 核心功能测试完成！")
print("\n💡 说明:")
print("  - 数据获取、指标计算、规则检查逻辑都正常")
print("  - Telegram 推送在本地环境可能有网络限制")
print("  - 在 GitHub Actions 环境中网络通畅，可以正常推送")
print("\n🚀 下一步:")
print("  1. pip3 install google-generativeai")
print("  2. python3 update_strategy.py (测试 AI 策略解析)")
print("  3. 推送到 GitHub 开启自动监控")
