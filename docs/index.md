# Stock Analysis Bot

股票分析报告生成器：多数据源 K 线获取、技术指标计算、PDF 报告生成。

## 快速开始

```bash
pip install -r requirements-core.txt -r requirements-optional.txt
cp config/config.example.yaml config/config.yaml
python github_stock_bot.py --mode manual --stocks "600460 300474"
```

## 文档导航

- [API - 数据获取](api/data.md)
- [API - 分析与报告](api/analysis_report.md)
- [API - 工具与配置](api/utils_config.md)
- [行业板块使用说明](SECTOR_INDEX_USAGE.md)
- [依赖管理](DEPENDENCIES.md)

## 构建文档

```bash
pip install mkdocs mkdocstrings[python]
mkdocs serve
```
