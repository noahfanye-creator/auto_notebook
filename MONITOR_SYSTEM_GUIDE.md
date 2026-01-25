# 股票监控系统使用指南

## 📋 系统概述

本系统实现了从 AI 策略解析到自动监控并推送 Telegram 的完整闭环，包含以下核心功能：

1. **AI 策略解析**：使用 Gemini API 从 NotebookLM 策略文本中自动提取监控规则
2. **实时监控**：每 10 分钟自动检查股票指标
3. **智能推送**：触发条件时通过 Telegram 推送预警
4. **冷却机制**：避免短时间内重复推送同一信号

## 🚀 快速开始

### 1. 安装依赖

```bash
pip install -r requirements.txt
```

**注意**：如果遇到 SSL 证书问题，可以尝试：
```bash
pip install --trusted-host pypi.org --trusted-host files.pythonhosted.org google-generativeai
```

或者使用国内镜像：
```bash
pip install -i https://pypi.tuna.tsinghua.edu.cn/simple google-generativeai
```

### 2. 配置环境变量

复制 `.env.example` 为 `.env`，并填入您的实际配置：

```bash
cp .env.example .env
```

编辑 `.env` 文件：
```
GEMINI_API_KEY=你的_Gemini_API_密钥
TELEGRAM_BOT_TOKEN=你的_Telegram_Bot_Token
TELEGRAM_CHAT_ID=你的_Telegram_用户ID
MONITOR_COOLDOWN_MINUTES=60
```

#### 获取各项配置：

**Gemini API Key**:
- 访问 https://makersuite.google.com/app/apikey
- 创建 API Key

**Telegram Bot Token**:
- 在 Telegram 中搜索 `@BotFather`
- 发送 `/newbot` 创建机器人
- 获取 Token

**Telegram Chat ID**:
- 在 Telegram 中搜索 `@userinfobot`
- 发送任意消息获取您的 Chat ID

### 3. 解析策略并生成监控规则

运行策略解析工具：

```bash
python3 update_strategy.py
```

然后粘贴您从 NotebookLM 复制的策略文本，例如：

```
士兰微(600460)分析：
- 当 RSI 跌破 30 时，可能进入超卖区，建议关注
- 价格突破 MA20 向上时，考虑买入机会

腾讯控股(00700.HK)：
- K 值大于 80，注意超买风险
```

输入完成后，输入 `EOF` 结束。系统会自动解析并保存到 `config/monitor_rules.yaml`。

### 4. 本地测试

运行测试脚本验证系统功能：

```bash
python3 test_monitor_system.py
```

这将测试：
- ✅ Gemini AI 策略解析
- ✅ Telegram 消息推送
- ✅ 股票数据获取和指标计算
- ✅ 监控逻辑执行

### 5. 手动运行监控

测试监控功能：

```bash
python3 src/monitor/runner.py
```

如果有规则触发，您将收到 Telegram 消息通知。

## 🤖 GitHub Actions 自动化

### 配置 GitHub Secrets

在 GitHub 仓库中配置以下 Secrets：

1. 进入仓库的 `Settings` → `Secrets and variables` → `Actions`
2. 点击 `New repository secret`
3. 添加以下三个 Secrets：
   - `GEMINI_API_KEY`
   - `TELEGRAM_BOT_TOKEN`
   - `TELEGRAM_CHAT_ID`

### 开启工作流权限

1. 进入 `Settings` → `Actions` → `General`
2. 在 "Workflow permissions" 中选择 `Read and write permissions`
3. 保存更改

### 推送配置文件

将您的监控规则推送到 GitHub：

```bash
git add config/monitor_rules.yaml
git commit -m "chore: 添加股票监控规则"
git push
```

### 自动运行

GitHub Actions 将：
- 在工作日（周一至周五）北京时间 9:30-15:00 每 10 分钟运行一次
- 自动检查所有配置的监控规则
- 触发时通过 Telegram 发送预警
- 保存冷却状态，避免重复推送

## 📂 文件结构

```
stock-analysis-bot/
├── src/
│   ├── strategy/
│   │   └── parser.py          # Gemini AI 策略解析器
│   ├── monitor/
│   │   └── runner.py          # 监控执行核心
│   └── notify/
│       └── telegram.py        # Telegram 推送模块
├── config/
│   ├── monitor_rules.yaml     # 监控规则配置
│   └── signal_cooldown.json   # 冷却状态（自动生成）
├── update_strategy.py         # 策略解析入口
├── test_monitor_system.py     # 系统测试脚本
└── .github/workflows/
    └── stock_monitor.yml      # GitHub Actions 配置
```

## 📝 监控规则格式

`config/monitor_rules.yaml` 示例：

```yaml
- code: sh600460           # 股票代码
  indicator: RSI           # 监控指标
  condition: "<"           # 条件 (>, <, >=, <=, ==)
  threshold: 30            # 阈值
  name: RSI超卖           # 规则名称

- code: HK.00700
  indicator: Close
  condition: ">"
  threshold: MA20          # 也可以是另一个指标
  name: 突破MA20
```

## 🎯 支持的技术指标

从 `github_stock_bot.py` 的 `calculate_technical_indicators` 函数，系统支持：

- **价格指标**: Close, Open, High, Low
- **均线**: MA5, MA10, MA20, MA60, MA250
- **MACD**: DIF, DEA, MACD
- **RSI**: RSI (14周期)
- **布林带**: BB_Upper, BB_Middle, BB_Lower
- **KDJ**: K, D, J
- **威廉指标**: WR
- **成交量**: Volume, Volume_MA5, Volume_MA10, Volume_Ratio
- **其他**: OBV, Amplitude

## 🔧 故障排查

### 1. Gemini API 调用失败
- 检查 `GEMINI_API_KEY` 是否正确
- 确认 API 配额未用尽
- 检查网络连接

### 2. Telegram 推送失败
- 确认 Bot Token 和 Chat ID 正确
- 确保已与 Bot 发起过对话（发送 `/start`）
- 检查网络连接

### 3. 数据获取失败
- 股票代码格式必须正确（如 `sh600460`, `HK.00700`）
- 非交易时段可能无法获取实时数据
- 检查新浪财经 API 是否可访问

### 4. GitHub Actions 不运行
- 确认已正确配置 Secrets
- 检查工作流权限设置
- 查看 Actions 标签页的错误日志

## 💡 最佳实践

1. **规则设置**：不要设置过多规则（建议 5-10 条），避免频繁推送
2. **冷却时间**：建议设置 60 分钟以上，给自己足够的决策时间
3. **定期审查**：每周检查并更新监控规则，删除不再需要的规则
4. **测试优先**：修改配置后先在本地测试，确认无误再推送

## 📞 技术支持

如遇问题，请检查：
1. 测试脚本输出：`python3 test_monitor_system.py`
2. GitHub Actions 日志：仓库的 Actions 标签页
3. 本地日志输出：运行 `python3 src/monitor/runner.py` 查看详细信息

---

🎉 恭喜！您的股票监控助手已经就绪！
