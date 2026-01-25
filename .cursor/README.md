# Cursor 项目级设置

此目录用于存储项目特定的 Cursor 编辑器设置，可以通过 Git 同步到其他设备。

## 📁 目录说明

- `rules.md` 或 `.cursorrules` - 项目特定的 Cursor 规则
- `settings.json` - 项目特定的编辑器设置（可选）
- 其他项目级配置文件

## 🔄 本地同步说明

此目录已提交到本地 Git 仓库，可以通过以下方式在本地不同电脑间同步：

### 方法一：使用 Git（推荐）
```bash
# 在另一台电脑上
git pull  # 拉取最新更改，包括 .cursor/ 目录
```

### 方法二：手动复制
```bash
# 从源电脑复制 .cursor/ 目录到目标电脑的项目目录
cp -r /path/to/source/.cursor /path/to/target/
```

### 方法三：使用同步脚本
```bash
# 使用项目根目录的 sync_cursor_project.sh 脚本
./sync_cursor_project.sh
```

## 📝 使用建议

1. **项目规则**：可以在此目录创建 `rules.md` 文件，定义项目特定的 AI 助手行为规则
2. **编辑器设置**：可以创建 `settings.json` 覆盖全局设置
3. **Agent 配置**：项目特定的 Agent 配置可以放在这里

## ⚠️ 注意事项

- 不要在此目录存放敏感信息（API Key、密码等）
- 确保设置文件不包含个人隐私信息
- 大型文件建议使用 `.gitignore` 排除
