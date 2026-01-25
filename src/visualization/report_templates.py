"""
PDF报告模板和辅助函数
提供报告生成所需的模板和格式化函数
"""
from typing import Dict, Any, Optional, List
import pandas as pd
from src.data.fetchers import format_beijing_time


def _format_range(df: Optional[pd.DataFrame]) -> str:
    """格式化数据区间
    
    Args:
        df: DataFrame with datetime index
    
    Returns:
        str: 格式化的日期范围字符串
    """
    if df is None or df.empty:
        return "无数据"
    
    start = df.index.min()
    end = df.index.max()
    if pd.isna(start) or pd.isna(end):
        return "无数据"
    
    needs_time = any([
        getattr(start, "hour", 0) != 0,
        getattr(start, "minute", 0) != 0,
        getattr(end, "hour", 0) != 0,
        getattr(end, "minute", 0) != 0
    ])
    fmt = "%Y-%m-%d %H:%M" if needs_time else "%Y-%m-%d"
    return f"{start.strftime(fmt)} ~ {end.strftime(fmt)} ({len(df)}条)"


def _get_trend_status(last: pd.Series) -> str:
    """根据均线判断趋势
    
    Args:
        last: 最后一行的数据 Series
    
    Returns:
        str: 趋势状态描述
    """
    if last is None:
        return "未知"
    if all(k in last for k in ['MA5', 'MA10', 'MA20']):
        if last['MA5'] > last['MA10'] > last['MA20']:
            return "多头排列"
        if last['MA5'] < last['MA10'] < last['MA20']:
            return "空头排列"
    return "震荡/中性"


def _build_report_summary(stock_name: str, stock_code: str, stock_data_map: Dict[str, Any], 
                          indices_data: Dict[str, Any]) -> List[str]:
    """生成结构化摘要文本
    
    Args:
        stock_name: 股票名称
        stock_code: 股票代码
        stock_data_map: 股票数据字典
        indices_data: 指数数据字典
    
    Returns:
        List[str]: 摘要文本行列表
    """
    summary_lines = []
    day_df = stock_data_map.get('day')
    
    if day_df is not None and not day_df.empty:
        last = day_df.iloc[-1]
        trend = _get_trend_status(last)
        rsi_status = "中性"
        if 'RSI' in last:
            rsi_status = "超买" if last['RSI'] > 70 else ("超卖" if last['RSI'] < 30 else "中性")
        macd_status = "多头" if last.get('MACD', 0) > 0 else "空头"
        
        summary_lines.append(
            f"{stock_name}({stock_code}) 日线收盘: {last['Close']:.2f}，趋势: {trend}，RSI: {rsi_status}，MACD: {macd_status}。"
        )
    else:
        summary_lines.append(f"{stock_name}({stock_code}) 日线数据不足，无法生成核心趋势摘要。")
    
    if indices_data:
        market_label = "港股" if stock_code.startswith("HK.") else "A股"
        sector_count = sum(1 for info in indices_data.values() if info.get('type') == 'SECTOR')
        market_count = len(indices_data) - sector_count
        if sector_count > 0:
            summary_lines.append(f"本次报告包含 {market_count} 个{market_label}主要指数和 {sector_count} 个行业板块指数的综合分析。")
        else:
            summary_lines.append(f"本次报告包含 {market_count} 个{market_label}主要指数的综合分析。")
    
    return summary_lines


def _build_parameters_table(meta: Dict[str, Any], stock_data_map: Dict[str, Any], 
                           indices_data: Dict[str, Any]) -> List[List[str]]:
    """生成参数与数据范围表格
    
    Args:
        meta: 元数据字典
        stock_data_map: 股票数据字典
        indices_data: 指数数据字典
    
    Returns:
        List[List[str]]: 表格数据（二维列表）
    """
    indicator_params = meta.get('indicator_params', {})
    indicator_text = (
        f"MA:{','.join(map(str, indicator_params.get('ma_windows', [])))}; "
        f"MACD:{'/'.join(map(str, indicator_params.get('macd', [])))}; "
        f"RSI:{indicator_params.get('rsi', '')}; "
        f"BB:{indicator_params.get('boll', '')}; "
        f"KDJ:{indicator_params.get('kdj', '')}; "
        f"WR:{indicator_params.get('wr', '')}; "
        f"VOL_MA:{','.join(map(str, indicator_params.get('volume_ma', [])))}"
    )
    
    table_data = [
        ['项目', '说明'],
        ['生成时间', meta.get('generated_at', '')],
        ['数据来源', meta.get('data_source', '未知')],
        ['指数来源', meta.get('index_source', '未知')],
        ['1分钟数据来源', meta.get('one_min_source', '未知')],
        ['日线范围', _format_range(stock_data_map.get('day'))],
        ['周线范围', _format_range(stock_data_map.get('week'))],
        ['月线范围', _format_range(stock_data_map.get('month'))],
        ['30分钟范围', _format_range(stock_data_map.get('30m'))],
        ['5分钟范围', _format_range(stock_data_map.get('5m'))],
        ['1分钟范围', _format_range(stock_data_map.get('1m'))],
        ['指标参数', indicator_text]
    ]
    
    if indices_data:
        index_ranges = [
            _format_range(info.get('data'))
            for info in indices_data.values()
            if info.get('data') is not None
        ]
        if index_ranges:
            table_data.insert(5, ['指数数据范围', f"{len(index_ranges)} 个指数，示例: {index_ranges[0]}"])
    
    return table_data
