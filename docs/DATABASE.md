# 本地数据库（积累 + 复用）

## 功能

- **积累**：查过的 A 股 K 线（日/30m/5m/1m）按 `(code, scale)` 写入 SQLite。
- **复用**：每次拉数前先读库；若条数够（≥ `datalen * 0.8`）且够新（日线最新距现在 ≤2 天，分钟线 ≤1 小时），直接返回库数据，**不请求接口**。
- **回写**：接口拉取成功后，将新数据写入库，供后续复用。

仅 **A 股**（`sh*` / `sz*`）走数据库；港股仍仅用缓存与接口。**GitHub Actions 不接入**；每次 run 环境重置，无法跨次积累。

## 配置

`config/config.yaml`：

```yaml
database:
  enabled: true
  path: "data/stock_data.db"
```

- `enabled`: 是否启用本地 DB；`false` 时只用缓存与接口。
- `path`: SQLite 文件路径；目录不存在时会自动创建。

## 依赖

无额外依赖；使用标准库 `sqlite3`。

## 存储

- 表 `kline_by_scale`：`(code, scale, date)` 为主键，逐条 `INSERT OR REPLACE`，避免重复。
- `data/` 已在 `.gitignore` 中，`stock_data.db` 不会入库。
