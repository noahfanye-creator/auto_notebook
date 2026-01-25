# 依赖管理文档

## 依赖分类

本项目将依赖分为三类，便于按需安装和管理：

### 1. 核心依赖 (`requirements-core.txt`)

运行程序必需的基础依赖，包括：

- **数据处理**: pandas, numpy
- **数据获取**: requests
- **数据可视化**: matplotlib, seaborn
- **PDF生成**: reportlab, Pillow
- **配置管理**: PyYAML
- **日志**: loguru

**安装方式：**
```bash
pip install -r requirements-core.txt
```

### 2. 可选依赖 (`requirements-optional.txt`)

增强功能的依赖，可根据需要选择安装：

- **数据源备选**: yfinance, akshare（用于备选数据获取）
- **环境变量管理**: python-dotenv
- **AI策略解析**: google-generativeai

**安装方式：**
```bash
pip install -r requirements-optional.txt
```

**说明：**
- `yfinance`: 用于某些数据源的备选方案
- `akshare`: 港股数据备选数据源，也用于交易日判断
- `python-dotenv`: 用于从`.env`文件加载环境变量（可选）
- `google-generativeai`: 用于AI策略解析功能（可选）

### 3. 开发依赖 (`requirements-dev.txt`)

仅用于开发和测试的依赖：

- **测试框架**: pytest, pytest-cov

**安装方式：**
```bash
pip install -r requirements-dev.txt
```

## 版本管理

所有依赖的版本号已固定，确保：
- ✅ 环境一致性
- ✅ 可重现的构建
- ✅ 避免意外升级导致的兼容性问题

## 安装建议

### 生产环境
```bash
# 仅安装核心依赖
pip install -r requirements-core.txt

# 如需可选功能，再安装可选依赖
pip install -r requirements-optional.txt
```

### 开发环境
```bash
# 安装所有依赖
pip install -r requirements-core.txt -r requirements-optional.txt -r requirements-dev.txt
```

### 快速开始（推荐）
```bash
# 安装核心 + 可选依赖（覆盖大部分使用场景）
pip install -r requirements-core.txt -r requirements-optional.txt
```

## 依赖更新

更新依赖版本时：
1. 在对应分类文件中更新版本号
2. 测试确保兼容性
3. 更新本文档说明

## 常见问题

### Q: 为什么拆分依赖文件？
A: 便于按需安装，减少不必要的依赖，提高安装速度和环境清洁度。

### Q: 不安装可选依赖会怎样？
A: 核心功能不受影响，但某些增强功能可能不可用：
- 不安装`akshare`: 港股交易日判断可能不可用（会使用默认值）
- 不安装`yfinance`: 某些数据源备选方案不可用
- 不安装`google-generativeai`: AI策略解析功能不可用

### Q: 如何检查已安装的依赖？
```bash
pip list
```

### Q: 如何更新依赖？
```bash
# 更新所有依赖到最新版本（不推荐，可能破坏兼容性）
pip install --upgrade -r requirements-core.txt -r requirements-optional.txt

# 更新特定包
pip install --upgrade pandas
```

## 依赖关系图

```
核心依赖 (requirements-core.txt)
├── pandas, numpy (数据处理)
├── requests (数据获取)
├── matplotlib, seaborn (可视化)
├── reportlab, Pillow (PDF生成)
├── PyYAML (配置管理)
└── loguru (日志)

可选依赖 (requirements-optional.txt)
├── yfinance (数据源备选)
├── akshare (数据源备选 + 交易日判断)
├── python-dotenv (环境变量)
└── google-generativeai (AI功能)

开发依赖 (requirements-dev.txt)
└── pytest, pytest-cov (测试)
```

## pyproject.toml

项目根目录提供 `pyproject.toml`，用于：

- **\[project]**：包元数据、`requires-python`
- **\[tool.pytest.ini_options]**：pytest 配置
- **\[tool.coverage.\*]**：覆盖率配置
- **\[tool.black]**、**\[tool.mypy]**：代码质量工具配置

安装与测试仍以 `requirements-*.txt` 为主。若希望锁版本或更严格依赖管理，可选用 **pip-tools**（`pip-compile`）或 **Poetry**，将 `requirements-*.txt` 或 `pyproject.toml` 作为源。
