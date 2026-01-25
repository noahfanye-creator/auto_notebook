"""
可选数据库模块
SQLite 存储历史 K 线等，供 fetcher 层优先读库、未命中再请求接口并回写
"""

from typing import Optional

from .manager import StockDatabase

_db: Optional[StockDatabase] = None


def get_stock_db() -> Optional[StockDatabase]:
    """根据 config 返回 StockDatabase；未启用则返回 None"""
    global _db
    if _db is not None:
        return _db
    try:
        from src.config import Config

        cfg = Config().load()
        db_cfg = cfg.get("database") or {}
        if not db_cfg.get("enabled", False):
            return None
        path = db_cfg.get("path", "data/stock_data.db")
        _db = StockDatabase(path)
        return _db
    except Exception:
        return None


__all__ = ["StockDatabase", "get_stock_db"]
