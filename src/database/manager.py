"""
可选数据库支持（本地积累 + 复用）
使用 SQLite 按 (code, scale) 存储 K 线，先读库、缺的再拉接口、新数据回写
增强版：支持数据验证、元数据跟踪、市场指数存储
"""

from pathlib import Path
from typing import Optional, List, Dict, Any
from datetime import datetime

import pandas as pd

from src.utils.logger import get_logger

logger = get_logger(__name__)


class StockDatabase:
    """SQLite K 线存储，按 (code, scale) 区分周期"""

    def __init__(self, db_path: str = "data/stock_data.db"):
        Path(db_path).parent.mkdir(parents=True, exist_ok=True)
        self.db_path = db_path
        self.conn = __import__("sqlite3").connect(db_path)
        self._init_tables()

    def _init_tables(self) -> None:
        """初始化数据库表结构"""
        # 表1: K线数据表（增强版：添加时间戳字段）
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
                created_at TEXT DEFAULT CURRENT_TIMESTAMP,
                updated_at TEXT DEFAULT CURRENT_TIMESTAMP,
                PRIMARY KEY (code, scale, date)
            )
            """
        )

        # 表2: 元数据表（跟踪数据状态）
        self.conn.execute(
            """
            CREATE TABLE IF NOT EXISTS meta_info (
                code TEXT NOT NULL,
                stock_name TEXT,
                market_type TEXT,
                last_update_date TEXT,
                last_update_scale INTEGER,
                data_count INTEGER DEFAULT 0,
                last_success_at TEXT,
                created_at TEXT DEFAULT CURRENT_TIMESTAMP,
                updated_at TEXT DEFAULT CURRENT_TIMESTAMP,
                PRIMARY KEY (code)
            )
            """
        )

        # 表3: 市场指数数据表
        self.conn.execute(
            """
            CREATE TABLE IF NOT EXISTS market_indices (
                index_code TEXT NOT NULL,
                index_name TEXT,
                scale INTEGER NOT NULL,
                date TEXT NOT NULL,
                open REAL,
                high REAL,
                low REAL,
                close REAL,
                volume REAL,
                created_at TEXT DEFAULT CURRENT_TIMESTAMP,
                updated_at TEXT DEFAULT CURRENT_TIMESTAMP,
                PRIMARY KEY (index_code, scale, date)
            )
            """
        )

        # 创建索引
        self.conn.execute("CREATE INDEX IF NOT EXISTS idx_kline_code_scale ON kline_by_scale(code, scale)")
        self.conn.execute("CREATE INDEX IF NOT EXISTS idx_kline_date ON kline_by_scale(date)")
        self.conn.execute("CREATE INDEX IF NOT EXISTS idx_index_code_scale ON market_indices(index_code, scale)")

        self.conn.commit()
        logger.info("数据库表初始化完成")

    def validate_data(self, df: pd.DataFrame) -> bool:
        """
        验证数据有效性
        确保只有成功返回的有效数据才写入数据库

        Args:
            df: 待验证的DataFrame（Date 可为 index 或列）

        Returns:
            bool: 数据是否有效
        """
        if df is None or df.empty:
            return False

        # 统一为列格式：Date 常为 index
        work = df.reset_index() if "Date" not in df.columns else df.copy()
        required_cols = ["Date", "Open", "High", "Low", "Close", "Volume"]
        if not all(c in work.columns for c in required_cols):
            logger.warning("数据缺少必需列")
            return False

        try:
            # 1. 价格数据应为正数
            for col in ["Open", "High", "Low", "Close"]:
                if work[col].isna().all():
                    logger.warning("价格数据全为空: %s", col)
                    return False
                valid = work[col].dropna()
                if len(valid) == 0 or (valid <= 0).any():
                    logger.warning("价格数据无效: %s", col)
                    return False
            # 2. High >= Low
            v = work.dropna(subset=["High", "Low"])
            if len(v) > 0 and (v["High"] < v["Low"]).any():
                logger.warning("最高价低于最低价")
                return False
            # 3. Volume >= 0
            vv = work["Volume"].dropna()
            if len(vv) > 0 and (vv < 0).any():
                logger.warning("成交量为负数")
                return False
            # 4. 无重复日期
            dates = work["Date"]
            if dates.duplicated().any():
                logger.warning("存在重复日期")
                return False
            logger.debug("数据验证通过: %d 条记录", len(work))
            return True
        except Exception as e:
            logger.warning("数据验证过程出错: %s", e)
            return False

    def save_kline_data(
        self, code: str, scale: int, df: pd.DataFrame, stock_name: Optional[str] = None, validate: bool = True
    ) -> int:
        """
        写入 K 线数据（只有成功返回的数据才写入）

        Args:
            code: 股票代码
            scale: K线周期
            df: K线数据DataFrame
            stock_name: 股票名称（可选）
            validate: 是否验证数据（默认True，确保只有有效数据才写入）

        Returns:
            int: 实际写入的记录数，如果验证失败返回0
        """
        # 数据验证：只有成功返回的有效数据才写入
        if validate and not self.validate_data(df):
            logger.warning("数据验证失败，不写入数据库: %s scale=%s", code, scale)
            return 0

        if df is None or df.empty:
            return 0

        try:
            subset = df.reset_index()[["Date", "Open", "High", "Low", "Close", "Volume"]].copy()
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

            now = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
            inserted_count = 0

            for _, row in subset.iterrows():
                try:
                    self.conn.execute(
                        """
                        INSERT OR REPLACE INTO kline_by_scale 
                        (code, scale, date, open, high, low, close, volume, updated_at)
                        VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
                        """,
                        (
                            str(row["code"]),
                            int(row["scale"]),
                            str(row["date"]),
                            float(row["open"]),
                            float(row["high"]),
                            float(row["low"]),
                            float(row["close"]),
                            float(row["volume"]),
                            now,
                        ),
                    )
                    inserted_count += 1
                except Exception as e:
                    logger.warning("插入单条记录失败: %s", e)
                    continue

            self.conn.commit()

            # 更新元数据
            if inserted_count > 0:
                self._update_meta_info(code, scale, stock_name, len(subset), df.index.max())
                logger.info("DB 写入成功: %s scale=%s %d 条", code, scale, inserted_count)

            return inserted_count

        except Exception as e:
            logger.error("保存K线数据失败: %s", e)
            self.conn.rollback()
            return 0

    def _update_meta_info(
        self, code: str, scale: int, stock_name: Optional[str], data_count: int, latest_date: pd.Timestamp
    ) -> None:
        """更新元数据表"""
        try:
            now = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
            latest_date_str = latest_date.strftime("%Y-%m-%d %H:%M:%S")

            # 获取市场类型
            market_type = "A股" if code.startswith(("sh", "sz")) else "港股"

            self.conn.execute(
                """
                INSERT OR REPLACE INTO meta_info 
                (code, stock_name, market_type, last_update_date, last_update_scale, 
                 data_count, last_success_at, updated_at)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?)
                """,
                (code, stock_name, market_type, latest_date_str, scale, data_count, now, now),
            )
            self.conn.commit()
        except Exception as e:
            logger.warning("更新元数据失败: %s", e)

    def get_kline_data(
        self,
        code: str,
        scale: int,
        start_date: Optional[str] = None,
        end_date: Optional[str] = None,
        limit: Optional[int] = None,
    ) -> Optional[pd.DataFrame]:
        """按 (code, scale) 查 K 线，可选日期范围与条数（取最近 limit 条）"""
        query = "SELECT date, open, high, low, close, volume FROM kline_by_scale " "WHERE code = ? AND scale = ?"
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

    def save_market_index_data(
        self, index_code: str, index_name: str, scale: int, df: pd.DataFrame, validate: bool = True
    ) -> int:
        """保存市场指数数据（只有成功返回的数据才写入）"""
        if validate and not self.validate_data(df):
            logger.warning("指数数据验证失败: %s", index_code)
            return 0

        if df is None or df.empty:
            return 0

        try:
            subset = df.reset_index()[["Date", "Open", "High", "Low", "Close", "Volume"]].copy()
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
            subset["index_code"] = index_code
            subset["index_name"] = index_name
            subset["scale"] = scale

            now = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
            inserted_count = 0

            for _, row in subset.iterrows():
                try:
                    self.conn.execute(
                        """
                        INSERT OR REPLACE INTO market_indices 
                        (index_code, index_name, scale, date, open, high, low, close, volume, updated_at)
                        VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                        """,
                        (
                            index_code,
                            index_name,
                            scale,
                            str(row["date"]),
                            float(row["open"]),
                            float(row["high"]),
                            float(row["low"]),
                            float(row["close"]),
                            float(row["volume"]),
                            now,
                        ),
                    )
                    inserted_count += 1
                except Exception as e:
                    logger.warning("插入指数数据失败: %s", e)
                    continue

            self.conn.commit()
            if inserted_count > 0:
                logger.info("指数 DB 写入成功: %s %d 条", index_code, inserted_count)
            return inserted_count

        except Exception as e:
            logger.error("保存指数数据失败: %s", e)
            self.conn.rollback()
            return 0

    def get_market_index_data(self, index_code: str, scale: int, limit: Optional[int] = None) -> Optional[pd.DataFrame]:
        """获取市场指数数据"""
        query = (
            "SELECT date, open, high, low, close, volume FROM market_indices "
            "WHERE index_code = ? AND scale = ? ORDER BY date DESC"
        )

        if limit:
            query += f" LIMIT {int(limit)}"

        try:
            df = pd.read_sql_query(query, self.conn, params=(index_code, scale))
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

            for col in ["Open", "High", "Low", "Close", "Volume"]:
                df[col] = pd.to_numeric(df[col], errors="coerce")

            return df
        except Exception as e:
            logger.error("读取指数数据失败: %s", e)
            return None

    def get_stats(self) -> Dict[str, Any]:
        """获取数据库统计信息"""
        stats = {}

        try:
            # K线数据统计
            cursor = self.conn.execute("SELECT COUNT(*) FROM kline_by_scale")
            stats["total_kline_records"] = cursor.fetchone()[0]

            cursor = self.conn.execute("SELECT COUNT(DISTINCT code) FROM kline_by_scale")
            stats["total_stocks"] = cursor.fetchone()[0]

            # 指数数据统计
            cursor = self.conn.execute("SELECT COUNT(*) FROM market_indices")
            stats["total_index_records"] = cursor.fetchone()[0]

            cursor = self.conn.execute("SELECT COUNT(DISTINCT index_code) FROM market_indices")
            stats["total_indices"] = cursor.fetchone()[0]

            # 数据库文件大小
            db_file = Path(self.db_path)
            if db_file.exists():
                stats["db_size_mb"] = db_file.stat().st_size / (1024 * 1024)

        except Exception as e:
            logger.error("获取统计信息失败: %s", e)

        return stats

    def close(self) -> None:
        """关闭数据库连接"""
        self.conn.close()

    def __enter__(self):
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        self.close()
