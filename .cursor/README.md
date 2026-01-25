# Cursor 项目级设置

此目录用于存储项目特定的 Cursor 编辑器设置，可以通过 Git 同步到其他设备。

## 📁 目录说明

- `rules.md` 或 `.cursorrules` - 项目特定的 Cursor 规则
- `settings.json` - 项目特定的编辑器设置（可选）
- 其他项目级配置文件

## 🔄 同步说明

### ✅ 自动同步（如果项目目录已同步）

**如果你的项目目录已经通过文件同步服务（iCloud、Dropbox、OneDrive、rsync 等）在两台电脑间同步，那么 `.cursor/` 目录会自动同步！**

这意味着：
- ✅ 项目级 Cursor 设置会自动同步
- ✅ 项目规则文件会自动同步
- ✅ 项目特定的编辑器设置会自动同步

**无需额外操作**，只需确保项目目录同步正常即可。

### 📝 其他同步方式（如果项目目录未同步）

如果项目目录没有自动同步，可以使用以下方式：

#### 方法一：使用 Git
```bash
# 在另一台电脑上
git pull  # 拉取最新更改，包括 .cursor/ 目录
```

#### 方法二：手动复制
```bash
# 从源电脑复制 .cursor/ 目录到目标电脑的项目目录
cp -r /path/to/source/.cursor /path/to/target/
```

#### 方法三：使用同步脚本
```bash
# 使用项目根目录的 sync_cursor_project.sh 脚本
./sync_cursor_project.sh
```

### ⚠️ 重要提示：Agent 配置需要单独同步

**项目级设置**（`.cursor/` 目录）会随项目文件自动同步 ✅

**但是，Agent 配置和对话历史**存储在 `~/.cursor/projects/` 中，**不会自动同步**，需要手动处理：

```bash
# 使用同步脚本备份 Agent 配置
./sync_cursor_project.sh

# 然后在另一台电脑上恢复
# 根据实际项目路径调整目录名
cp -r ~/cursor-backup/Users-felix-Documents-stock-analysis-bot \
     ~/.cursor/projects/<目标项目路径>/
```

详细说明请参考项目根目录的 `CURSOR_SYNC_GUIDE.md`。

## 📝 使用建议

1. **项目规则**：可以在此目录创建 `rules.md` 文件，定义项目特定的 AI 助手行为规则
2. **编辑器设置**：可以创建 `settings.json` 覆盖全局设置
3. **Agent 配置**：项目特定的 Agent 配置可以放在这里

## ⚠️ 注意事项

- 不要在此目录存放敏感信息（API Key、密码等）
- 确保设置文件不包含个人隐私信息
- 大型文件建议使用 `.gitignore` 排除
