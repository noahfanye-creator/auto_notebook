"""
可选数据库支持（本地积累 + 复用）
使用 SQLite 按 (code, scale) 存储 K 线，先读库、缺的再拉接口、新数据回写
"""
from pathlib import Path
from typing import Optional, List

import pandas as pd


class StockDatabase:
    """SQLite K 线存储，按 (code, scale) 区分周期"""

    def __init__(self, db_path: str = "data/stock_data.db"):
        Path(db_path).parent.mkdir(parents=True, exist_ok=True)
        self.conn = __import__("sqlite3").connect(db_path)
        self._init_tables()

    def _init_tables(self) -> None:
        self.conn.execute(
            """
            CREATE TABLE IF NOT EXISTS kline_by_scale (
                code TEXT NOT NULL,
                scale INTEGER NOT NULL,
                date TEXT NOT NULL,
                open REAL,
                high REAL,
                low REAL,
                close REAL,
                volume REAL,
                PRIMARY KEY (code, scale, date)
            )
            """
        )
        self.conn.execute(
            "CREATE INDEX IF NOT EXISTS idx_kline_code_scale ON kline_by_scale(code, scale)"
        )
        self.conn.commit()

    def save_kline_data(self, code: str, scale: int, df: pd.DataFrame) -> None:
        """写入 K 线，同 (code, scale, date) 已存在则覆盖"""
        if df is None or df.empty:
            return
        subset = (
            df.reset_index()[["Date", "Open", "High", "Low", "Close", "Volume"]]
            .copy()
        )
        subset = subset.rename(
            columns={
                "Date": "date",
                "Open": "open",
                "High": "high",
                "Low": "low",
                "Close": "close",
                "Volume": "volume",
            }
        )
        subset["date"] = subset["date"].astype(str)
        subset["code"] = code
        subset["scale"] = scale
        cols = ["code", "scale", "date", "open", "high", "low", "close", "volume"]
        for _, row in subset[cols].iterrows():
            self.conn.execute(
                """
                INSERT OR REPLACE INTO kline_by_scale (code, scale, date, open, high, low, close, volume)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?)
                """,
                (row["code"], row["scale"], row["date"], row["open"], row["high"], row["low"], row["close"], row["volume"])
            )
        self.conn.commit()

    def get_kline_data(
        self,
        code: str,
        scale: int,
        start_date: Optional[str] = None,
        end_date: Optional[str] = None,
        limit: Optional[int] = None,
    ) -> Optional[pd.DataFrame]:
        """按 (code, scale) 查 K 线，可选日期范围与条数（取最近 limit 条）"""
        query = (
            "SELECT date, open, high, low, close, volume FROM kline_by_scale "
            "WHERE code = ? AND scale = ?"
        )
        params: List[object] = [code, scale]
        if start_date:
            query += " AND date >= ?"
            params.append(start_date)
        if end_date:
            query += " AND date <= ?"
            params.append(end_date)
        query += " ORDER BY date DESC"
        if limit is not None and limit > 0:
            query += f" LIMIT {int(limit)}"
        try:
            df = pd.read_sql_query(query, self.conn, params=params)
        except Exception:
            return None
        if df.empty:
            return None
        df = df.sort_values("date").reset_index(drop=True)
        df = df.rename(
            columns={
                "date": "Date",
                "open": "Open",
                "high": "High",
                "low": "Low",
                "close": "Close",
                "volume": "Volume",
            }
        )
        df["Date"] = pd.to_datetime(df["Date"])
        df.set_index("Date", inplace=True)
        return df

    def get_latest_date(self, code: str, scale: int) -> Optional[pd.Timestamp]:
        """返回 (code, scale) 库中最新一条的日期"""
        row = self.conn.execute(
            "SELECT date FROM kline_by_scale WHERE code = ? AND scale = ? ORDER BY date DESC LIMIT 1",
            (code, scale),
        ).fetchone()
        if not row:
            return None
        return pd.to_datetime(row[0])

    def close(self) -> None:
        self.conn.close()
