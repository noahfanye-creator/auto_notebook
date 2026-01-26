"""
市场指数数据获取模块
获取A股和港股市场指数数据；仅从网络获取，不读不写数据库。
"""

from typing import Dict, Any

import pandas as pd

# 导入数据获取和技术分析模块
from .a_share_fetcher import fetch_kline_data
from src.analysis import calculate_technical_indicators


def get_market_indices_data(is_hk: bool = False) -> Dict[str, Any]:
    """获取市场指数数据 - 仅从网络获取，带缓存

    Args:
        is_hk: 是否为港股市场

    Returns:
        dict: {code: {'name': name, 'data': df, 'type': 'A' or 'HK'}}
    """
    # 尝试从缓存获取
    try:
        from src.utils.cache import get_cache

        cache = get_cache()
        if cache is not None:
            # 指数数据缓存6小时
            cached_data = cache.get("get_market_indices_data", ttl_hours=6, is_hk=is_hk)
            if cached_data is not None:
                return cached_data
    except Exception:
        pass

    indices_data = {}

    if is_hk:
        hk_indices = {
            "HSI": "恒生指数",
            "HSCEI": "恒生国企指数",
            "HSTECH": "恒生科技指数",
            "HSCCI": "恒生综合指数",
            "CES100": "恒生中国企业精选100",
        }

        print("📊 获取港股指数数据...")

        try:
            import akshare as ak
        except Exception as e:
            print(f"  ❌ AKShare不可用，无法获取港股指数: {e}")
            return indices_data

        for code, name in hk_indices.items():
            print(f"  获取 {name}...")
            df_raw = None

            try:
                df = ak.stock_hk_index_daily_sina(symbol=code)
                if df is not None and not df.empty:
                    df_raw = df.rename(
                        columns={
                            "date": "Date",
                            "open": "Open",
                            "high": "High",
                            "low": "Low",
                            "close": "Close",
                            "volume": "Volume",
                        }
                    )
                    df_raw["Date"] = pd.to_datetime(df_raw["Date"])
                    df_raw.set_index("Date", inplace=True)
                    df_raw.sort_index(inplace=True)
                    df_raw = df_raw.tail(150)
                else:
                    print("    ❌ 获取失败")
            except Exception as e:
                print(f"    ❌ 获取失败: {e}")

            # 计算技术指标（用于报告）
            if df_raw is not None and not df_raw.empty:
                df = calculate_technical_indicators(df_raw)
                indices_data[code] = {"name": name, "data": df, "type": "HK"}
                print(f"    ✓ 获取成功: {len(df)} 条数据")
            else:
                print("    ❌ 获取失败")
    else:
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
            df_raw = None

            try:
                df_raw = fetch_kline_data(code, 240, 150)
                if df_raw is None or df_raw.empty:
                    print("    ❌ 获取失败")
            except Exception as e:
                print(f"    ❌ 获取失败: {e}")

            # 计算技术指标（用于报告）
            if df_raw is not None and not df_raw.empty:
                df = calculate_technical_indicators(df_raw)
                indices_data[code] = {"name": name, "data": df, "type": "A"}
                print(f"    ✓ 获取成功: {len(df)} 条数据")
            else:
                print("    ❌ 获取失败")

    # 保存到缓存
    if indices_data:
        try:
            from src.utils.cache import get_cache

            cache = get_cache()
            if cache is not None:
                cache.set("get_market_indices_data", indices_data, ttl_hours=6, is_hk=is_hk)
        except Exception:
            pass

    return indices_data
