# 测试文档

## 测试结构

```
tests/
├── __init__.py
├── conftest.py              # pytest配置和共享fixtures
├── utils/
│   ├── test_code_normalizer.py    # 代码标准化测试
│   ├── test_trading_hours.py      # 交易时间判断测试
│   ├── test_cache.py              # 缓存模块测试
│   └── test_parallel.py           # 并发处理测试
├── data/
│   └── test_data_fetchers.py      # 数据获取函数测试（使用mock）
└── analysis/
    └── test_indicators.py         # 技术指标计算测试
```

## 运行测试

### 运行所有测试
```bash
pytest tests/ -v
```

### 运行特定测试文件
```bash
pytest tests/utils/test_code_normalizer.py -v
pytest tests/analysis/test_indicators.py -v
```

### 运行特定测试类
```bash
pytest tests/utils/test_code_normalizer.py::TestCodeNormalizer -v
```

### 运行特定测试方法
```bash
pytest tests/utils/test_code_normalizer.py::TestCodeNormalizer::test_normalize_a_share_code_sh -v
```

## 测试覆盖率

当前测试覆盖：
- ✅ 工具函数模块（code_normalizer, trading_hours, cache, parallel）
- ✅ 技术指标计算模块（indicators）
- ✅ 数据获取函数（使用mock）

## 测试统计

- 总测试数：35
- 通过率：100%
- 测试文件：6个

## 测试内容

### 1. 代码标准化测试 (`test_code_normalizer.py`)
- A股代码标准化（上海/深圳）
- 港股代码标准化
- 港股识别
- 股票列表解析

### 2. 交易时间判断测试 (`test_trading_hours.py`)
- A股市场交易日判断
- 港股市场交易日判断
- 周末休市判断

### 3. 缓存模块测试 (`test_cache.py`)
- 缓存保存和读取
- 缓存键生成
- TTL过期功能
- 缓存删除
- 缓存统计
- 单例模式

### 4. 并发处理测试 (`test_parallel.py`)
- 基础并发处理
- 错误处理
- 分批并发处理
- 并发映射
- 线程安全计数器

### 5. 技术指标计算测试 (`test_indicators.py`)
- 综合技术指标计算
- 移动平均线（MA）
- RSI计算
- MACD计算
- KDJ计算
- K线数据重采样

### 6. 数据获取函数测试 (`test_data_fetchers.py`)
- 股票名称获取（使用mock）
- K线数据获取（使用mock）
- 时区标准化
- 交易时间过滤

## 注意事项

1. **Mock使用**：数据获取函数测试使用mock避免实际网络请求
2. **并发测试**：并发处理的结果顺序可能不同，测试时需要注意
3. **时间相关测试**：交易时间判断测试需要mock datetime和akshare
4. **缓存测试**：使用临时目录避免污染实际缓存

## 添加新测试

1. 在对应的测试目录创建测试文件
2. 使用pytest的fixture和mock功能
3. 确保测试独立，不依赖外部资源
4. 运行测试确保通过
