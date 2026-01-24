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

## 🛠 技术栈
- **语言**: Python 3.8+
- **数据处理**: Pandas, NumPy
- **数据源**: yfinance, AKShare, 新浪财经/东方财富（港股）
- **技术分析**: TA-Lib, ta
- **可视化**: Matplotlib, Plotly, Seaborn
- **Web框架**: FastAPI (REST API)
- **调度任务**: APScheduler
- **数据库**: SQLite / PostgreSQL (可选)

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
```bash
pip install -r requirements.txt
```

### 4. 运行示例
```bash
python examples/basic_analysis.py
```

### 5. 配置设置

#### A股配置
```bash
cp config/config.example.yaml config/config.yaml
# 编辑 config.yaml 文件
```

#### 港股配置（可选）
港股使用免费数据源，无需额外API配置。

### 6. 使用示例

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

## 📁 项目结构
```
stock-analysis-bot/
├── src/                    # 源代码
│   ├── data/              # 数据获取模块
│   │   └── hk_data_sources.py # 港股数据源
│   ├── analysis/          # 技术分析模块
│   ├── visualization/     # 数据可视化
│   ├── notify/            # 通知提醒模块
│   └── utils/             # 工具函数
├── tests/                 # 单元测试
├── docs/                  # 项目文档
│   └── (已移除港股API配置文档)
├── examples/              # 使用示例
├── config/                # 配置文件
├── scripts/               # 脚本文件
├── logs/                  # 日志文件
├── requirements.txt       # Python依赖
├── .gitignore            # Git忽略文件
└── README.md             # 项目说明
```

## 📖 港股功能说明

### 支持的港股代码格式
- `00700` - 5位数字（自动识别为港股）
- `00700.HK` - 带.HK后缀
- `HK.00700` - 带HK.前缀

### 功能特性
- ✅ 自动识别港股代码
- ✅ 使用免费数据源获取实时和历史数据
- ✅ 支持多周期K线（日/周/月/30分钟/5分钟/1分钟）
- ✅ 自动计算技术指标
- ✅ 生成PDF报告
- ✅ 自动上传到Google Drive
- ✅ Telegram通知

港股不需要额外配置即可使用。

## 🔧 GitHub Actions 自动化

项目已配置GitHub Actions，支持：
- 定时任务（工作日自动分析）
- 手动触发
- 自动生成报告
- 上传到Google Drive
- Telegram通知

## 📝 许可证

MIT License

## 🤝 贡献

欢迎提交Issue和Pull Request！

## 📞 支持

如有问题，请查看：
- GitHub Issues
