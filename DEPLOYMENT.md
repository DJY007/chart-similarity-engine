# 部署指南

本文档介绍如何在不同环境中部署加密货币 K 线模式匹配工具。

## 📋 前置要求

- Python 3.11+
- Node.js 18+
- Docker & Docker Compose（可选）
- Anthropic API Key
- 足够的磁盘空间（用于存储历史数据）

## 🚀 本地部署

### 1. 克隆项目

```bash
git clone <repository-url>
cd chart-similarity-engine
```

### 2. 创建虚拟环境（推荐）

```bash
python3.11 -m venv venv
source venv/bin/activate  # Linux/Mac
# 或
venv\Scripts\activate  # Windows
```

### 3. 安装依赖

```bash
pip install -r requirements.txt
cd frontend && npm install && cd ..
```

### 4. 配置环境变量

```bash
cp .env.example .env
```

编辑 `.env` 文件，填入您的 API 密钥：

```env
ANTHROPIC_API_KEY=sk-ant-your-key-here
TELEGRAM_BOT_TOKEN=your-telegram-token  # 可选
```

### 5. 初始化数据

```bash
python scripts/init_data.py
```

这将拉取历史数据，首次运行需要几分钟。

### 6. 启动服务

#### 方式1：使用启动脚本

```bash
chmod +x run.sh
./run.sh
```

#### 方式2：手动启动

**终端1 - 后端：**
```bash
uvicorn app.main:app --host 0.0.0.0 --port 8000 --reload
```

**终端2 - 前端：**
```bash
cd frontend
npm run dev
```

**终端3 - Telegram Bot（可选）：**
```bash
python -m app.telegram_bot
```

### 7. 访问应用

- Web 界面：http://localhost:5173
- API 服务：http://localhost:8000
- API 文档：http://localhost:8000/docs

## 🐳 Docker 部署

### 使用 Docker Compose

```bash
docker-compose up -d
```

这将启动：
- FastAPI 后端（端口 8000）
- React 前端（端口 5173）
- SQLite 数据库

### 查看日志

```bash
docker-compose logs -f
```

### 停止服务

```bash
docker-compose down
```

## ☁️ 云部署

### 部署到 Heroku

1. 创建 Heroku 账户并安装 Heroku CLI
2. 创建新应用：
   ```bash
   heroku create your-app-name
   ```
3. 设置环境变量：
   ```bash
   heroku config:set ANTHROPIC_API_KEY=sk-ant-xxx
   ```
4. 部署：
   ```bash
   git push heroku main
   ```

### 部署到 AWS

1. 使用 EC2 实例或 ECS 容器
2. 配置 RDS 或 DynamoDB 用于数据存储（可选）
3. 使用 CloudFront 作为 CDN
4. 配置 Route 53 用于 DNS

### 部署到 Google Cloud

1. 使用 Cloud Run 部署容器
2. 使用 Cloud SQL 存储数据
3. 使用 Cloud Storage 存储大文件

## 🔒 安全建议

### 生产环境配置

1. **环境变量管理**
   - 不要在代码中硬编码 API 密钥
   - 使用密钥管理服务（如 AWS Secrets Manager）
   - 定期轮换密钥

2. **API 安全**
   - 启用 HTTPS
   - 配置 CORS 白名单
   - 实现速率限制
   - 添加 API 密钥认证

3. **数据库安全**
   - 启用数据库加密
   - 定期备份
   - 限制数据库访问权限

4. **前端安全**
   - 启用 CSP（Content Security Policy）
   - 实现 CSRF 保护
   - 定期更新依赖

## 📊 性能优化

### 数据库优化

```sql
-- 创建索引加速查询
CREATE INDEX idx_klines_lookup ON klines(symbol, timeframe, timestamp);
```

### 缓存策略

- 使用 Redis 缓存热数据
- 实现客户端缓存
- 使用 CDN 加速静态资源

### 负载均衡

- 使用 Nginx 进行反向代理
- 配置多个后端实例
- 使用消息队列处理异步任务

## 📈 监控和日志

### 日志配置

```python
import logging

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('app.log'),
        logging.StreamHandler()
    ]
)
```

### 监控指标

- API 响应时间
- 数据库查询性能
- 内存使用率
- CPU 使用率
- 错误率

### 推荐工具

- Prometheus - 指标收集
- Grafana - 可视化
- ELK Stack - 日志分析
- Sentry - 错误追踪

## 🔄 持续集成/部署 (CI/CD)

### GitHub Actions 示例

```yaml
name: Deploy

on:
  push:
    branches: [main]

jobs:
  test:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v2
      - uses: actions/setup-python@v2
        with:
          python-version: 3.11
      - run: pip install -r requirements.txt
      - run: pytest
      - run: npm run build --prefix frontend

  deploy:
    needs: test
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v2
      - run: docker build -t app:latest .
      - run: docker push app:latest
```

## 🆘 故障排除

### 常见问题

1. **API 密钥错误**
   - 检查 `.env` 文件中的密钥
   - 确保密钥有效且未过期

2. **数据库连接失败**
   - 检查数据库路径
   - 确保有写入权限
   - 查看日志获取详细错误

3. **前端无法连接后端**
   - 检查后端是否运行
   - 验证 CORS 配置
   - 检查防火墙设置

详见 [TROUBLESHOOTING.md](TROUBLESHOOTING.md)

## 📞 支持

如有问题，请：
1. 查看 [TROUBLESHOOTING.md](TROUBLESHOOTING.md)
2. 检查项目日志
3. 提交 GitHub Issue
4. 联系开发者

---

**最后更新：** 2024 年
