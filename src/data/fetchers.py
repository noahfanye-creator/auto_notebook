"""
数据获取模块
提供股票数据、指数数据等获取功能
"""

import json
import os
from datetime import datetime
from typing import Any, Dict, Optional

import pandas as pd
import pytz
import requests

# 可选依赖：akshare
try:
    import akshare as ak
except Exception:
    ak = None

from src.analysis import calculate_technical_indicators


def get_name(symbol: str) -> str:
    """获取股票名称"""
    try:
        url = f"http://hq.sinajs.cn/list={symbol}"
        headers = {
            "User-Agent": "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36",
            "Referer": "https://finance.sina.com.cn",
        }
        resp = requests.get(url, headers=headers, timeout=10)
        if '="' in resp.text:
            name = resp.text.split('="')[1].split(",")[0]
            if name and name != symbol:
                return name
    except Exception as e:
        print(f"获取A股名称出错: {e}")

    return symbol


def fetch_kline_data(symbol: str, scale: int, datalen: int = 100) -> Optional[pd.DataFrame]:
    """获取K线数据"""
    try:
        url = f"http://money.finance.sina.com.cn/quotes_service/api/json_v2.php/CN_MarketData.getKLineData?symbol={symbol}&scale={scale}&ma=no&datalen={datalen}"
        headers = {"User-Agent": "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36"}
        resp = requests.get(url, headers=headers, timeout=20)

        if resp.status_code != 200:
            return None

        data = resp.json()
        if not data:
            return None

        df = pd.DataFrame(data)

        df.rename(
            columns={"day": "Date", "open": "Open", "high": "High", "low": "Low", "close": "Close", "volume": "Volume"},
            inplace=True,
        )

        cols = ["Open", "High", "Low", "Close", "Volume"]
        for col in cols:
            df[col] = pd.to_numeric(df[col], errors="coerce")

        df["Date"] = pd.to_datetime(df["Date"])
        df.set_index("Date", inplace=True)
        df.sort_index(inplace=True)

        return df

    except Exception as e:
        print(f"获取数据失败 {symbol} scale={scale}: {e}")
        return None


def get_market_indices_data(is_hk: bool = False) -> Dict[str, Any]:
    """获取市场指数数据

    Args:
        is_hk: 是否为港股市场

    Returns:
        Dict[str, Any]: 指数数据字典，key为指数代码，value为包含name和data的字典
    """
    indices_data = {}

    if is_hk:
        # 港股主要指数
        hk_indices = {"HSI": "恒生指数", "HSCEI": "恒生国企", "HSTECH": "恒生科技"}

        print("📊 获取港股指数数据...")
        for code, name in hk_indices.items():
            print(f"  获取 {name}...")
            # 港股指数数据获取需要特殊处理
            try:
                if ak:
                    df = ak.stock_hk_index_daily_sina(symbol=code)
                    if df is not None and not df.empty:
                        df = df.rename(
                            columns={
                                "date": "Date",
                                "open": "Open",
                                "close": "Close",
                                "high": "High",
                                "low": "Low",
                                "volume": "Volume",
                            }
                        )
                        df["Date"] = pd.to_datetime(df["Date"])
                        df.set_index("Date", inplace=True)
                        df = calculate_technical_indicators(df)
                        indices_data[code] = {"name": name, "data": df}
                else:
                    # 如果没有akshare，尝试其他方式
                    df = fetch_kline_data(f"HK.{code}", 240, 150)
                    if df is not None:
                        df = calculate_technical_indicators(df)
                        indices_data[code] = {"name": name, "data": df}
            except Exception as e:
                print(f"  获取 {name} 失败: {e}")
    else:
        # A股主要指数
        a_indices = {
            "sh000001": "上证指数",
            "sz399001": "深证成指",
            "sz399006": "创业板指",
            "sh000688": "科创50",
            "sh000300": "沪深300",
            "sh000905": "中证500",
            "sh000016": "上证50",
            "sz399005": "中小板指",
        }

        print("📊 获取A股指数数据...")
        for code, name in a_indices.items():
            print(f"  获取 {name}...")
            df = fetch_kline_data(code, 240, 150)
            if df is not None:
                df = calculate_technical_indicators(df)
                indices_data[code] = {"name": name, "data": df}

    return indices_data


def load_sector_index_map() -> Dict[str, Any]:
    """加载行业板块指数代码对照表

    Returns:
        Dict[str, Any]: 包含code_to_name和name_to_code的字典
    """
    current_dir = os.path.dirname(os.path.abspath(__file__))
    config_dir = os.path.join(current_dir, "..", "..", "config")
    map_file = os.path.join(config_dir, "sector_index_map.json")

    try:
        with open(map_file, "r", encoding="utf-8") as f:
            data = json.load(f)

        # 创建反向映射
        code_to_name = data.get("code_to_name", {})
        name_to_code = {v: k for k, v in code_to_name.items()}

        return {"code_to_name": code_to_name, "name_to_code": name_to_code}
    except Exception as e:
        print(f"加载行业指数对照表失败: {e}")
        return {"code_to_name": {}, "name_to_code": {}}


def get_sector_indices_data(sector_code: str, count: int = 150) -> Dict[str, Any]:
    """获取行业板块指数数据

    Args:
        sector_code: 行业代码（如BK1031）或行业名称（如光伏设备）
        count: 获取数据条数

    Returns:
        Dict[str, Any]: 行业指数数据字典
    """
    if ak is None:
        print("⚠️  akshare 未安装，无法获取行业指数数据")
        return {}

    sector_map = load_sector_index_map()
    code_to_name = sector_map.get("code_to_name", {})
    name_to_code = sector_map.get("name_to_code", {})

    # 判断输入是代码还是名称
    if sector_code in code_to_name:
        sector_name = code_to_name[sector_code]
    elif sector_code in name_to_code:
        sector_name = sector_code
        sector_code = name_to_code[sector_code]
    else:
        print(f"⚠️  未找到行业: {sector_code}")
        return {}

    indices_data = {}

    try:
        # 获取行业日线数据
        df_day = ak.stock_board_industry_hist_em(
            symbol=sector_name, period="daily", start_date="20230101", end_date="20261231", adjust=""
        )

        if df_day is not None and not df_day.empty:
            df_day = df_day.rename(
                columns={
                    "日期": "Date",
                    "开盘": "Open",
                    "收盘": "Close",
                    "最高": "High",
                    "最低": "Low",
                    "成交量": "Volume",
                }
            )
            df_day["Date"] = pd.to_datetime(df_day["Date"])
            df_day.set_index("Date", inplace=True)
            df_day = calculate_technical_indicators(df_day)

            indices_data[sector_code] = {"name": sector_name, "data": df_day}
    except Exception as e:
        print(f"获取行业指数数据失败 {sector_code}: {e}")

    return indices_data


def normalize_beijing_time(df: pd.DataFrame) -> pd.DataFrame:
    """将时间索引转换为北京时区

    Args:
        df: 包含Date索引的DataFrame

    Returns:
        pd.DataFrame: 转换后的DataFrame
    """
    if df is None or df.empty:
        return df

    try:
        beijing_tz = pytz.timezone("Asia/Shanghai")

        # 如果索引已经是时区感知的，转换为北京时区
        if df.index.tz is not None:
            df.index = df.index.tz_convert(beijing_tz)
        else:
            # 如果索引是naive的，假设是北京时区
            df.index = df.index.tz_localize(beijing_tz)

        return df
    except Exception as e:
        print(f"时区转换失败: {e}")
        return df


def filter_trading_hours(df: pd.DataFrame) -> pd.DataFrame:
    """过滤交易时间，只保留A股交易时间段的数据

    Args:
        df: 包含Date索引的DataFrame

    Returns:
        pd.DataFrame: 过滤后的DataFrame
    """
    if df is None or df.empty:
        return df

    try:
        # A股交易时间：9:30-11:30, 13:00-15:00
        def is_trading_time(ts):
            if isinstance(ts, pd.Timestamp):
                hour = ts.hour
                minute = ts.minute
                # 上午：9:30-11:30
                if (hour == 9 and minute >= 30) or (hour == 10) or (hour == 11 and minute <= 30):
                    return True
                # 下午：13:00-15:00
                if hour >= 13 and hour < 15:
                    return True
            return False

        # 对于日内数据，过滤交易时间
        if df.index.inferred_freq is None or "D" not in str(df.index.inferred_freq):
            # 可能是分钟级数据
            mask = df.index.map(is_trading_time)
            return df[mask]
        else:
            # 日线数据，不需要过滤
            return df
    except Exception as e:
        print(f"过滤交易时间失败: {e}")
        return df


def format_beijing_time(timestamp) -> str:
    """格式化时间为北京时区字符串

    Args:
        timestamp: 时间戳或时间对象

    Returns:
        str: 格式化后的时间字符串
    """
    try:
        beijing_tz = pytz.timezone("Asia/Shanghai")

        if isinstance(timestamp, pd.Timestamp):
            if timestamp.tz is None:
                timestamp = timestamp.tz_localize(beijing_tz)
            else:
                timestamp = timestamp.tz_convert(beijing_tz)
        else:
            timestamp = pd.to_datetime(timestamp).tz_localize(beijing_tz)

        return timestamp.strftime("%Y-%m-%d %H:%M:%S")
    except Exception as e:
        print(f"时间格式化失败: {e}")
        return str(timestamp)


def is_intraday_data(df: pd.DataFrame) -> bool:
    """判断是否为日内数据（分钟级数据）

    Args:
        df: 包含Date索引的DataFrame

    Returns:
        bool: True表示是日内数据，False表示是日线数据
    """
    if df is None or df.empty or len(df) < 2:
        return False

    try:
        # 计算时间间隔
        time_diff = (df.index[1] - df.index[0]).total_seconds()

        # 如果时间间隔小于1天（86400秒），认为是日内数据
        return time_diff < 86400
    except Exception:
        return False
