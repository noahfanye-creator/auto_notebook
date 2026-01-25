"""StockDatabase 单元测试"""
import os
import tempfile

import pandas as pd

from src.database.manager import StockDatabase


class TestStockDatabase:
    """StockDatabase 测试"""

    def test_save_get_kline_data(self):
        """保存与读取 K 线（Date 为 index）"""
        with tempfile.TemporaryDirectory() as d:
            db_path = os.path.join(d, "t.db")
            db = StockDatabase(db_path)
            df = pd.DataFrame(
                {
                    "Open": [100.0] * 5,
                    "High": [105.0] * 5,
                    "Low": [95.0] * 5,
                    "Close": [102.0] * 5,
                    "Volume": [1e6] * 5,
                },
                index=pd.date_range("2024-01-01", periods=5, freq="B"),
            )
            df.index.name = "Date"
            n = db.save_kline_data("sh600460", 240, df, validate=True)
            assert n == 5
            out = db.get_kline_data("sh600460", 240, limit=3)
            assert out is not None
            assert len(out) == 3
            assert list(out.columns) == ["Open", "High", "Low", "Close", "Volume"]
            db.close()

    def test_validate_data_rejects_invalid(self):
        """validate_data 拒绝无效数据"""
        with tempfile.TemporaryDirectory() as d:
            db = StockDatabase(os.path.join(d, "t.db"))
            # 空 DataFrame
            assert db.validate_data(pd.DataFrame()) is False
            # 缺列
            bad = pd.DataFrame({"Open": [1], "Close": [1]})
            assert db.validate_data(bad) is False
            # 负价格
            df = pd.DataFrame(
                {
                    "Date": pd.date_range("2024-01-01", periods=2, freq="B"),
                    "Open": [100, 100],
                    "High": [105, 105],
                    "Low": [95, 95],
                    "Close": [-1, 102],
                    "Volume": [1e6, 1e6],
                }
            )
            df.set_index("Date", inplace=True)
            assert db.validate_data(df) is False
            db.close()

    def test_get_stats(self):
        """get_stats 返回统计信息"""
        with tempfile.TemporaryDirectory() as d:
            db_path = os.path.join(d, "t.db")
            db = StockDatabase(db_path)
            df = pd.DataFrame(
                {
                    "Open": [100.0],
                    "High": [105.0],
                    "Low": [95.0],
                    "Close": [102.0],
                    "Volume": [1e6],
                },
                index=pd.DatetimeIndex(["2024-01-01"], name="Date"),
            )
            db.save_kline_data("sh600460", 240, df)
            stats = db.get_stats()
            assert "total_kline_records" in stats
            assert stats["total_kline_records"] >= 1
            assert "total_stocks" in stats
            db.close()
