# 🚀 Stock Analysis Bot (股票分析机器人)

一个功能强大的股票分析工具，支持数据获取、技术分析、信号预警和可视化。

## ✨ 核心功能
- 📊 **多数据源支持**: yfinance、AKShare、Sina/东方财富（港股）
- 📈 **技术分析**: 30+ 技术指标计算
- 🔔 **智能预警**: RSI超买超卖、价格突破等
- 📊 **数据可视化**: K线图、指标图表、仪表板
- ⚡ **高性能**: 异步处理、数据缓存
- 📱 **多格式输出**: PDF报告、Excel、图表图片
- 🇭🇰 **港股支持**: 使用免费数据源获取港股数据并生成报告
- 🎯 **每日复盘**: 自动抓取热门板块和股票，生成短线交易清单

## 🛠 技术栈
- **语言**: Python 3.8+
- **主程序**: `github_stock_bot.py`，配置 `config/config.yaml`
- **数据处理**: Pandas, NumPy
- **数据源**: 新浪财经、东方财富、AKShare、yfinance（港股等）
- **技术分析**: 自研指标模块（MA、MACD、RSI、KDJ、布林带等）
- **可视化**: Matplotlib、ReportLab（PDF）
- **依赖管理**: `requirements-core.txt`、`requirements-optional.txt`、`requirements-dev.txt`
- **数据库**: 可选 `src/database`（SQLite 历史 K 线）

## 🚦 快速开始

### 1. 克隆项目
```bash
git clone git@github.com:noahfanye-creator/stock-analysis-bot.git
cd stock-analysis-bot
```

### 2. 创建虚拟环境
```bash
python -m venv venv
source venv/bin/activate  # macOS/Linux
# venv\Scripts\activate   # Windows
```

### 3. 安装依赖

#### 方式一：安装核心依赖（推荐）
```bash
# 仅安装核心依赖（必需）
pip install -r requirements-core.txt
```

#### 方式二：安装所有依赖（包括可选功能）
```bash
# 安装核心依赖 + 可选依赖
pip install -r requirements-core.txt -r requirements-optional.txt
```

#### 方式三：向后兼容（使用原requirements.txt）
```bash
# 安装所有依赖（包括开发工具）
pip install -r requirements.txt
```

**依赖说明：**
- **核心依赖** (`requirements-core.txt`): 运行程序必需，包括数据处理、可视化、PDF生成等
- **可选依赖** (`requirements-optional.txt`): 增强功能，如备选数据源、AI策略解析等
- **开发依赖** (`requirements-dev.txt`): 仅用于开发和测试，如pytest等

### 4. 配置
```bash
cp config/config.example.yaml config/config.yaml
# 按需编辑 config.yaml（股票列表、指标参数、报告目录等）
```
港股使用免费数据源，无需 API 配置。

### 5. 运行主程序

#### A股分析
```bash
python github_stock_bot.py --mode manual --stocks "600460 300474"
```

#### 港股分析
```bash
python github_stock_bot.py --mode manual --stocks "00700 03690"
```

#### 混合分析（A股+港股）
```bash
python github_stock_bot.py --mode manual --stocks "600460 00700 300474"
```

#### 每日复盘（可选）
```bash
./run_daily_review.sh
# 或 python3 daily_review.py
```
详见 [DAILY_REVIEW_README.md](DAILY_REVIEW_README.md)。

## 📁 项目结构
```
stock-analysis-bot/
├── github_stock_bot.py    # 主程序入口
├── config/
│   ├── config.yaml        # 主配置（股票列表、指标、报告目录等）
│   └── config.example.yaml
├── src/
│   ├── data/              # 数据获取（A股/港股/行业）
│   ├── analysis/          # 技术指标、市场分析
│   ├── visualization/     # 图表、PDF 报告
│   ├── report/            # 报告生成流程
│   ├── config/            # 配置加载
│   ├── utils/             # 工具、日志、缓存、异常
│   ├── database/          # 可选 SQLite 存储
│   └── notify/            # 通知（如 Telegram）
├── tests/                 # 单元测试与集成测试
├── docs/                  # 文档与 API（MkDocs）
├── examples/              # 使用示例
├── requirements-core.txt  # 核心依赖
├── requirements-optional.txt
├── requirements-dev.txt   # 开发与测试
└── .github/workflows/     # CI（stock_bot、code-quality 等）
```

## 📖 港股功能说明

### 支持的港股代码格式
- `00700` - 5位数字（自动识别为港股）
- `00700.HK` - 带.HK后缀
- `HK.00700` - 带HK.前缀

### 功能特性
- ✅ 自动识别港股代码
- ✅ 免费数据源获取实时与历史数据
- ✅ 多周期 K 线（日/周/月/30 分钟/5 分钟/1 分钟）
- ✅ 技术指标计算与 PDF 报告
- ✅ Telegram 通知（可选）

港股不需要额外配置即可使用。

## 🔧 GitHub Actions

- **stock_bot.yml**：定时/手动运行分析，生成报告 ZIP，Telegram 推送，自动上传 Google Drive。
  - **Google Drive 配置 (OAuth)**：由于服务账号配额限制，现已切换至 OAuth 认证。请运行 `auth_tool.py` 获取 `GDRIVE_CLIENT_ID`, `GDRIVE_CLIENT_SECRET`, `GDRIVE_REFRESH_TOKEN` 并配置到 GitHub Secrets。
- **code-quality.yml**：PR/push 时 black、flake8、mypy、pytest 与覆盖率检查

## 📝 许可证

MIT License

## 🤝 贡献

欢迎提交Issue和Pull Request！

## 📞 支持

如有问题，请查看：
- GitHub Issues
