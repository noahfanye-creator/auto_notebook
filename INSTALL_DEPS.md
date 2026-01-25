# 安装依赖说明

## 主项目（股票分析报告生成器）

### 推荐方式

```bash
cd /path/to/stock-analysis-bot
python -m venv venv
source venv/bin/activate   # macOS/Linux
# venv\Scripts\activate    # Windows

pip install -r requirements-core.txt
pip install -r requirements-optional.txt
```

### 可选：开发与测试

```bash
pip install -r requirements-dev.txt
pytest tests/ -v
```

### 可选：文档生成

```bash
pip install -r requirements-docs.txt
mkdocs serve
```

## 其他子系统

### 监控 / AI 策略解析

若使用监控系统或 AI 策略解析，需额外安装：

```bash
pip install google-generativeai
```

验证（若有对应脚本）：

```bash
python test_monitor_system.py
```

### SSL 或网络问题

- 使用国内镜像：`pip install -i https://mirrors.aliyun.com/pypi/simple/ -r requirements-core.txt`
- 跳过证书验证：`pip install --trusted-host pypi.org --trusted-host files.pythonhosted.org -r requirements-core.txt`

## 参考

- [DEPENDENCIES.md](docs/DEPENDENCIES.md)：依赖分类与说明
