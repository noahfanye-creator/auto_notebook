"""
技术指标计算模块
提供各种技术指标的计算函数
"""

from typing import Optional

import numpy as np
import pandas as pd

from src.utils.logger import get_logger
from src.utils.exceptions import IndicatorCalculationError

logger = get_logger(__name__)


def calculate_technical_indicators(df: Optional[pd.DataFrame]) -> Optional[pd.DataFrame]:
    """计算技术指标（增强版）

    Args:
        df: 包含 OHLCV 数据的 DataFrame

    Returns:
        添加了技术指标的 DataFrame
    """
    if df is None or df.empty:
        return df

    df = df.copy()

    # 移动平均线
    window_5 = min(5, len(df))
    window_10 = min(10, len(df))
    window_20 = min(20, len(df))
    window_60 = min(60, len(df))

    if "Close" in df.columns:
        df["MA5"] = df["Close"].rolling(window=window_5, min_periods=1).mean()
        df["MA10"] = df["Close"].rolling(window=window_10, min_periods=1).mean()
        df["MA20"] = df["Close"].rolling(window=window_20, min_periods=1).mean()
        df["MA60"] = df["Close"].rolling(window=window_60, min_periods=1).mean()
        df["MA250"] = df["Close"].rolling(window=min(250, len(df)), min_periods=1).mean()

    # MACD
    if "Close" in df.columns and len(df) >= 26:
        exp12 = df["Close"].ewm(span=12, adjust=False).mean()
        exp26 = df["Close"].ewm(span=26, adjust=False).mean()
        df["DIF"] = exp12 - exp26
        df["DEA"] = df["DIF"].ewm(span=9, adjust=False).mean()
        df["MACD"] = 2 * (df["DIF"] - df["DEA"])

    # RSI
    if "Close" in df.columns and len(df) >= 14:
        delta = df["Close"].diff()
        gain = (delta.where(delta > 0, 0)).rolling(window=min(14, len(df))).mean()
        loss = (-delta.where(delta < 0, 0)).rolling(window=min(14, len(df))).mean()
        rs = gain / loss
        df["RSI"] = 100 - (100 / (1 + rs))
        df["RSI"] = df["RSI"].fillna(50)

    # 布林带
    if "Close" in df.columns and len(df) >= 20:
        df["BB_Middle"] = df["Close"].rolling(window=min(20, len(df))).mean()
        df["BB_Std"] = df["Close"].rolling(window=min(20, len(df))).std()
        df["BB_Upper"] = df["BB_Middle"] + (df["BB_Std"] * 2)
        df["BB_Lower"] = df["BB_Middle"] - (df["BB_Std"] * 2)

    # 成交量均线
    if "Volume" in df.columns:
        df["Volume_MA5"] = df["Volume"].rolling(window=min(5, len(df)), min_periods=1).mean()
        df["Volume_MA10"] = df["Volume"].rolling(window=min(10, len(df)), min_periods=1).mean()

        # 量比
        df["Volume_Ratio"] = df["Volume"] / df["Volume_MA5"]
        df["Volume_Ratio"] = df["Volume_Ratio"].replace([np.inf, -np.inf], 1).fillna(1)

    # KDJ指标
    if "High" in df.columns and "Low" in df.columns and "Close" in df.columns and len(df) >= 9:
        window_9 = min(9, len(df))
        low_list = df["Low"].rolling(window=window_9, min_periods=1).min()
        high_list = df["High"].rolling(window=window_9, min_periods=1).max()
        rsv = ((df["Close"] - low_list) / (high_list - low_list) * 100).fillna(50)
        df["K"] = rsv.ewm(com=2, adjust=False).mean()
        df["D"] = df["K"].ewm(com=2, adjust=False).mean()
        df["J"] = 3 * df["K"] - 2 * df["D"]

    # 威廉指标
    if "High" in df.columns and "Low" in df.columns and "Close" in df.columns and len(df) >= 14:
        high_14 = df["High"].rolling(window=min(14, len(df)), min_periods=1).max()
        low_14 = df["Low"].rolling(window=min(14, len(df)), min_periods=1).min()
        df["WR"] = ((high_14 - df["Close"]) / (high_14 - low_14) * 100).fillna(50)

    # OBV
    if "Close" in df.columns and "Volume" in df.columns:
        df["OBV"] = 0.0
        obv_values = []
        obv = 0
        prev_close = None

        for idx, row in df.iterrows():
            if prev_close is not None:
                if row["Close"] > prev_close:
                    obv += row["Volume"]
                elif row["Close"] < prev_close:
                    obv -= row["Volume"]
            obv_values.append(obv)
            prev_close = row["Close"]

        df["OBV"] = obv_values

    # 振幅
    if "High" in df.columns and "Low" in df.columns and "Close" in df.columns:
        df["Amplitude"] = ((df["High"] - df["Low"]) / df["Close"].shift(1).replace(0, 1)) * 100
        df["Amplitude"] = df["Amplitude"].fillna(0)

    return df


def resample_kline_data(df: Optional[pd.DataFrame], period: str = "W") -> Optional[pd.DataFrame]:
    """重采样K线数据

    Args:
        df: K线数据 DataFrame
        period: 重采样周期，'W'=周线，'M'=月线，或其他pandas周期

    Returns:
        重采样后的 DataFrame
    """
    if df is None or df.empty:
        return None

    try:
        logic = {"Open": "first", "High": "max", "Low": "min", "Close": "last", "Volume": "sum"}

        if period == "W":
            df_resampled = df.resample("W-FRI").apply(logic)
        elif period == "M":
            df_resampled = df.resample("ME").apply(logic)  # 'M'已弃用，使用'ME'
        else:
            df_resampled = df.resample(period).apply(logic)

        df_resampled = df_resampled.dropna()

        if len(df_resampled) < 3:
            return None

        df_resampled = calculate_technical_indicators(df_resampled)

        return df_resampled

    except IndicatorCalculationError:
        raise
    except Exception as e:
        raise IndicatorCalculationError(f"重采样失败: {e}") from e


# 保留原有的独立函数，以便向后兼容
def calculate_ma(df: pd.DataFrame, windows: list = [5, 10, 20, 60]) -> pd.DataFrame:
    """计算移动平均线"""
    df = df.copy()
    for window in windows:
        if len(df) >= window:
            df[f"MA{window}"] = df["Close"].rolling(window=window, min_periods=1).mean()
    return df


def calculate_rsi(df: pd.DataFrame, period: int = 14) -> pd.DataFrame:
    """计算 RSI 指标"""
    df = df.copy()
    if len(df) < period:
        return df

    delta = df["Close"].diff()
    gain = (delta.where(delta > 0, 0)).rolling(window=period).mean()
    loss = (-delta.where(delta < 0, 0)).rolling(window=period).mean()

    rs = gain / loss
    df["RSI"] = 100 - (100 / (1 + rs))
    df["RSI"] = df["RSI"].fillna(50)

    return df


def calculate_macd(df: pd.DataFrame, fast: int = 12, slow: int = 26, signal: int = 9) -> pd.DataFrame:
    """计算 MACD 指标"""
    df = df.copy()
    if len(df) < slow:
        return df

    exp_fast = df["Close"].ewm(span=fast, adjust=False).mean()
    exp_slow = df["Close"].ewm(span=slow, adjust=False).mean()

    df["DIF"] = exp_fast - exp_slow
    df["DEA"] = df["DIF"].ewm(span=signal, adjust=False).mean()
    df["MACD"] = 2 * (df["DIF"] - df["DEA"])

    return df


def calculate_kdj(df: pd.DataFrame, period: int = 9) -> pd.DataFrame:
    """计算 KDJ 指标"""
    df = df.copy()
    if len(df) < period:
        return df

    low_min = df["Low"].rolling(window=period, min_periods=1).min()
    high_max = df["High"].rolling(window=period, min_periods=1).max()

    rsv = ((df["Close"] - low_min) / (high_max - low_min) * 100).fillna(50)

    df["K"] = rsv.ewm(com=2, adjust=False).mean()
    df["D"] = df["K"].ewm(com=2, adjust=False).mean()
    df["J"] = 3 * df["K"] - 2 * df["D"]

    return df


def calculate_bollinger(df: pd.DataFrame, period: int = 20, std_multiplier: float = 2.0) -> pd.DataFrame:
    """计算布林带"""
    df = df.copy()
    if len(df) < period:
        return df

    df["BB_Middle"] = df["Close"].rolling(window=period).mean()
    df["BB_Std"] = df["Close"].rolling(window=period).std()
    df["BB_Upper"] = df["BB_Middle"] + (df["BB_Std"] * std_multiplier)
    df["BB_Lower"] = df["BB_Middle"] - (df["BB_Std"] * std_multiplier)

    return df


def calculate_volume_indicators(df: pd.DataFrame) -> pd.DataFrame:
    """计算成交量相关指标"""
    df = df.copy()

    if "Volume" not in df.columns:
        return df

    # 成交量均线
    df["Volume_MA5"] = df["Volume"].rolling(window=min(5, len(df)), min_periods=1).mean()
    df["Volume_MA10"] = df["Volume"].rolling(window=min(10, len(df)), min_periods=1).mean()

    # 量比
    df["Volume_Ratio"] = df["Volume"] / df["Volume_MA5"]
    df["Volume_Ratio"] = df["Volume_Ratio"].replace([np.inf, -np.inf], 1).fillna(1)

    return df


def calculate_all_indicators(df: pd.DataFrame) -> pd.DataFrame:
    """
    计算所有技术指标（兼容函数）

    Args:
        df: DataFrame with OHLCV data

    Returns:
        DataFrame with all technical indicators
    """
    return calculate_technical_indicators(df)
