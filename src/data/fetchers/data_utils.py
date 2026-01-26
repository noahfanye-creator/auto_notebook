"""
数据工具函数模块
处理时间格式、交易时段等
"""

import pandas as pd
from typing import Optional, Union


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
    """格式化北京时间；纯日期（00:00:00）仅输出 YYYY-MM-DD"""
    if dt is None:
        return "未知"
    if getattr(dt, "tzinfo", None) is not None:
        try:
            dt = dt.tz_convert("Asia/Shanghai").tz_localize(None)
        except Exception:
            pass
    ts = pd.Timestamp(dt)
    if getattr(ts, "hour", 0) == 0 and getattr(ts, "minute", 0) == 0:
        return ts.strftime("%Y-%m-%d")
    return ts.strftime("%Y-%m-%d %H:%M:%S")


def _period_end_for(bar_ts: pd.Timestamp, timeframe: str) -> pd.Timestamp:
    """单根 K 线对应周期的结束时间（日/周/月为当日 15:00，分钟线为 bar + 周期）。"""
    bar = pd.Timestamp(bar_ts)
    if timeframe in ("day", "week", "month"):
        return bar.normalize() + pd.Timedelta(hours=15, minutes=0)
    if timeframe == "30m":
        return bar + pd.Timedelta(minutes=30)
    if timeframe == "5m":
        return bar + pd.Timedelta(minutes=5)
    if timeframe == "1m":
        return bar + pd.Timedelta(minutes=1)
    return bar


def is_last_bar_incomplete(
    df: Optional[pd.DataFrame],
    as_of: Union[pd.Timestamp, str],
    timeframe: str,
) -> bool:
    """最后一根 K 线是否未走完（周期结束时间 > 数据获取时点）。"""
    if df is None or df.empty or not isinstance(df.index, pd.DatetimeIndex):
        return False
    as_ts = pd.Timestamp(as_of)
    if as_ts.tz is not None:
        try:
            as_ts = as_ts.tz_convert("Asia/Shanghai").tz_localize(None)
        except Exception:
            pass
    last = df.index[-1]
    end = _period_end_for(last, timeframe)
    return as_ts < end


def fill_last_bar(
    df: Optional[pd.DataFrame],
    latest_price: float,
) -> Optional[pd.DataFrame]:
    """用数据获取时点最新价补充最后一根 K 线的 Close/High/Low（原地修改）。"""
    if df is None or df.empty:
        return df
    last_idx = df.index[-1]
    row = df.loc[last_idx]
    close = float(latest_price)
    high = float(row.get("High", close))
    low = float(row.get("Low", close))
    df.at[last_idx, "Close"] = close
    df.at[last_idx, "High"] = max(high, close)
    df.at[last_idx, "Low"] = min(low, close)
    return df


def trim_to_as_of(
    df: Optional[pd.DataFrame],
    as_of: Union[pd.Timestamp, str],
) -> Optional[pd.DataFrame]:
    """按截止时点裁剪数据，仅保留 index <= as_of 的行情

    用于报告生成：日/周/月/分钟线范围、封面最新价与涨跌幅均以「报告生成/数据获取时点」为界，
    而非完整日线或未来时点。

    Args:
        df: 带 DatetimeIndex 的 DataFrame
        as_of: 截止时点（北京时间，建议 naive）

    Returns:
        裁剪后的 DataFrame，若为空则返回 None
    """
    if df is None or df.empty:
        return df
    if not isinstance(df.index, pd.DatetimeIndex):
        return df
    as_ts = pd.Timestamp(as_of)
    if as_ts.tz is not None:
        try:
            as_ts = as_ts.tz_convert("Asia/Shanghai").tz_localize(None)
        except Exception:
            pass
    subset = df[df.index <= as_ts]
    if subset.empty:
        return None
    return subset
