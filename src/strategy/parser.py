import os
import json
import yaml
import google.generativeai as genai
from loguru import logger
from typing import List, Dict, Any

class StrategyParser:
    """
    使用 Gemini API 解析策略文本并提取结构化监控指标
    """
    
    def __init__(self, api_key: str = None):
        self.api_key = api_key or os.getenv("GEMINI_API_KEY")
        if not self.api_key:
            raise ValueError("GEMINI_API_KEY must be provided or set as an environment variable")
        
        genai.configure(api_key=self.api_key)
        self.model = genai.GenerativeModel('gemini-pro')
        
    def parse(self, text: str) -> List[Dict[str, Any]]:
        """
        解析策略文本
        
        Args:
            text: 粘贴的策略文本
            
        Returns:
            List[Dict]: 解析出的规则列表
        """
        prompt = f"""
你是一个专业的量化股票策略分析师。请从以下策略分析文本中提取重要的监控指标规则。

规则定义如下：
1. 股票代码(code): 必须是标准格式，如 sh600460, sz300474, HK.00700。如果是纯数字，请根据常识补全前缀。
2. 指标(indicator): 技术指标名称，如 Close (现价), RSI, MACD, MA20, MA60, K, D, J, Volume, Volume_Ratio 等。
3. 条件(condition): 比较操作符，只能是 ">", "<", ">=", "<=", "==" 之一。
4. 阈值(threshold): 比较的数值，或者是另一个指标名称（如 "MA20"）。
5. 规则名称(name): 简短的描述，如 "RSI超卖", "突破MA20"。

请严格返回一个 JSON 数组，每个元素包含 fields: code, indicator, condition, threshold, name。
不要输出任何其他解释性文字，只输出 JSON。

策略文本内容：
---
{text}
---
"""
        try:
            response = self.model.generate_content(prompt)
            # 清理可能的 Markdown 格式标记
            clean_text = response.text.replace('```json', '').replace('```', '').strip()
            rules = json.loads(clean_text)
            
            if not isinstance(rules, list):
                rules = [rules]
                
            logger.info(f"✅ 成功从策略文本中解析出 {len(rules)} 条规则")
            return rules
            
        except Exception as e:
            logger.error(f"❌ 解析策略文本出错: {e}")
            return []

    def save_rules(self, rules: List[Dict[str, Any]], config_path: str = "config/monitor_rules.yaml"):
        """
        将解析出的规则保存到 YAML 配置文件中
        """
        # 确保目录存在
        os.makedirs(os.path.dirname(config_path), exist_ok=True)
        
        # 如果文件已存在，加载现有规则并合并（按 code + indicator + condition 唯一性去重）
        existing_rules = []
        if os.path.exists(config_path):
            with open(config_path, 'r', encoding='utf-8') as f:
                try:
                    existing_rules = yaml.safe_load(f) or []
                except:
                    existing_rules = []
        
        # 合并逻辑：简单追加，去重
        merged_map = {f"{r['code']}_{r['indicator']}_{r['condition']}_{r['threshold']}": r for r in existing_rules}
        for r in rules:
            key = f"{r['code']}_{r['indicator']}_{r['condition']}_{r['threshold']}"
            merged_map[key] = r
            
        final_rules = list(merged_map.values())
        
        with open(config_path, 'w', encoding='utf-8') as f:
            yaml.dump(final_rules, f, allow_unicode=True, sort_keys=False)
            
        logger.info(f"✅ 已同步监控规则到 {config_path}，当前共有 {len(final_rules)} 条规则")
        return final_rules
