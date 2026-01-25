#!/usr/bin/env python3
"""
技术分析模块
"""
import pandas as pd
import numpy as np
from typing import Dict, List, Any


class TechnicalAnalyzer:
    """技术分析器"""

    def __init__(self, df: pd.DataFrame):
        """
        初始化分析器

        Args:
            df: 包含 OHLCV 数据的 DataFrame
        """
        self.df = df.copy()
        self.signals = {}

    def calculate_rsi(self, period: int = 14) -> pd.Series:
        """计算相对强弱指数 (RSI)"""
        delta = self.df["收盘"].diff()
        gain = (delta.where(delta > 0, 0)).rolling(window=period).mean()
        loss = (-delta.where(delta < 0, 0)).rolling(window=period).mean()

        rs = gain / loss
        rsi = 100 - (100 / (1 + rs))

        self.signals["rsi"] = rsi
        return rsi

    def calculate_sma(self, period: int = 20) -> pd.Series:
        """计算简单移动平均线"""
        sma = self.df["收盘"].rolling(window=period).mean()
        self.signals[f"sma_{period}"] = sma
        return sma

    def calculate_ema(self, period: int = 12) -> pd.Series:
        """计算指数移动平均线"""
        ema = self.df["收盘"].ewm(span=period, adjust=False).mean()
        self.signals[f"ema_{period}"] = ema
        return ema

    def calculate_macd(self) -> Dict[str, pd.Series]:
        """计算 MACD 指标"""
        ema_12 = self.calculate_ema(12)
        ema_26 = self.calculate_ema(26)

        macd_line = ema_12 - ema_26
        signal_line = macd_line.ewm(span=9, adjust=False).mean()
        histogram = macd_line - signal_line

        result = {"macd": macd_line, "signal": signal_line, "histogram": histogram}

        self.signals["macd"] = result
        return result

    def calculate_bollinger_bands(self, period: int = 20, std_dev: int = 2) -> Dict[str, pd.Series]:
        """计算布林带"""
        sma = self.calculate_sma(period)
        std = self.df["收盘"].rolling(window=period).std()

        upper_band = sma + (std * std_dev)
        lower_band = sma - (std * std_dev)

        result = {"upper": upper_band, "middle": sma, "lower": lower_band}

        self.signals["bollinger"] = result
        return result

    def generate_signals(self) -> Dict[str, str]:
        """生成交易信号"""
        signals = {}

        # RSI 信号
        if "rsi" in self.signals:
            rsi = self.signals["rsi"]
            if len(rsi) > 0:
                latest_rsi = rsi.iloc[-1]
                if latest_rsi > 70:
                    signals["rsi"] = "SELL (超买)"
                elif latest_rsi < 30:
                    signals["rsi"] = "BUY (超卖)"
                else:
                    signals["rsi"] = "HOLD"

        # MACD 信号
        if "macd" in self.signals:
            macd_data = self.signals["macd"]
            if len(macd_data["macd"]) > 1:
                macd = macd_data["macd"].iloc[-1]
                signal = macd_data["signal"].iloc[-1]
                prev_macd = macd_data["macd"].iloc[-2]
                prev_signal = macd_data["signal"].iloc[-2]

                # 金叉
                if prev_macd < prev_signal and macd > signal:
                    signals["macd"] = "BUY (金叉)"
                # 死叉
                elif prev_macd > prev_signal and macd < signal:
                    signals["macd"] = "SELL (死叉)"
                else:
                    signals["macd"] = "HOLD"

        # 布林带信号
        if "bollinger" in self.signals:
            bb = self.signals["bollinger"]
            latest_price = self.df["收盘"].iloc[-1]

            if latest_price > bb["upper"].iloc[-1]:
                signals["bollinger"] = "SELL (上轨突破)"
            elif latest_price < bb["lower"].iloc[-1]:
                signals["bollinger"] = "BUY (下轨突破)"
            else:
                signals["bollinger"] = "HOLD (轨道内)"

        return signals

    def get_summary(self) -> Dict[str, Any]:
        """获取分析摘要"""
        if "rsi" not in self.signals:
            self.calculate_rsi()

        if "macd" not in self.signals:
            self.calculate_macd()

        if "bollinger" not in self.signals:
            self.calculate_bollinger_bands()

        signals = self.generate_signals()

        summary = {
            "数据天数": len(self.df),
            "当前价格": self.df["收盘"].iloc[-1],
            "价格变化%": ((self.df["收盘"].iloc[-1] - self.df["收盘"].iloc[0]) / self.df["收盘"].iloc[0] * 100),
            "RSI(14)": self.signals["rsi"].iloc[-1] if len(self.signals["rsi"]) > 0 else None,
            "交易信号": signals,
        }

        return summary
