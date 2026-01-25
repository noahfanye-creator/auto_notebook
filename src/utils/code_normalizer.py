"""
股票代码标准化模块
支持A股和港股代码的识别和标准化
"""

import re
from typing import List


def is_hk_stock(code: str) -> bool:
    """判断是否为港股代码"""
    code = code.strip().upper()

    # 以.HK结尾
    if code.endswith(".HK"):
        return True

    # 以HK.开头
    if code.startswith("HK."):
        return True

    # 纯数字代码判断
    if code.isdigit():
        # 5位数字（港股通常是5位）
        if len(code) == 5:
            return True
        # 4位数字且以0开头（如0700）
        if len(code) == 4 and code.startswith("0"):
            return True
        # 3位数字且以0开头（如700，补零后是00700）
        if len(code) == 3 and code.startswith("0"):
            return True

    return False


def normalize_hk_code(code: str) -> str:
    """标准化港股代码格式"""
    code = code.strip().upper()

    # 移除.HK后缀
    if code.endswith(".HK"):
        code = code[:-3]

    # 移除HK.前缀
    if code.startswith("HK."):
        code = code[3:]

    # 确保是5位数字
    if code.isdigit():
        code = code.zfill(5)

    # 返回标准格式：HK.00700
    return f"HK.{code}"


def normalize_code(code: str) -> str:
    """标准化代码：区分A股和港股市场"""
    code = code.strip()

    # 检查是否为港股
    if is_hk_stock(code):
        return normalize_hk_code(code)

    # 如果是 6 位数字，判定为 A 股
    if re.match(r"^\d{6}$", code):
        if code.startswith("6"):  # 沪市（包括科创板）
            return f"sh{code}"
        if code.startswith("0") or code.startswith("3"):  # 深市/创业板
            return f"sz{code}"

    # 如果已经是带前缀的代码，直接返回
    if code.startswith("sh") or code.startswith("sz"):
        return code

    return code


def parse_stock_list(stocks_input: str) -> List[str]:
    """解析股票列表，支持逗号与空格分隔"""
    if not stocks_input:
        return []
    normalized = stocks_input.replace(",", " ").replace("，", " ")
    return [item for item in normalized.split() if item]
