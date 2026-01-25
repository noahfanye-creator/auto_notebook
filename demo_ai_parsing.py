#!/usr/bin/env python3
"""
模拟 AI 策略解析测试（不需要真实调用 Gemini API）
演示策略解析的完整流程
"""

import yaml
import os

print("="*60)
print("🤖 AI 策略解析功能演示")
print("="*60)

# 示例策略文本
example_strategy = """
士兰微(600460)策略分析：
1. RSI 指标跌破 30 时关注超卖机会，可能反弹
2. 价格突破 MA20 均线时考虑买入信号
3. MACD 出现金叉(DIF上穿DEA)时趋势转多

腾讯控股(00700.HK)策略：
- K 值大于 80 时注意超买风险
- 成交量放大 1.5 倍以上需要关注
- 价格跌破 MA60 需要警惕趋势转弱
"""

print("\n📝 输入的策略文本:")
print("-"*60)
print(example_strategy)

# 模拟 Gemini 解析后的结果
parsed_rules = [
    {
        "code": "sh600460",
        "indicator": "RSI",
        "condition": "<",
        "threshold": 30,
        "name": "士兰微-RSI超卖预警"
    },
    {
        "code": "sh600460",
        "indicator": "Close",
        "condition": ">",
        "threshold": "MA20",
        "name": "士兰微-突破MA20"
    },
    {
        "code": "sh600460",
        "indicator": "DIF",
        "condition": ">",
        "threshold": "DEA",
        "name": "士兰微-MACD金叉"
    },
    {
        "code": "HK.00700",
        "indicator": "K",
        "condition": ">",
        "threshold": 80,
        "name": "腾讯控股-KDJ超买预警"
    },
    {
        "code": "HK.00700",
        "indicator": "Volume_Ratio",
        "condition": ">",
        "threshold": 1.5,
        "name": "腾讯控股-成交量异动"
    },
    {
        "code": "HK.00700",
        "indicator": "Close",
        "condition": "<",
        "threshold": "MA60",
        "name": "腾讯控股-跌破MA60预警"
    }
]

print("\n🎯 AI 解析结果:")
print("-"*60)
for i, rule in enumerate(parsed_rules, 1):
    print(f"\n规则 {i}: {rule['name']}")
    print(f"  股票代码: {rule['code']}")
    print(f"  监控指标: {rule['indicator']}")
    print(f"  触发条件: {rule['condition']}")
    print(f"  阈值: {rule['threshold']}")

# 保存为 YAML 配置
os.makedirs("config", exist_ok=True)
config_path = "config/monitor_rules.yaml"

print(f"\n💾 保存配置到: {config_path}")
print("-"*60)

with open(config_path, "w", encoding="utf-8") as f:
    yaml.dump(parsed_rules, f, allow_unicode=True, default_flow_style=False)

print("✅ 配置文件已保存")

# 显示生成的 YAML 文件内容
print("\n📄 生成的 YAML 配置:")
print("-"*60)
with open(config_path, "r", encoding="utf-8") as f:
    print(f.read())

# 验证配置可以正确加载
print("\n🔍 验证配置文件:")
print("-"*60)
with open(config_path, "r", encoding="utf-8") as f:
    loaded_rules = yaml.safe_load(f)
    print(f"✅ 成功加载 {len(loaded_rules)} 条监控规则")

print("\n" + "="*60)
print("📋 总结")
print("="*60)
print("\n✅ AI 策略解析流程演示完成！")
print("\n💡 实际使用时的流程:")
print("  1. 从 NotebookLM 复制策略文本")
print("  2. 运行: python3 update_strategy.py")
print("  3. 粘贴策略文本，按回车")
print("  4. Gemini AI 自动解析并生成 monitor_rules.yaml")
print("  5. 推送到 GitHub，自动监控生效")
print("\n🔑 Gemini API 安装:")
print("  如果 pip 遇到 SSL 错误，请在终端直接运行:")
print("  pip3 install google-generativeai --trusted-host pypi.org --trusted-host files.pythonhosted.org")
