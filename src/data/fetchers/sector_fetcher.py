"""
行业板块数据获取模块
获取行业板块指数数据
"""

import os
import json
from typing import Optional, Dict, Any


def load_sector_index_map() -> Dict[str, Any]:
    """加载行业代码对照表"""
    try:
        # 获取项目根目录
        current_dir = os.path.dirname(os.path.abspath(__file__))
        project_root = os.path.dirname(os.path.dirname(os.path.dirname(os.path.dirname(current_dir))))
        config_path = os.path.join(project_root, "config", "sector_index_map.json")

        if os.path.exists(config_path):
            with open(config_path, "r", encoding="utf-8") as f:
                return json.load(f)
    except Exception as e:
        print(f"⚠️ 加载行业代码对照表失败: {e}")
    return {"code_to_name": {}, "name_to_code": {}}


def get_sector_index_name(sector_input: str) -> Optional[str]:
    """根据代码或名称获取行业名称"""
    sector_map = load_sector_index_map()
    code_to_name = sector_map.get("code_to_name", {})
    name_to_code = sector_map.get("name_to_code", {})

    # 如果是代码（BK开头）
    if sector_input.startswith("BK") and sector_input in code_to_name:
        return code_to_name[sector_input]
    # 如果是名称
    elif sector_input in name_to_code:
        return sector_input
    # 尝试模糊匹配
    else:
        for code, name in code_to_name.items():
            if sector_input in name or name in sector_input:
                return name
    return None


def get_sector_indices_data(sector_input: Optional[str] = None, count: int = 150) -> Dict[str, Any]:
    """
    获取行业板块指数数据

    Args:
        sector_input: 行业代码（如"BK1031"）或行业名称（如"光伏设备"）
        count: 获取数据条数

    Returns:
        dict: {code: {'name': name, 'data': df, 'type': 'SECTOR'}}
    """
    sector_data = {}

    if not sector_input:
        return sector_data

    try:
        import akshare as ak
    except Exception as e:
        print(f"  ❌ AKShare不可用，无法获取行业板块指数: {e}")
        return sector_data

    # 获取行业名称
    sector_name = get_sector_index_name(sector_input)
    if not sector_name:
        print(f"  ❌ 未找到行业: {sector_input}")
        return sector_data

    print(f"📊 获取行业板块指数数据: {sector_name}")

    try:
        # 获取行业板块日线K线
        df = ak.stock_board_industry_hist_em(symbol=sector_name, period="日k", adjust="")

        if df is not None and not df.empty:
            import pandas as pd

            # 标准化列名
            df = df.rename(
                columns={
                    "日期": "Date",
                    "开盘": "Open",
                    "收盘": "Close",
                    "最高": "High",
                    "最低": "Low",
                    "成交量": "Volume",
                }
            )

            # 处理日期
            df["Date"] = pd.to_datetime(df["Date"])
            df.set_index("Date", inplace=True)
            df.sort_index(inplace=True)

            # 限制数据量
            df = df.tail(count)

            # 计算技术指标
            from src.analysis import calculate_technical_indicators

            df = calculate_technical_indicators(df)

            # 获取行业代码
            sector_map = load_sector_index_map()
            name_to_code = sector_map.get("name_to_code", {})
            sector_code = name_to_code.get(sector_name, sector_input)

            sector_data[sector_code] = {"name": sector_name, "data": df, "type": "SECTOR"}
            print(f"    ✓ 获取成功: {len(df)} 条数据")
        else:
            print("    ❌ 数据为空")
    except Exception as e:
        print(f"    ❌ 获取失败: {e}")
        import traceback

        traceback.print_exc()

    return sector_data
