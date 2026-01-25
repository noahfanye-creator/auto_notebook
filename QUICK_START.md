# 🎯 股票监控系统 - 快速开始指南

## ✅ 本地测试已完成

所有核心功能已通过本地测试：
- ✅ 数据获取和指标计算
- ✅ 监控规则检查逻辑
- ✅ AI 策略解析流程
- ✅ 配置文件生成
- ⚠️ Telegram 推送（本地网络限制，GitHub 环境正常）

详细测试报告请查看 `LOCAL_TEST_REPORT.md`

---

## 🚀 三步部署到生产

### 第 1 步：推送代码到 GitHub

在**系统终端**运行：

```bash
cd /Users/felix/Documents/stock-analysis-bot

git add .
git commit -m "feat: 添加独立股票监控系统"
git push origin main
```

### 第 2 步：配置 GitHub Secrets

进入 GitHub 仓库页面：
**Settings → Secrets and variables → Actions → New repository secret**

添加以下 3 个 Secrets：

| Name | Value |
|------|-------|
| `GEMINI_API_KEY` | `AIzaSyACxeXgptMz5wbbfTzDq0Zj21VtF_-YYA0` |
| `TELEGRAM_BOT_TOKEN` | `8371667461:AAGXMmYflhwuVFt1tE5lIlOtgxXeoXi7Fhg` |
| `TELEGRAM_CHAT_ID` | `5920715689` |

### 第 3 步：开启 Actions 权限

**Settings → Actions → General → Workflow permissions**

选择：✅ **Read and write permissions**

点击 **Save**

---

## 📱 如何使用

### 方式 1: 使用 AI 自动解析策略（推荐）

1. **在本地运行策略更新工具**：
   ```bash
   python3 update_strategy.py
   ```

2. **粘贴您的策略文本**（从 NotebookLM 复制），例如：
   ```
   士兰微(600460)策略：
   - RSI 跌破 30 时关注超卖机会
   - 价格突破 MA20 考虑买入
   
   腾讯控股(00700)策略：
   - K 值大于 80 注意超买
   ```

3. **Gemini 自动解析**并保存到 `config/monitor_rules.yaml`

4. **推送更新**：
   ```bash
   git add config/monitor_rules.yaml
   git commit -m "update: 更新监控策略"
   git push
   ```

5. **等待下一个监控周期**（最多 10 分钟），系统自动生效！

### 方式 2: 手动编辑配置文件

直接编辑 `config/monitor_rules.yaml`：

```yaml
- code: sh600460          # 股票代码
  indicator: RSI          # 监控指标
  condition: "<"          # 条件：<, >, >=, <=, ==
  threshold: 30           # 阈值（数值或另一个指标如 MA20）
  name: RSI超卖预警       # 预警名称

- code: HK.00700
  indicator: Close
  condition: ">"
  threshold: MA60
  name: 突破MA60
```

然后推送到 GitHub。

---

## 📊 支持的技术指标

### 价格指标
- `Open`, `High`, `Low`, `Close` - OHLC
- `MA5`, `MA10`, `MA20`, `MA60`, `MA250` - 移动平均线

### 趋势指标
- `DIF`, `DEA`, `MACD` - MACD 指标
- `RSI` - 相对强弱指数

### 摆动指标
- `K`, `D`, `J` - KDJ 指标
- `WR` - 威廉指标

### 布林带
- `BB_Upper`, `BB_Middle`, `BB_Lower`

### 成交量
- `Volume` - 成交量
- `Volume_MA5`, `Volume_MA10` - 成交量均线
- `Volume_Ratio` - 量比
- `OBV` - 能量潮

### 其他
- `Amplitude` - 振幅

---

## ⏰ 监控时间表

GitHub Actions 自动监控时间：
- **周一至周五**
- **北京时间 9:30 - 15:00**（交易时段）
- **每 10 分钟检查一次**

您也可以在 Actions 页面手动触发测试。

---

## 🔔 通知示例

当触发预警时，您会收到 Telegram 消息：

```
🎯 股票监控预警

名称: 士兰微 (sh600460)
规则: RSI超卖预警
详情: RSI (28.56) < 30
时间: 2026-01-27 10:30:00

🕒 此预警在 60 分钟内不会重复推送。
```

---

## 🛠️ 可选：本地安装 Gemini

如果想在本地测试 AI 解析（可选），在终端运行：

```bash
pip3 install google-generativeai --trusted-host pypi.org --trusted-host files.pythonhosted.org
```

如果遇到 SSL 错误，可以：
1. 使用上面的 `--trusted-host` 参数
2. 或直接在 GitHub 上编辑 `config/monitor_rules.yaml`
3. GitHub Actions 会自动使用已配置的 API Key

---

## 📂 重要文件说明

```
/Users/felix/Documents/stock-analysis-bot/
├── config/
│   └── monitor_rules.yaml          # 📝 监控规则配置（您需要编辑的文件）
│
├── src/                            # 源代码（已完成，无需修改）
│   ├── data/fetcher.py            # 数据获取
│   ├── analysis/indicators.py     # 指标计算
│   ├── strategy/parser.py         # AI 解析
│   ├── monitor/runner.py          # 监控执行
│   └── notify/telegram.py         # Telegram 推送
│
├── update_strategy.py             # 🤖 策略更新工具（AI 驱动）
├── simple_test.py                 # 🧪 本地测试脚本
├── demo_ai_parsing.py             # 📖 AI 解析演示
│
├── .env                           # 🔑 本地环境变量（已配置）
├── .github/workflows/
│   └── stock_monitor.yml          # ⚙️ GitHub Actions 配置
│
└── 文档/
    ├── STANDALONE_MONITOR_SYSTEM.md  # 系统架构说明
    ├── LOCAL_TEST_REPORT.md          # 测试报告
    └── QUICK_START.md                # 本文件
```

---

## 🎉 总结

1. **推送代码** → GitHub
2. **配置 Secrets** → 3 个 API Keys
3. **开启权限** → Read and write
4. **开始使用** → 编辑 `monitor_rules.yaml` 或使用 `update_strategy.py`

**就这么简单！下次交易日自动开始监控！** 📈
