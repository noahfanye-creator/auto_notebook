"""
独立的股票数据获取模块
支持 A 股和港股
"""

import requests
import pandas as pd
import re
from loguru import logger


def normalize_code(code: str) -> str:
    """标准化股票代码"""
    code = code.strip()

    # 港股代码
    if code.startswith("HK.") or code.endswith(".HK"):
        if code.endswith(".HK"):
            code = code[:-3]
        if code.startswith("HK."):
            code = code[3:]
        return f"HK.{code.zfill(5)}"

    # A股代码
    if re.match(r"^\d{6}$", code):
        if code.startswith("6"):
            return f"sh{code}"
        elif code.startswith(("0", "3")):
            return f"sz{code}"

    return code


def get_stock_name(code: str) -> str:
    """获取股票名称"""
    try:
        if code.startswith("HK."):
            # 港股名称映射（简化版）
            return f"港股{code}"

        # A股使用新浪财经
        url = f"http://hq.sinajs.cn/list={code}"
        headers = {"User-Agent": "Mozilla/5.0", "Referer": "https://finance.sina.com.cn"}
        response = requests.get(url, headers=headers, timeout=10)
        response.encoding = "gbk"

        if response.status_code == 200 and '="' in response.text:
            data = response.text.split('="')[1].split('"')[0]
            if data:
                return data.split(",")[0]
    except Exception:
        pass

    return code


def fetch_stock_data(code: str, period: str = "5m", count: int = 100) -> pd.DataFrame:
    """
    获取股票数据

    Args:
        code: 股票代码
        period: 周期 ('1m', '5m', '15m', '30m', '1h', '1d')
        count: 数据条数

    Returns:
        DataFrame with columns: Date, Open, High, Low, Close, Volume
    """
    code = normalize_code(code)

    # 周期映射
    scale_map = {"1m": 1, "5m": 5, "15m": 15, "30m": 30, "1h": 60, "1d": 240}
    scale = scale_map.get(period, 5)

    try:
        # 新浪财经 API
        if scale == 240:
            url = "https://quotes.sina.cn/cn/api/openapi.php/CN_MarketDataService.getKLineData"
        else:
            url = "https://quotes.sina.cn/cn/api/openapi.php/StockV2Service.getMinLine"

        params = {"symbol": code.upper(), "scale": scale, "datalen": count, "ma": "no"}

        headers = {"User-Agent": "Mozilla/5.0", "Referer": "https://finance.sina.com.cn"}

        response = requests.get(url, headers=headers, params=params, timeout=15)

        if response.status_code != 200:
            logger.error(f"获取数据失败: HTTP {response.status_code}")
            return None

        data = response.json()

        if not data or "result" not in data or "data" not in data["result"]:
            logger.warning("主接口数据格式错误，尝试备用接口...")
            return fetch_stock_data_fallback(code, scale, count)

        # 解析数据
        klines = []
        for item in data["result"]["data"]:
            try:
                if scale == 240:
                    klines.append(
                        {
                            "Date": item["day"],
                            "Open": float(item["open"]),
                            "High": float(item["high"]),
                            "Low": float(item["low"]),
                            "Close": float(item["close"]),
                            "Volume": float(item.get("volume", 0)),
                        }
                    )
                else:
                    klines.append(
                        {
                            "Date": f"{item['d']} {item['t']}:00",
                            "Open": float(item["o"]),
                            "High": float(item["h"]),
                            "Low": float(item["l"]),
                            "Close": float(item["c"]),
                            "Volume": float(item.get("v", 0)),
                        }
                    )
            except Exception:
                continue

        if not klines:
            logger.error("无有效数据")
            return None

        df = pd.DataFrame(klines)
        df["Date"] = pd.to_datetime(df["Date"])
        df.set_index("Date", inplace=True)
        df.sort_index(inplace=True)

        logger.info(f"成功获取 {len(df)} 条数据: {code}")
        return df

    except Exception as e:
        logger.error(f"获取股票数据失败 {code}: {e}")
        return fetch_stock_data_fallback(code, scale, count)


def fetch_stock_data_fallback(code: str, scale: int, count: int) -> pd.DataFrame:
    """备用数据接口"""
    try:
        url = "http://money.finance.sina.com.cn/quotes_service/api/json_v2.php/CN_MarketData.getKLineData"
        params = {"symbol": code, "scale": scale, "ma": "no", "datalen": count}

        response = requests.get(url, params=params, timeout=15)
        if response.status_code != 200:
            return None

        data = response.json()
        if not data:
            return None

        df = pd.DataFrame(data)
        df.rename(
            columns={"day": "Date", "open": "Open", "high": "High", "low": "Low", "close": "Close", "volume": "Volume"},
            inplace=True,
        )

        for col in ["Open", "High", "Low", "Close", "Volume"]:
            if col in df.columns:
                df[col] = pd.to_numeric(df[col], errors="coerce")

        df["Date"] = pd.to_datetime(df["Date"])
        df.set_index("Date", inplace=True)
        df.sort_index(inplace=True)

        logger.info(f"备用接口获取成功: {code}")
        return df if not df.empty else None

    except Exception as e:
        logger.error(f"备用接口也失败: {e}")
        return None
