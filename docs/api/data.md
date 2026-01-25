# 数据获取 API

## 数据获取模块

::: src.data.fetchers
    options:
      show_source: true
      docstring_style: google
      members:
        - get_name
        - fetch_kline_data
        - load_sector_index_map
        - get_market_indices_data
        - get_sector_indices_data
        - normalize_beijing_time
        - filter_trading_hours

## A 股数据

::: src.data.fetchers.a_share_fetcher
    options:
      show_source: true
      docstring_style: google
      members:
        - fetch_kline_data_from_sina
        - fetch_kline_data_fallback
        - fetch_kline_data

## 港股数据

::: src.data.fetchers.hk_stock_fetcher
    options:
      show_source: true
      docstring_style: google
      members:
        - fetch_kline_data_from_hk_sources
        - fetch_alternative_1min_data
