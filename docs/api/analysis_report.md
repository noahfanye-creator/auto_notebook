# 分析与报告 API

## 技术指标

::: src.analysis.indicators
    options:
      show_source: true
      docstring_style: google
      members:
        - calculate_technical_indicators
        - resample_kline_data

## 报告生成

::: src.report.generator
    options:
      show_source: true
      docstring_style: google
      members:
        - process_multiple_stocks
        - create_zip_archive

## 可视化

::: src.visualization.pdf_generator
    options:
      show_source: true
      docstring_style: google
      members:
        - create_pdf_with_market_analysis

::: src.visualization.charts
    options:
      show_source: true
      docstring_style: google
      members:
        - create_candle_chart
        - create_indices_charts
