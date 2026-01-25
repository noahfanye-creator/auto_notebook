#!/usr/bin/env python3
import sys
import os
from dotenv import load_dotenv
from src.strategy.parser import StrategyParser
from loguru import logger

# 加载环境变量
load_dotenv()

def main():
    print("==========================================")
    print("🚀 Stock Analysis Strategy Parser")
    print("==========================================")
    print("请输入或粘贴您的 NotebookLM 策略文本 (输入 'EOF' 结束):")
    
    lines = []
    while True:
        try:
            line = input()
            if line.strip().upper() == 'EOF':
                break
            lines.append(line)
        except EOFError:
            break
            
    strategy_text = "\n".join(lines).strip()
    
    if not strategy_text:
        print("❌ 未输入内容，退出。")
        return
        
    try:
        parser = StrategyParser()
        rules = parser.parse(strategy_text)
        
        if rules:
            print(f"\n✅ 解析出 {len(rules)} 条监控规则:")
            for i, r in enumerate(rules, 1):
                print(f"  {i}. [{r['code']}] {r['name']}: {r['indicator']} {r['condition']} {r['threshold']}")
            
            confirm = input("\n是否同步到监控配置文件? (y/n): ")
            if confirm.lower() == 'y':
                parser.save_rules(rules)
                print("\n✨ 配置同步完成！GitHub Actions 下次运行时将生效。")
            else:
                print("\n❌ 已取消同步。")
        else:
            print("\n⚠️ 未能解析出有效规则，请检查文本内容或 AI 配置。")
            
    except Exception as e:
        logger.error(f"发生错误: {e}")
        print(f"\n❌ 执行失败: {e}")

if __name__ == "__main__":
    main()
