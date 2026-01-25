#!/usr/bin/env python3
"""
快速测试 - 不依赖 Gemini API
测试 Telegram 推送和监控逻辑
"""

import os
import sys
from dotenv import load_dotenv

# 加载环境变量
load_dotenv()

def test_telegram():
    """测试 Telegram 推送"""
    print("="*60)
    print("🧪 测试 Telegram 消息推送")
    print("="*60)
    
    try:
        from src.notify.telegram import send_telegram_msg
        
        test_message = """
🎯 *股票监控系统测试*

这是一条测试消息，用于验证 Telegram 推送功能。

*股票*: 士兰微 (sh600460)
*规则*: RSI超卖预警
*当前值*: RSI = 28.5 < 30
*时间*: 测试中

✅ 如果您收到此消息，说明推送功能正常！
"""
        
        print("\n📤 正在发送测试消息到 Telegram...")
        success = send_telegram_msg(test_message)
        
        if success:
            print("✅ Telegram 消息发送成功！")
            print("📱 请检查您的 Telegram 应用")
            return True
        else:
            print("❌ 发送失败")
            return False
            
    except Exception as e:
        print(f"❌ 测试失败: {e}")
        import traceback
        traceback.print_exc()
        return False

def test_monitor_with_mock_data():
    """测试监控逻辑（使用真实数据）"""
    print("\n" + "="*60)
    print("🧪 测试监控执行逻辑（真实数据）")
    print("="*60)
    
    try:
        from github_stock_bot import fetch_kline_data, calculate_technical_indicators
        
        # 获取真实数据
        print("\n📊 获取士兰微实时数据...")
        df = fetch_kline_data("sh600460", scale=5, datalen=100)
        
        if df is None or df.empty:
            print("❌ 数据获取失败")
            return False
            
        df = calculate_technical_indicators(df)
        last = df.iloc[-1]
        
        print(f"✅ 数据获取成功")
        print(f"\n当前指标:")
        print(f"  收盘价: {last['Close']:.2f}")
        print(f"  RSI(14): {last['RSI']:.2f}")
        print(f"  MACD: {last['MACD']:.4f}")
        print(f"  MA20: {last['MA20']:.2f}")
        
        # 模拟规则检查
        print(f"\n📋 模拟规则检查:")
        
        rules = [
            {"name": "RSI超卖", "check": last['RSI'] < 30, "desc": f"RSI({last['RSI']:.2f}) < 30"},
            {"name": "RSI超买", "check": last['RSI'] > 70, "desc": f"RSI({last['RSI']:.2f}) > 70"},
            {"name": "突破MA20", "check": last['Close'] > last['MA20'], "desc": f"价格({last['Close']:.2f}) > MA20({last['MA20']:.2f})"},
            {"name": "MACD金叉", "check": last['MACD'] > 0, "desc": f"MACD({last['MACD']:.4f}) > 0"},
        ]
        
        triggered = []
        for rule in rules:
            status = "✅ 触发" if rule['check'] else "⏸️  未触发"
            print(f"  {status} - {rule['name']}: {rule['desc']}")
            if rule['check']:
                triggered.append(rule)
        
        if triggered:
            print(f"\n🔔 {len(triggered)} 条规则已触发:")
            for r in triggered:
                print(f"  - {r['name']}")
        else:
            print(f"\n✅ 当前无触发规则")
            
        return True
        
    except Exception as e:
        print(f"❌ 测试失败: {e}")
        import traceback
        traceback.print_exc()
        return False

def main():
    print("╔" + "="*58 + "╗")
    print("║  📊 股票监控系统 - 快速测试                             ║")
    print("╚" + "="*58 + "╝")
    
    # 检查环境变量
    print("\n🔍 环境变量检查:")
    telegram_token_ok = "✅" if os.getenv("TELEGRAM_BOT_TOKEN") else "❌"
    telegram_chat_ok = "✅" if os.getenv("TELEGRAM_CHAT_ID") else "❌"
    
    print(f"  {telegram_token_ok} TELEGRAM_BOT_TOKEN")
    print(f"  {telegram_chat_ok} TELEGRAM_CHAT_ID")
    
    if not all([os.getenv("TELEGRAM_BOT_TOKEN"), os.getenv("TELEGRAM_CHAT_ID")]):
        print("\n⚠️  Telegram 配置不完整")
        return
    
    # 运行测试
    results = []
    results.append(("Telegram 推送", test_telegram()))
    results.append(("监控逻辑（真实数据）", test_monitor_with_mock_data()))
    
    # 总结
    print("\n" + "="*60)
    print("📋 测试总结")
    print("="*60)
    
    for name, result in results:
        status = "✅ 通过" if result else "❌ 失败"
        print(f"  {status}  {name}")
    
    passed = sum(1 for _, r in results if r)
    total = len(results)
    
    print(f"\n总计: {passed}/{total} 项测试通过")
    
    if passed == total:
        print("\n🎉 所有测试通过！")
        print("\n💡 下一步:")
        print("   1. 在终端手动安装: pip3 install google-generativeai")
        print("   2. 运行完整测试: python3 test_monitor_system.py")
        print("   3. 使用策略解析: python3 update_strategy.py")

if __name__ == "__main__":
    main()
