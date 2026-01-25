# 技术指标计算模块
from .indicators import (
    calculate_technical_indicators,
    resample_kline_data,
    calculate_ma,
    calculate_rsi,
    calculate_macd,
    calculate_kdj,
    calculate_bollinger,
    calculate_volume_indicators,
    calculate_all_indicators,
)

# 市场分析模块
from .market_analyzer import get_market_summary_analysis, get_market_sentiment_analysis

# 缠论模块（如果存在）
try:
    from .chan_kline import process_include  # noqa: F401
    from .chan_fractal import find_fractals  # noqa: F401
    from .chan_bi import find_bi  # noqa: F401
    from .chan_xd import find_xd  # noqa: F401
    from .chan_zhongshu import find_zhongshu  # noqa: F401
    from .chan_third_buy import detect_third_buy, run_chan_pipeline  # noqa: F401

    __all__ = [
        # 技术指标
        "calculate_technical_indicators",
        "resample_kline_data",
        "calculate_ma",
        "calculate_rsi",
        "calculate_macd",
        "calculate_kdj",
        "calculate_bollinger",
        "calculate_volume_indicators",
        "calculate_all_indicators",
        # 市场分析
        "get_market_summary_analysis",
        "get_market_sentiment_analysis",
        # 缠论
        "process_include",
        "find_fractals",
        "find_bi",
        "find_xd",
        "find_zhongshu",
        "detect_third_buy",
        "run_chan_pipeline",
    ]
except ImportError:
    # 缠论模块不存在时，只导出技术指标和市场分析
    __all__ = [
        # 技术指标
        "calculate_technical_indicators",
        "resample_kline_data",
        "calculate_ma",
        "calculate_rsi",
        "calculate_macd",
        "calculate_kdj",
        "calculate_bollinger",
        "calculate_volume_indicators",
        "calculate_all_indicators",
        # 市场分析
        "get_market_summary_analysis",
        "get_market_sentiment_analysis",
    ]
