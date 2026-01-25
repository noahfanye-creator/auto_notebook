"""
A股多数据源模块
实现多个免费数据源的自动降级机制
"""

import re
import json
import traceback
from typing import Optional
from datetime import datetime, timedelta

import pandas as pd
import requests


class AShareDataSources:
    """A股数据源管理器 - 自动降级"""

    @staticmethod
    def _normalize_symbol(symbol: str) -> tuple:
        """标准化股票代码
        返回: (clean_code, market_prefix)
        """
        clean_code = re.sub(r"[a-zA-Z]", "", symbol)
        if symbol.startswith("sh"):
            return clean_code, "sh"
        elif symbol.startswith("sz"):
            return clean_code, "sz"
        elif clean_code.startswith("6"):
            return clean_code, "sh"
        elif clean_code.startswith(("0", "3")):
            return clean_code, "sz"
        else:
            return clean_code, "sh"  # 默认

    @staticmethod
    def fetch_from_eastmoney(symbol: str, scale: int = 240, datalen: int = 100) -> Optional[pd.DataFrame]:
        """从东方财富获取K线数据

        Args:
            symbol: 股票代码
            scale: K线周期，240=日线，30=30分钟，5=5分钟
            datalen: 数据长度

        Returns:
            pd.DataFrame: K线数据
        """
        try:
            clean_code, market = AShareDataSources._normalize_symbol(symbol)
            if not clean_code:
                return None

            # 东方财富secid格式：1.600460 (上海) 或 0.000001 (深圳)
            secid = f"{'1.' if market == 'sh' else '0.'}{clean_code}"

            # 周期映射
            period_map = {
                240: "klt",  # 日线
                30: "klt30",  # 30分钟
                5: "klt5",  # 5分钟
            }

            period = period_map.get(scale, "klt")

            # 东方财富K线数据接口
            url = "https://push2his.eastmoney.com/api/qt/stock/kline/get"
            params = {
                "secid": secid,
                "fields1": "f1,f2,f3,f4,f5,f6",
                "fields2": "f51,f52,f53,f54,f55,f56,f57,f58",
                "klt": period,
                "fqt": "0",  # 不复权
                "lmt": datalen,
                "end": "20500101",  # 结束日期（未来日期表示获取最新）
                "ut": "fa5fd1943c7b386f172d6893dbfba10b",
                "cb": "jQuery1124061234567890_1234567890123",
                "_": str(int(datetime.now().timestamp() * 1000)),
            }

            headers = {
                "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36",
                "Referer": "https://quote.eastmoney.com/",
            }

            print(f"  📡 从东方财富获取数据: {symbol} scale={scale}")

            response = requests.get(url, headers=headers, params=params, timeout=15)

            if response.status_code != 200:
                return None

            # 解析JSONP响应
            text = response.text
            # 移除JSONP包装
            if text.startswith("jQuery") or text.startswith("("):
                start = text.find("{")
                end = text.rfind("}") + 1
                if start >= 0 and end > start:
                    text = text[start:end]

            try:
                data = json.loads(text)
            except:
                return None

            if "data" not in data or not data["data"]:
                return None

            klines = data["data"].get("klines", [])
            if not klines:
                return None

            # 解析数据
            result = []
            for line in klines:
                parts = line.split(",")
                if len(parts) >= 6:
                    try:
                        result.append(
                            {
                                "Date": parts[0],
                                "Open": float(parts[1]),
                                "Close": float(parts[2]),
                                "High": float(parts[3]),
                                "Low": float(parts[4]),
                                "Volume": float(parts[5]),
                            }
                        )
                    except:
                        continue

            if not result:
                return None

            df = pd.DataFrame(result)
            df["Date"] = pd.to_datetime(df["Date"])
            df.set_index("Date", inplace=True)
            df.sort_index(inplace=True)

            print(f"    ✓ 获取到 {len(df)} 条数据")
            return df

        except Exception as e:
            print(f"  ❌ 东方财富获取失败: {e}")
            return None

    @staticmethod
    def fetch_from_tencent(symbol: str, scale: int = 240, datalen: int = 100) -> Optional[pd.DataFrame]:
        """从腾讯财经获取K线数据

        Args:
            symbol: 股票代码
            scale: K线周期，240=日线
            datalen: 数据长度

        Returns:
            pd.DataFrame: K线数据
        """
        try:
            clean_code, market = AShareDataSources._normalize_symbol(symbol)
            if not clean_code:
                return None

            # 腾讯财经只支持日线
            if scale != 240:
                return None

            # 腾讯财经代码格式：sh600460 或 sz000001
            tencent_code = f"{market}{clean_code}"

            # 计算日期范围
            end_date = datetime.now()
            start_date = end_date - timedelta(days=datalen * 2)  # 多取一些，过滤后保留需要的

            url = "http://web.ifzq.gtimg.cn/appstock/app/fqkline/get"
            params = {
                "param": f"{tencent_code},day,{start_date.strftime('%Y-%m-%d')},{end_date.strftime('%Y-%m-%d')},,qfq",
                "_var": "kline_dayqfq",
                "r": str(int(datetime.now().timestamp() * 1000)),
            }

            headers = {
                "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36",
                "Referer": "http://stock.finance.qq.com/",
            }

            print(f"  📡 从腾讯财经获取数据: {symbol} scale={scale}")

            response = requests.get(url, headers=headers, params=params, timeout=15)

            if response.status_code != 200:
                return None

            try:
                data = response.json()
            except:
                return None

            # 解析腾讯财经数据格式
            if tencent_code not in data or "data" not in data[tencent_code]:
                return None

            klines = data[tencent_code]["data"]
            if not klines:
                return None

            result = []
            for item in klines:
                if len(item) >= 6:
                    try:
                        result.append(
                            {
                                "Date": item[0],
                                "Open": float(item[1]),
                                "Close": float(item[2]),
                                "High": float(item[3]),
                                "Low": float(item[4]),
                                "Volume": float(item[5]),
                            }
                        )
                    except:
                        continue

            if not result:
                return None

            df = pd.DataFrame(result)
            df["Date"] = pd.to_datetime(df["Date"])
            df.set_index("Date", inplace=True)
            df.sort_index(inplace=True)
            df = df.tail(datalen)  # 只保留最近的数据

            print(f"    ✓ 获取到 {len(df)} 条数据")
            return df

        except Exception as e:
            print(f"  ❌ 腾讯财经获取失败: {e}")
            return None

    @staticmethod
    def fetch_from_akshare(symbol: str, scale: int = 240, datalen: int = 100) -> Optional[pd.DataFrame]:
        """从AKShare获取K线数据（如果已安装）

        Args:
            symbol: 股票代码
            scale: K线周期
            datalen: 数据长度

        Returns:
            pd.DataFrame: K线数据
        """
        try:
            import akshare as ak
        except ImportError:
            return None

        try:
            clean_code, market = AShareDataSources._normalize_symbol(symbol)
            if not clean_code:
                return None

            # AKShare代码格式：600460 (上海) 或 000001 (深圳)
            ak_code = f"{clean_code}.{'SH' if market == 'sh' else 'SZ'}"

            # 周期映射
            period_map = {
                240: "daily",  # 日线
                30: "30",  # 30分钟
                5: "5",  # 5分钟
                1: "1",  # 1分钟
            }

            period = period_map.get(scale)
            if not period:
                return None

            print(f"  📡 从AKShare获取数据: {symbol} scale={scale}")

            if period == "daily":
                # 日线数据
                df = ak.stock_zh_a_hist(
                    symbol=clean_code,
                    period=period,
                    adjust="qfq",  # 前复权
                    start_date=(datetime.now() - timedelta(days=datalen * 2)).strftime("%Y%m%d"),
                    end_date=datetime.now().strftime("%Y%m%d"),
                )
            else:
                # 分钟数据
                df = ak.stock_zh_a_hist_min_em(
                    symbol=clean_code,
                    period=period,
                    adjust="qfq",
                    start_date=(datetime.now() - timedelta(days=5)).strftime("%Y%m%d"),
                    end_date=datetime.now().strftime("%Y%m%d"),
                )

            if df is None or df.empty:
                return None

            # 标准化列名
            column_map = {
                "日期": "Date",
                "时间": "Date",
                "开盘": "Open",
                "收盘": "Close",
                "最高": "High",
                "最低": "Low",
                "成交量": "Volume",
                "成交额": "Amount",
            }

            df = df.rename(columns=column_map)

            # 确保有Date列
            if "Date" not in df.columns:
                return None

            # 选择需要的列
            required_cols = ["Date", "Open", "High", "Low", "Close", "Volume"]
            available_cols = [col for col in required_cols if col in df.columns]
            df = df[available_cols].copy()

            # 转换数据类型
            for col in ["Open", "High", "Low", "Close", "Volume"]:
                if col in df.columns:
                    df[col] = pd.to_numeric(df[col], errors="coerce")

            df["Date"] = pd.to_datetime(df["Date"])
            df.set_index("Date", inplace=True)
            df.sort_index(inplace=True)
            df = df.tail(datalen)  # 只保留最近的数据

            print(f"    ✓ 获取到 {len(df)} 条数据")
            return df

        except Exception as e:
            print(f"  ❌ AKShare获取失败: {e}")
            return None

    @staticmethod
    def get_kline_with_fallback(symbol: str, scale: int = 240, datalen: int = 100) -> Optional[pd.DataFrame]:
        """获取K线数据 - 自动降级

        数据源优先级：
        1. 新浪财经（由调用方先尝试）
        2. 东方财富
        3. 腾讯财经（仅日线）
        4. AKShare（如果已安装）

        Args:
            symbol: 股票代码
            scale: K线周期
            datalen: 数据长度

        Returns:
            pd.DataFrame: K线数据
        """
        # 注意：新浪财经由调用方先尝试，这里只处理降级

        # 尝试东方财富
        df = AShareDataSources.fetch_from_eastmoney(symbol, scale, datalen)
        if df is not None and not df.empty:
            return df

        # 尝试腾讯财经（仅日线）
        if scale == 240:
            df = AShareDataSources.fetch_from_tencent(symbol, scale, datalen)
            if df is not None and not df.empty:
                return df

        # 尝试AKShare
        df = AShareDataSources.fetch_from_akshare(symbol, scale, datalen)
        if df is not None and not df.empty:
            return df

        return None
