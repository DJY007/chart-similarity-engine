# Railway 部署指南

本指南将帮助您在 Railway 平台上部署 Chart Similarity Engine。

## 前置条件

- GitHub 账户（DJY007）
- Railway 账户（https://railway.app）
- DeepSeek API Key：`sk-f843f0f7297a4f5ab60c4e4c59d98149`
- Telegram Bot Token：`8723720710:AAHHYHQa8VqhXh7FpE8OBjs1IwJP4EDbiSc`

## 部署步骤

### 方式1：通过 Railway Web UI（推荐）

#### 第1步：将代码推送到 GitHub

```bash
# 在您的本地机器上执行
cd /path/to/chart-similarity-engine

# 创建 GitHub 仓库
git remote add origin https://github.com/DJY007/chart-similarity-engine.git
git branch -M main
git push -u origin main
```

#### 第2步：在 Railway 上创建项目

1. 访问 https://railway.app
2. 登录您的账户
3. 点击 "New Project" → "Deploy from GitHub"
4. 授权 Railway 访问您的 GitHub 账户
5. 选择 `chart-similarity-engine` 仓库
6. 选择 `main` 分支

#### 第3步：配置环境变量

在 Railway 项目中，进入 "Variables" 标签，添加以下环境变量：

```
DEEPSEEK_API_KEY=sk-f843f0f7297a4f5ab60c4e4c59d98149
TELEGRAM_BOT_TOKEN=8723720710:AAHHYHQa8VqhXh7FpE8OBjs1IwJP4EDbiSc
ENVIRONMENT=production
DEBUG=false
LOG_LEVEL=INFO
API_HOST=0.0.0.0
API_PORT=8000
```

#### 第4步：配置构建和部署

1. 进入 "Settings" 标签
2. 在 "Build" 部分：
   - Dockerfile：`Dockerfile.backend`
   - Build Context：`.`
3. 在 "Deploy" 部分：
   - Start Command：`uvicorn app.main:app --host 0.0.0.0 --port $PORT`
   - Restart Policy：Enable

#### 第5步：部署

1. Railway 会自动开始构建和部署
2. 等待部署完成（通常需要 5-10 分钟）
3. 部署完成后，您将获得一个公网 URL，如：`https://chart-similarity-engine-production.up.railway.app`

### 方式2：使用 Railway CLI

#### 第1步：安装 Railway CLI

```bash
npm install -g @railway/cli
```

#### 第2步：登录 Railway

```bash
railway login
```

#### 第3步：初始化项目

```bash
cd /path/to/chart-similarity-engine
railway init
```

#### 第4步：配置环境变量

```bash
railway variables set DEEPSEEK_API_KEY=sk-f843f0f7297a4f5ab60c4e4c59d98149
railway variables set TELEGRAM_BOT_TOKEN=8723720710:AAHHYHQa8VqhXh7FpE8OBjs1IwJP4EDbiSc
railway variables set ENVIRONMENT=production
railway variables set DEBUG=false
```

#### 第5步：部署

```bash
railway up
```

## 验证部署

部署完成后，验证应用是否正常运行：

```bash
# 检查健康状态
curl https://your-railway-url/api/health

# 应该返回：
# {"status":"ok","environment":"production","debug":false}
```

## 配置 Telegram Bot

部署完成后，Telegram Bot 会自动启动。您可以通过以下方式测试：

1. 在 Telegram 中搜索您的 Bot（使用 Bot Token 中的 ID）
2. 发送 `/start` 命令
3. Bot 会显示欢迎信息和可用命令

## 常见问题

### 问题1：部署失败

**原因**：通常是因为 Python 依赖安装失败或 Docker 构建错误。

**解决方案**：
1. 检查 Railway 的构建日志
2. 确保 `requirements.txt` 中的所有依赖都是兼容的
3. 尝试在本地构建 Docker 镜像进行测试

### 问题2：API 调用超时

**原因**：DeepSeek API 响应缓慢或网络连接问题。

**解决方案**：
1. 增加 `DEEPSEEK_TIMEOUT` 值（默认 60 秒）
2. 检查 DeepSeek API 的状态
3. 检查网络连接

### 问题3：数据库错误

**原因**：SQLite 数据库文件权限问题或磁盘空间不足。

**解决方案**：
1. 确保 `data/` 目录有写入权限
2. 检查 Railway 的磁盘空间
3. 清除旧的数据库文件

## 监控和日志

在 Railway 上，您可以：

1. **查看日志**：进入项目 → "Logs" 标签
2. **监控资源**：进入项目 → "Metrics" 标签
3. **设置告警**：进入项目 → "Alerts" 标签

## 更新部署

当您更新代码时：

1. 推送到 GitHub：`git push origin main`
2. Railway 会自动检测更新并重新部署
3. 部署过程通常需要 5-10 分钟

## 回滚部署

如果需要回滚到之前的版本：

1. 进入 Railway 项目
2. 进入 "Deployments" 标签
3. 选择之前的部署版本
4. 点击 "Redeploy"

## 性能优化建议

1. **增加内存**：在 Railway 的 "Settings" 中增加 RAM 分配
2. **启用缓存**：配置 Redis 缓存（可选）
3. **优化数据库**：定期清理旧的历史数据
4. **监控 API 调用**：使用 DeepSeek 的 API 监控工具

## 支持

如有问题，请参考：

- Railway 文档：https://docs.railway.app
- DeepSeek 文档：https://platform.deepseek.com/docs
- Telegram Bot 文档：https://core.telegram.org/bots/api

---

**部署完成！** 🚀

您的应用现在已在 Railway 上运行，可以通过公网 URL 访问。
