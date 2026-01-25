"""
统一异常体系
便于区分错误类型、统一日志与重试逻辑
"""


class StockAnalysisError(Exception):
    """股票分析基础异常"""

    pass


class DataFetchError(StockAnalysisError):
    """数据获取失败"""

    pass


class IndicatorCalculationError(StockAnalysisError):
    """指标计算错误"""

    pass


class ReportGenerationError(StockAnalysisError):
    """报告生成错误"""

    pass


class ConfigError(StockAnalysisError):
    """配置加载或解析错误"""

    pass
