"""
交易时间检查模块
检查A股和港股是否为交易日
"""

from datetime import datetime
import pandas as pd

# 可选依赖：akshare
try:
    import akshare as ak
except Exception:
    ak = None


def is_china_stock_market_open() -> bool:
    """
    检查今日是否为A股交易日（自动剔除法定节假日）

    Returns:
        bool: True表示今日是交易日，False表示休市
    """
    try:
        if ak is None:
            print("⚠️  akshare 未安装，跳过交易日检查")
            return True
        # 获取上证指数最新行情
        df = ak.stock_zh_index_daily(symbol="sh000001")
        if df is None or df.empty:
            return True  # 接口故障时默认运行，防止漏发

        # 比较最后交易日与系统今日日期
        last_trade_date = pd.to_datetime(df.iloc[-1]["date"]).date()
        today = datetime.now().date()

        # 如果上证最后交易日期不是今天，说明今天休市
        if last_trade_date != today:
            return False
        return True
    except Exception as e:
        print(f"⚠️ 交易日检查异常: {e}")
        return True


def is_hk_stock_market_open() -> bool:
    """
    检查今日是否为港股交易日

    Returns:
        bool: True表示今日是交易日，False表示休市
    """
    try:
        if ak is None:
            print("⚠️  akshare 未安装，跳过港股交易日检查")
            return True
        # 使用恒生指数判断港股交易日
        df = ak.stock_hk_index_daily_sina(symbol="HSI")
        if df is None or df.empty:
            return True

        last_trade_date = pd.to_datetime(df.iloc[-1]["date"]).date()
        today = datetime.now().date()

        if last_trade_date != today:
            return False
        return True
    except Exception as e:
        print(f"⚠️ 港股交易日检查异常: {e}")
        return True
