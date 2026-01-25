# 开发中功能模块说明

> **注意**：以下功能模块正在开发调试中，暂不推送到 GitHub 远程仓库。

## 📝 开发中的模块列表

### 1. 每日复盘功能
- `daily_review.py` - 每日复盘主程序
- `DAILY_REVIEW_README.md` - 功能说明文档
- `DAILY_REVIEW_SUMMARY.md` - 功能总结
- `run_daily_review.sh` - 快速运行脚本
- `docs/DAILY_REVIEW_GUIDE.md` - 使用指南
- `.github/workflows/daily_review.yml` - GitHub Actions 工作流

**功能说明**：每天收盘后自动抓取热门板块和股票，生成短线交易清单。

### 2. 缠论分析模块
- `src/analysis/chan_*.py` - 缠论分析核心模块
  - `chan_bi.py` - 笔识别
  - `chan_fractal.py` - 分型识别
  - `chan_kline.py` - K线处理
  - `chan_third_buy.py` - 第三类买点检测
  - `chan_xd.py` - 线段识别
  - `chan_zhongshu.py` - 中枢识别
- `scan_third_buy*.py` - 三买扫描脚本（多个版本）
- `examples/chan_demo.py` - 缠论分析示例

**功能说明**：基于缠论理论的技术分析模块，支持分型、笔、线段、中枢识别和第三类买点检测。

### 3. 监控模块
- `src/monitor/` - 实时监控模块
  - `rule_engine.py` - 规则引擎
  - `run.py` - 监控运行脚本
  - `trading_hours.py` - 交易时间判断
- `.github/workflows/stock_monitor.yml` - 监控工作流

**功能说明**：实时监控股票信号，支持自定义规则引擎和交易时间判断。

### 4. 策略规则配置
- `config/strategy_rules/` - 策略规则配置目录
  - `example.yaml` - 示例配置
  - `test_a_stock.yaml` - 测试配置
  - `README.md` - 配置说明

**功能说明**：策略规则的配置文件，支持 YAML 格式的规则定义。

### 5. 测试和工具脚本
- `run_test_now.sh` - 测试运行脚本
- `test_*.py` - 测试脚本
- `update_market_macd_akshare.py` - 市场 MACD 更新工具
- `stock_cursor.sql` - 数据库 SQL 文件

**功能说明**：开发测试和工具脚本，用于调试和数据处理。

## 🔒 忽略配置

以上模块已添加到 `.gitignore` 文件中，不会被意外提交到远程仓库。

## 📅 更新日期

- 创建日期：2026-01-25
- 最后更新：2026-01-25

## 💡 说明

当这些模块开发完成并测试通过后，可以从 `.gitignore` 中移除相应的条目，然后提交到远程仓库。
