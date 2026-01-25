# 工具与配置 API

## 配置加载

::: src.config.loader
    options:
      show_source: true
      docstring_style: google
      members:
        - Config

## 工具函数

::: src.utils.code_normalizer
    options:
      show_source: true
      docstring_style: google
      members:
        - normalize_code
        - is_hk_stock
        - normalize_hk_code
        - parse_stock_list

::: src.utils.trading_hours
    options:
      show_source: true
      docstring_style: google
      members:
        - is_china_stock_market_open
        - is_hk_stock_market_open

## 统一异常

::: src.utils.exceptions
    options:
      show_source: true
      docstring_style: google
      members:
        - StockAnalysisError
        - DataFetchError
        - IndicatorCalculationError
        - ReportGenerationError
        - ConfigError

## 缓存与并发

::: src.utils.cache
    options:
      show_source: true
      docstring_style: google
      members:
        - DataCache
        - get_cache

::: src.utils.parallel
    options:
      show_source: true
      docstring_style: google
      members:
        - parallel_process
        - batch_process
        - parallel_map
