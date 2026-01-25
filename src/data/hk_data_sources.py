"""
港股数据备选来源（多个免费数据源）
支持：新浪财经、东方财富、AKShare
"""

import logging
import time
from datetime import datetime, timedelta
from typing import Optional

import pandas as pd
import requests

logger = logging.getLogger(__name__)


def _request_with_retry(url, params=None, headers=None, timeout=10, retries=2, backoff=1.0):
    """简单重试封装，缓解临时网络波动"""
    last_exc = None
    for attempt in range(retries + 1):
        try:
            return requests.get(url, params=params, headers=headers, timeout=timeout)
        except Exception as exc:
            last_exc = exc
            if attempt < retries:
                time.sleep(backoff * (attempt + 1))
    if last_exc:
        raise last_exc
    return None


try:
    import akshare as ak

    AK_AVAILABLE = True
except Exception:
    AK_AVAILABLE = False


class HKDataSources:
    """港股数据备选数据源（AKShare）"""

    @staticmethod
    def normalize_code(code: str) -> str:
        """标准化港股代码为5位数字字符串"""
        code = code.strip().upper()
        if code.startswith("HK."):
            code = code[3:]
        if code.endswith(".HK"):
            code = code[:-3]
        if code.isdigit():
            return code.zfill(5)
        return code

    @staticmethod
    def get_stock_name_fallback(code: str) -> Optional[str]:
        """获取港股名称（多个数据源）"""
        symbol = HKDataSources.normalize_code(code)

        # 1. 尝试新浪财经实时行情接口
        try:
            sina_code = f"hk{symbol}"
            url = f"http://hq.sinajs.cn/list={sina_code}"
            headers = {
                "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36",
                "Referer": "https://finance.sina.com.cn",
            }
            response = _request_with_retry(url, headers=headers, timeout=10)
            response.encoding = "gbk"

            if response.status_code == 200:
                content = response.text
                if '="' in content:
                    data_str = content.split('="')[1].split('"')[0]
                    if data_str:
                        parts = data_str.split(",")
                        if len(parts) > 0 and parts[0]:
                            logger.info(f"✅ 从新浪财经获取股票名称: {parts[0]}")
                            return parts[0]
        except Exception as e:
            logger.debug(f"新浪财经获取名称失败: {e}")

        # 2. 尝试东方财富
        try:
            em_code = f"116.{symbol}"
            url = "https://push2.eastmoney.com/api/qt/stock/get"
            params = {"secid": em_code, "fields": "f12,f13,f14"}
            headers = {
                "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36",
                "Referer": "https://quote.eastmoney.com/",
            }
            response = _request_with_retry(url, params=params, headers=headers, timeout=10)
            if response.status_code == 200:
                data = response.json()
                if data.get("data") and data["data"].get("f14"):
                    name = data["data"]["f14"]
                    logger.info(f"✅ 从东方财富获取股票名称: {name}")
                    return name
        except Exception as e:
            logger.debug(f"东方财富获取名称失败: {e}")

        # 3. 尝试AKShare（如果可用）
        if AK_AVAILABLE:
            try:
                df = ak.stock_hk_spot()
                if df is not None and not df.empty:
                    row = df[df["代码"] == symbol]
                    if not row.empty:
                        name = row.iloc[0].get("中文名称")
                        if name:
                            logger.info(f"✅ 从AKShare获取股票名称: {name}")
                            return name
            except Exception as e:
                logger.debug(f"AKShare获取名称失败: {e}")

        return None

    @staticmethod
    def get_kline_from_sina(code: str, period: str = "1d", count: int = 100) -> Optional[pd.DataFrame]:
        """从新浪财经获取港股K线数据"""
        symbol = HKDataSources.normalize_code(code)

        try:
            # 新浪财经港股代码格式：hk02899
            sina_code = f"hk{symbol}"

            logger.info(f"尝试从新浪财经获取港股数据: {sina_code}")

            # 转换周期
            scale_map = {
                "1d": 240,  # 日线
                "1w": 240,  # 周线
                "1M": 240,  # 月线
            }
            scale = scale_map.get(period, 240)

            # 新浪财经港股K线专用接口（注意 URL 和 symbol 参数）
            url = "https://quotes.sina.com.cn/cn/api/jsonp_v2.php/var%20_hk/HK_StockService.getHKKLineData"
            params = {"symbol": symbol, "scale": scale, "datalen": min(count, 1023)}

            headers = {
                "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36",
                "Referer": "https://finance.sina.com.cn",
            }

            response = _request_with_retry(url, params=params, headers=headers, timeout=15)

            if response.status_code != 200:
                return None

            text = response.text
            # 解析 JSONP: var _hk=[{...}];
            if "[" in text and "]" in text:
                json_str = text[text.find("[") : text.rfind("]") + 1]
                import json

                data = json.loads(json_str)
            else:
                return None

            if not data or len(data) == 0:
                return None

            # 转换为DataFrame
            df = pd.DataFrame(data)

            # 标准化列名
            column_map = {
                "day": "Date",
                "open": "Open",
                "high": "High",
                "low": "Low",
                "close": "Close",
                "volume": "Volume",
            }

            df.rename(columns=column_map, inplace=True)

            # 处理日期
            if "Date" in df.columns:
                df["Date"] = pd.to_datetime(df["Date"])
                df.set_index("Date", inplace=True)
                df.sort_index(inplace=True)

            # 转换数据类型
            for col in ["Open", "High", "Low", "Close", "Volume"]:
                if col in df.columns:
                    df[col] = pd.to_numeric(df[col], errors="coerce")

            # 限制数据量
            if len(df) > count:
                df = df.tail(count)

            logger.info(f"✅ 从新浪财经获取 {len(df)} 条数据")
            return df[["Open", "High", "Low", "Close", "Volume"]]

        except Exception as e:
            logger.error(f"新浪财经获取数据失败 {code}: {e}")
            return None

    @staticmethod
    def get_kline_from_eastmoney(code: str, period: str = "1d", count: int = 100) -> Optional[pd.DataFrame]:
        """从东方财富获取港股K线数据"""
        symbol = HKDataSources.normalize_code(code)

        try:
            logger.info(f"尝试从东方财富获取港股数据: {symbol}")

            # 东方财富港股代码格式：116.02899 (116是港股市场代码)
            em_code = f"116.{symbol}"

            # 计算日期范围
            end_date = datetime.now()
            start_date = end_date - timedelta(days=min(count * 2, 365 * 2))

            # 东方财富港股K线接口
            url = "https://push2his.eastmoney.com/api/qt/stock/kline/get"
            params = {
                "secid": em_code,
                "fields1": "f1,f2,f3,f4,f5,f6",
                "fields2": "f51,f52,f53,f54,f55,f56,f57,f58",
                "klt": 101 if period == "1d" else 102,  # 101=日线, 102=周线
                "fqt": 1,
                "beg": start_date.strftime("%Y%m%d"),
                "end": end_date.strftime("%Y%m%d"),
                "lmt": count,
            }

            headers = {
                "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36",
                "Referer": "https://quote.eastmoney.com/",
            }

            response = _request_with_retry(url, params=params, headers=headers, timeout=15)

            if response.status_code != 200:
                return None

            data = response.json()

            if not data.get("data") or not data["data"].get("klines"):
                return None

            klines = data["data"]["klines"]

            # 解析数据
            data_list = []
            for kline_str in klines:
                parts = kline_str.split(",")
                if len(parts) >= 6:
                    try:
                        data_list.append(
                            {
                                "Date": pd.to_datetime(parts[0]),
                                "Open": float(parts[1]),
                                "Close": float(parts[2]),
                                "High": float(parts[3]),
                                "Low": float(parts[4]),
                                "Volume": float(parts[5]),
                            }
                        )
                    except Exception:
                        continue

            if not data_list:
                return None

            df = pd.DataFrame(data_list)
            df.set_index("Date", inplace=True)
            df.sort_index(inplace=True)

            # 限制数据量
            if len(df) > count:
                df = df.tail(count)

            logger.info(f"✅ 从东方财富获取 {len(df)} 条数据")
            return df

        except Exception as e:
            logger.error(f"东方财富获取数据失败 {code}: {e}")
            return None

    @staticmethod
    def get_kline_with_fallback(code: str, period: str = "1d", count: int = 100) -> Optional[pd.DataFrame]:
        """获取港股K线（多个数据源自动降级）"""
        symbol = HKDataSources.normalize_code(code)
        minute_map = {"1m": "1", "5m": "5", "15m": "15", "30m": "30", "60m": "60"}

        # 针对网络不稳定做整体重试
        for attempt in range(3):
            if attempt > 0:
                time.sleep(2 * attempt)

            # 分钟线优先用 AKShare（接口支持分钟）
            if period in minute_map:
                if AK_AVAILABLE:
                    try:
                        now = datetime.now()
                        start = (now - timedelta(days=7)).strftime("%Y-%m-%d 09:30:00")
                        end = now.strftime("%Y-%m-%d %H:%M:%S")
                        df = ak.stock_hk_hist_min_em(
                            symbol=symbol, period=minute_map[period], adjust="", start_date=start, end_date=end
                        )
                        if df is not None and not df.empty:
                            df = df.tail(count).copy()
                            df.rename(
                                columns={
                                    "时间": "Date",
                                    "开盘": "Open",
                                    "收盘": "Close",
                                    "最高": "High",
                                    "最低": "Low",
                                    "成交量": "Volume",
                                },
                                inplace=True,
                            )
                            df["Date"] = pd.to_datetime(df["Date"])
                            df.set_index("Date", inplace=True)
                            df.sort_index(inplace=True)
                            logger.info(f"✅ 从AKShare获取 {len(df)} 条分钟数据")
                            return df
                    except Exception as e:
                        logger.debug(f"AKShare分钟数据失败: {e}")
                continue

            # 1. 优先尝试东方财富（目前对港股最稳定）
            df = HKDataSources.get_kline_from_eastmoney(symbol, period, count)
            if df is not None and not df.empty:
                return df

            # 2. 尝试新浪财经
            df = HKDataSources.get_kline_from_sina(symbol, period, count)
            if df is not None and not df.empty:
                return df

            # 3. 尝试AKShare（如果可用）
            if AK_AVAILABLE:
                try:
                    now = datetime.now()
                    if period in {"1d", "1w", "1M"}:
                        period_map = {"1d": "daily", "1w": "weekly", "1M": "monthly"}
                        df = ak.stock_hk_hist(
                            symbol=symbol,
                            period=period_map[period],
                            start_date=(now - timedelta(days=365 * 3)).strftime("%Y%m%d"),
                            end_date=now.strftime("%Y%m%d"),
                            adjust="",
                        )
                        if df is not None and not df.empty:
                            df = df.tail(count).copy()
                            df.rename(
                                columns={
                                    "日期": "Date",
                                    "开盘": "Open",
                                    "收盘": "Close",
                                    "最高": "High",
                                    "最低": "Low",
                                    "成交量": "Volume",
                                },
                                inplace=True,
                            )
                            df["Date"] = pd.to_datetime(df["Date"])
                            df.set_index("Date", inplace=True)
                            df.sort_index(inplace=True)
                            logger.info(f"✅ 从AKShare获取 {len(df)} 条数据")
                            return df
                except Exception as e:
                    logger.debug(f"AKShare失败: {e}")

        logger.error(f"❌ 所有数据源都无法获取港股数据: {code}")
        return None
