"""
日志系统模块
提供结构化的日志记录功能，支持文件和控制台输出
"""

import logging
import sys
from pathlib import Path
from typing import Optional
from datetime import datetime


class ColoredFormatter(logging.Formatter):
    """带颜色的日志格式化器"""

    # ANSI颜色代码
    COLORS = {
        "DEBUG": "\033[36m",  # 青色
        "INFO": "\033[32m",  # 绿色
        "WARNING": "\033[33m",  # 黄色
        "ERROR": "\033[31m",  # 红色
        "CRITICAL": "\033[35m",  # 紫色
        "RESET": "\033[0m",  # 重置
    }

    def format(self, record):
        # 添加颜色
        if record.levelname in self.COLORS:
            record.levelname = f"{self.COLORS[record.levelname]}{record.levelname}{self.COLORS['RESET']}"
        return super().format(record)


def setup_logger(
    name: str, log_file: Optional[str] = None, level: str = "INFO", console: bool = True, log_dir: str = "logs"
) -> logging.Logger:
    """
    设置并返回一个配置好的日志记录器

    Args:
        name: 日志记录器名称（通常使用 __name__）
        log_file: 日志文件名（可选，如 'stock_bot.log'）
        level: 日志级别（DEBUG, INFO, WARNING, ERROR, CRITICAL）
        console: 是否输出到控制台
        log_dir: 日志文件目录

    Returns:
        logging.Logger: 配置好的日志记录器
    """
    logger = logging.getLogger(name)

    # 避免重复添加处理器
    if logger.handlers:
        return logger

    # 设置日志级别
    log_level = getattr(logging, level.upper(), logging.INFO)
    logger.setLevel(log_level)

    # 日志格式
    detailed_format = "%(asctime)s - %(name)s - %(levelname)s - %(message)s"
    simple_format = "%(levelname)s - %(message)s"
    date_format = "%Y-%m-%d %H:%M:%S"

    # 控制台处理器（带颜色）
    if console:
        console_handler = logging.StreamHandler(sys.stdout)
        console_handler.setLevel(log_level)

        # 根据是否支持颜色选择格式化器
        if sys.stdout.isatty():
            console_formatter = ColoredFormatter(simple_format, datefmt=date_format)
        else:
            console_formatter = logging.Formatter(simple_format, datefmt=date_format)

        console_handler.setFormatter(console_formatter)
        logger.addHandler(console_handler)

    # 文件处理器（详细格式）
    if log_file:
        log_path = Path(log_dir)
        log_path.mkdir(parents=True, exist_ok=True)

        file_path = log_path / log_file
        file_handler = logging.FileHandler(file_path, encoding="utf-8")
        file_handler.setLevel(logging.DEBUG)  # 文件记录所有级别

        file_formatter = logging.Formatter(detailed_format, datefmt=date_format)
        file_handler.setFormatter(file_formatter)
        logger.addHandler(file_handler)

    return logger


def get_logger(name: str = None) -> logging.Logger:
    """
    获取日志记录器（便捷函数）
    如果已存在则返回，否则创建新的

    Args:
        name: 日志记录器名称，默认为调用模块名

    Returns:
        logging.Logger: 日志记录器
    """
    if name is None:
        import inspect

        frame = inspect.currentframe().f_back
        name = frame.f_globals.get("__name__", "stock_bot")

    logger = logging.getLogger(name)

    # 如果还没有配置，使用默认配置
    if not logger.handlers:
        try:
            from src.config import Config

            config = Config()
            log_config = config.get("logging", {})

            log_file = log_config.get("file")
            log_level = log_config.get("level", "INFO")
            console = log_config.get("console", True)

            return setup_logger(name, log_file, log_level, console)
        except Exception:
            # 如果配置加载失败，使用默认设置
            return setup_logger(name, "stock_bot.log", "INFO", True)

    return logger
