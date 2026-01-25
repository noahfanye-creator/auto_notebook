"""
市场分析模块
提供市场综合分析和情绪分析功能
"""

from typing import Dict, Any


def get_market_summary_analysis(indices_data: Dict[str, Any], market_label: str = "A股") -> str:
    """生成市场综合分析

    Args:
        indices_data: 市场指数数据字典，格式为 {code: {'name': name, 'data': df, 'type': 'A' or 'HK'}}
        market_label: 市场标签，如 "A股"、"港股"

    Returns:
        市场综合分析文本
    """
    if not indices_data:
        return "【市场指数数据获取失败】\n\n"

    analysis = f"【{market_label}市场综合分析】\n\n"

    for code, info in indices_data.items():
        df = info["data"]
        name = info["name"]

        if df is not None and not df.empty and len(df) >= 20:
            last = df.iloc[-1]

            trend = "横盘"
            if "MA5" in last and "MA10" in last and "MA20" in last:
                if last["MA5"] > last["MA10"] > last["MA20"]:
                    trend = "多头排列"
                elif last["MA5"] < last["MA10"] < last["MA20"]:
                    trend = "空头排列"

            rsi_status = "中性"
            if "RSI" in last:
                if last["RSI"] > 70:
                    rsi_status = "超买"
                elif last["RSI"] < 30:
                    rsi_status = "超卖"

            analysis += f"{name}:\n"
            analysis += f"  现价: {last['Close']:.2f}"

            if "MA5" in last:
                analysis += f", MA5: {last['MA5']:.2f}"
            if "MA10" in last:
                analysis += f", MA10: {last['MA10']:.2f}"

            analysis += f"\n  趋势: {trend}"

            if "RSI" in last:
                analysis += f", RSI: {last['RSI']:.1f}({rsi_status})"

            if "MACD" in last:
                analysis += f"\n  MACD: {last['MACD']:.3f}"

            if "K" in last and "D" in last and "J" in last:
                analysis += f", KDJ: K={last['K']:.1f} D={last['D']:.1f} J={last['J']:.1f}"

            analysis += "\n\n"

    return analysis


def get_market_sentiment_analysis(indices_data: Dict[str, Any], market_label: str = "A股") -> str:
    """生成市场情绪分析

    Args:
        indices_data: 市场指数数据字典，格式为 {code: {'name': name, 'data': df, 'type': 'A' or 'HK'}}
        market_label: 市场标签，如 "A股"、"港股"

    Returns:
        市场情绪分析文本
    """
    if not indices_data:
        return ""

    analysis = f"【{market_label}市场情绪分析】\n\n"

    up_count = 0
    down_count = 0
    overbought_count = 0
    oversold_count = 0

    for code, info in indices_data.items():
        df = info["data"]
        if df is not None and len(df) >= 2:
            last = df.iloc[-1]
            prev = df.iloc[-2]

            if last["Close"] > prev["Close"]:
                up_count += 1
            else:
                down_count += 1

            if "RSI" in last:
                if last["RSI"] > 70:
                    overbought_count += 1
                elif last["RSI"] < 30:
                    oversold_count += 1

    total = up_count + down_count
    if total > 0:
        up_ratio = (up_count / total) * 100
        analysis += "市场宽度指标:\n"
        analysis += f"  上涨指数: {up_count}个 ({up_ratio:.1f}%)\n"
        analysis += f"  下跌指数: {down_count}个 ({100-up_ratio:.1f}%)\n\n"

    if overbought_count > 0 or oversold_count > 0:
        analysis += "情绪极值:\n"
        analysis += f"  超买状态: {overbought_count}个指数\n"
        analysis += f"  超卖状态: {oversold_count}个指数\n\n"

    volatility_data = []
    for code, info in indices_data.items():
        df = info["data"]
        if df is not None and len(df) >= 5 and "Amplitude" in df.columns:
            last_5 = df.tail(5)
            volatility = last_5["Amplitude"].mean()
            volatility_data.append((info["name"], volatility))

    if volatility_data:
        volatility_data.sort(key=lambda x: x[1], reverse=True)
        analysis += "波动性排名 (5日平均振幅):\n"
        for name, vol in volatility_data[:3]:
            analysis += f"  {name}: {vol:.2f}%\n"

    return analysis
