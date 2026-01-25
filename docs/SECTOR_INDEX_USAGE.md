# 行业板块指数查询使用说明

## 功能概述

现在可以在生成股票分析报告时，同时查询并展示对应的行业板块指数数据。

## 使用方法

### 命令行方式

```bash
# 通过行业代码查询
python3 github_stock_bot.py --mode manual --stocks "688630" --sector "BK1031"

# 通过行业名称查询
python3 github_stock_bot.py --mode manual --stocks "688630" --sector "光伏设备"

# 多个股票 + 行业指数
python3 github_stock_bot.py --mode manual --stocks "688630 600460" --sector "BK1031"
```

### GitHub Actions 方式

在 `.github/workflows/stock_bot.yml` 的 `workflow_dispatch` 中添加 `sector` 输入：

```yaml
workflow_dispatch:
  inputs:
    stocks:
      description: '输入股票代码'
      required: false
    sector:
      description: '行业代码（如BK1031）或行业名称（如光伏设备）'
      required: false
```

然后在运行步骤中使用：

```yaml
- name: 运行股票分析
  run: |
    export TZ='Asia/Shanghai'
    STOCKS="${{ github.event.inputs.stocks }}"
    SECTOR="${{ github.event.inputs.sector }}"
    if [ -z "$STOCKS" ]; then
      STOCKS="688630,600460,300474,300623,300019"
    fi
    STOCKS="${STOCKS//,/ }"
    SECTOR_ARG=""
    if [ -n "$SECTOR" ]; then
      SECTOR_ARG="--sector $SECTOR"
    fi
    python github_stock_bot.py --mode manual --stocks "$STOCKS" $SECTOR_ARG
```

## 报告内容

当指定了 `--sector` 参数时，报告将包含：

1. **市场指数综合分析**（原有功能）
   - A股：上证、深证、创业板、科创50、沪深300等
   - 港股：恒生指数、恒生国企、恒生科技等

2. **行业板块指数分析**（新增功能）
   - 行业板块指数日线数据
   - 行业板块技术指标（MA、MACD、RSI、KDJ等）
   - 行业板块指数K线图表

## 行业代码对照表

完整的行业代码对照表请查看：[SECTOR_INDEX_MAP.md](./SECTOR_INDEX_MAP.md)

常用行业示例：
- `BK1031` - 光伏设备
- `BK1033` - 电池
- `BK1036` - 半导体
- `BK0737` - 软件开发
- `BK1041` - 医疗器械
- `BK0478` - 有色金属

## 注意事项

1. **数据来源**：行业板块指数数据来自 AKShare（同花顺行业板块）
2. **数据周期**：仅支持日线数据，不支持分钟线
3. **查询方式**：支持通过代码（BK开头）或名称查询，支持模糊匹配
4. **报告格式**：行业指数会在报告中单独展示，位于"市场指数综合分析"之后

## 示例

```bash
# 分析半导体股票，同时查看半导体行业指数
python3 github_stock_bot.py --mode manual --stocks "688630" --sector "半导体"

# 分析电池相关股票，查看电池行业指数
python3 github_stock_bot.py --mode manual --stocks "300750 300014" --sector "BK1033"
```
