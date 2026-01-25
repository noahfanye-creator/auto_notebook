"""
数据工具函数模块
处理时间格式、交易时段等
"""

import pandas as pd
from typing import Optional


def normalize_beijing_time(df: Optional[pd.DataFrame]) -> Optional[pd.DataFrame]:
    """将时间索引规范为北京时间（无时区）"""
    if df is None or df.empty:
        return df

    if not isinstance(df.index, pd.DatetimeIndex):
        return df

    if df.index.tz is None:
        return df

    try:
        df = df.copy()
        df.index = df.index.tz_convert("Asia/Shanghai").tz_localize(None)
        return df
    except Exception:
        return df


def filter_trading_hours(df: Optional[pd.DataFrame]) -> Optional[pd.DataFrame]:
    """仅保留A股交易时段数据"""
    if df is None or df.empty:
        return df

    try:
        df = normalize_beijing_time(df)
        if not isinstance(df.index, pd.DatetimeIndex):
            return df

        morning = df.between_time("09:30", "11:30")
        afternoon = df.between_time("13:00", "15:00")
        filtered = pd.concat([morning, afternoon]).sort_index()
        return filtered
    except Exception:
        return df


def is_intraday_data(df: Optional[pd.DataFrame]) -> bool:
    """判断是否为日内数据（含时间）"""
    if df is None or df.empty or not isinstance(df.index, pd.DatetimeIndex):
        return False
    return any((df.index.hour != 0) | (df.index.minute != 0))


def format_beijing_time(dt) -> str:
    """格式化北京时间"""
    if dt is None:
        return "未知"
    if getattr(dt, "tzinfo", None) is not None:
        try:
            dt = dt.tz_convert("Asia/Shanghai").tz_localize(None)
        except Exception:
            pass
    return dt.strftime("%Y-%m-%d %H:%M:%S")
