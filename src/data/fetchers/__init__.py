"""
数据获取模块
统一导出所有数据获取函数
"""

from .a_share_fetcher import get_name, fetch_kline_data_from_sina, fetch_kline_data_fallback, fetch_kline_data
from .hk_stock_fetcher import fetch_kline_data_from_hk_sources, fetch_alternative_1min_data
from .sector_fetcher import load_sector_index_map, get_sector_index_name, get_sector_indices_data
from .market_indices_fetcher import get_market_indices_data
from .data_utils import (
    normalize_beijing_time,
    filter_trading_hours,
    is_intraday_data,
    format_beijing_time,
    trim_to_as_of,
    is_last_bar_incomplete,
    fill_last_bar,
)

__all__ = [
    # A股数据获取
    "get_name",
    "fetch_kline_data_from_sina",
    "fetch_kline_data_fallback",
    "fetch_kline_data",
    # 港股数据获取
    "fetch_kline_data_from_hk_sources",
    "fetch_alternative_1min_data",
    # 行业数据获取
    "load_sector_index_map",
    "get_sector_index_name",
    "get_sector_indices_data",
    # 市场指数数据
    "get_market_indices_data",
    # 数据工具函数
    "normalize_beijing_time",
    "filter_trading_hours",
    "is_intraday_data",
    "format_beijing_time",
    "trim_to_as_of",
    "is_last_bar_incomplete",
    "fill_last_bar",
]
