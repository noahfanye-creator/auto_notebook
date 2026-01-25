"""
工具函数模块
提供代码标准化、交易时间判断、字体设置、日志、缓存、并发处理、统一异常等功能
"""

from .logger import setup_logger, get_logger
from .cache import get_cache, DataCache
from .parallel import parallel_process, batch_process, parallel_map
from .exceptions import (
    StockAnalysisError,
    DataFetchError,
    IndicatorCalculationError,
    ReportGenerationError,
    ConfigError,
)

__all__ = [
    "setup_logger",
    "get_logger",
    "get_cache",
    "DataCache",
    "parallel_process",
    "batch_process",
    "parallel_map",
    "StockAnalysisError",
    "DataFetchError",
    "IndicatorCalculationError",
    "ReportGenerationError",
    "ConfigError",
]
