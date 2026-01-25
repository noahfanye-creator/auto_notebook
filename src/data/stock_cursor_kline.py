# -*- coding: utf-8 -*-
"""从 stock_cursor 库拉取日线/分钟 K 线，供缠论三买测试用。"""
from __future__ import annotations

import os
from typing import List, Optional

import pandas as pd
import pymysql


def _conn():
    host = os.getenv("DB_HOST", "localhost")
    user = os.getenv("DB_USER", "root")
    password = os.getenv("DB_PASSWORD", "root")
    database = os.getenv("DB_NAME", "stock_cursor")
    return pymysql.connect(
        host=host,
        user=user,
        password=password,
        database=database,
        charset="utf8mb4",
    )


def fetch_kline_day(ts_code: str, limit: int = 200) -> Optional[pd.DataFrame]:
    """日线 K 线。返回 DataFrame：Open, High, Low, Close, Volume，索引为 Date。"""
    sql = """
    SELECT trade_date AS Date, open AS Open, high AS High, low AS Low, close AS Close, vol AS Volume
    FROM stock_daily_history
    WHERE ts_code = %s
    ORDER BY trade_date ASC
    LIMIT %s
    """
    try:
        with _conn() as conn:
            df = pd.read_sql(sql, conn, params=(ts_code, limit))
    except Exception as e:
        print(f"  ⚠ DB 日线 {ts_code}: {e}")
        return None
    if df is None or df.empty:
        return None
    df["Date"] = pd.to_datetime(df["Date"])
    df.set_index("Date", inplace=True)
    df.sort_index(inplace=True)
    return df


def fetch_kline_minute(ts_code: str, period: str = "30min", limit: int = 200) -> Optional[pd.DataFrame]:
    """分钟 K 线。period: '30min' | '5min'。返回 Open, High, Low, Close, Volume，索引为 Date。"""
    sql = """
    SELECT datetime AS Date, open AS Open, high AS High, low AS Low, close AS Close, volume AS Volume
    FROM stock_minute_data
    WHERE ts_code = %s AND period_type = %s
    ORDER BY datetime ASC
    LIMIT %s
    """
    try:
        with _conn() as conn:
            df = pd.read_sql(sql, conn, params=(ts_code, period, limit))
    except Exception as e:
        print(f"  ⚠ DB 分钟 {ts_code} {period}: {e}")
        return None
    if df is None or df.empty:
        return None
    df["Date"] = pd.to_datetime(df["Date"])
    df.set_index("Date", inplace=True)
    df.sort_index(inplace=True)
    return df


def get_name(ts_code: str) -> str:
    """从 stock_basic 取名称。"""
    sql = "SELECT name FROM stock_basic WHERE ts_code = %s LIMIT 1"
    try:
        with _conn() as conn:
            with conn.cursor() as cur:
                cur.execute(sql, (ts_code,))
                row = cur.fetchone()
                return row[0] if row else ts_code
    except Exception:
        return ts_code


def list_ts_codes_for_test(limit: int = 20) -> List[str]:
    """取一批 ts_code 用于测试（来自 stock_basic）。"""
    sql = "SELECT ts_code FROM stock_basic ORDER BY ts_code LIMIT %s"
    try:
        with _conn() as conn:
            with conn.cursor() as cur:
                cur.execute(sql, (limit,))
                return [r[0] for r in cur.fetchall()]
    except Exception as e:
        print(f"  ⚠ list_ts_codes: {e}")
        return []


def codes_with_minute_data(period: str = "30min", limit: int = 50) -> List[str]:
    """仅返回在 stock_minute_data 中有该周期数据的 ts_code，用于测试。"""
    sql = """
    SELECT DISTINCT ts_code FROM stock_minute_data WHERE period_type = %s ORDER BY ts_code LIMIT %s
    """
    try:
        with _conn() as conn:
            with conn.cursor() as cur:
                cur.execute(sql, (period, limit))
                return [r[0] for r in cur.fetchall()]
    except Exception as e:
        print(f"  ⚠ codes_with_minute_data: {e}")
        return []
