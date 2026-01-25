"""
报告生成模块
提供批量股票处理和报告生成功能
"""
from .generator import (
    process_multiple_stocks,
    create_zip_archive
)

__all__ = [
    'process_multiple_stocks',
    'create_zip_archive',
]
