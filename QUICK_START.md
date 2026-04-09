# 🚀 快速开始指南

## ⏱️ 5 分钟快速部署

### 前置要求

- Python 3.11+
- Node.js 18+
- Anthropic API Key

### 第 1 步：克隆项目

```bash
git clone <repository-url>
cd chart-similarity-engine
```

### 第 2 步：配置环境

```bash
cp .env.example .env
```

编辑 `.env` 文件，填入您的 API 密钥：

```env
ANTHROPIC_API_KEY=sk-ant-your-key-here
```

### 第 3 步：一键启动

```bash
chmod +x run.sh
./run.sh
```

### 第 4 步：访问应用

打开浏览器访问：**http://localhost:5173**

## 📸 使用步骤

### 1. 上传 K 线截图

- 拖拽或点击上传 JPG/PNG 格式的 K 线图
- 或按 Ctrl+V 粘贴截图

### 2. 等待分析

系统会分步显示进度：
- ⏳ 正在分析图表…
- ⏳ 正在检索历史数据…
- ⏳ 正在匹配模式…
- ✅ 完成

### 3. 查看结果

**预测摘要**
- 📈 上涨概率
- 💰 平均收益
- 🎯 置信度

**匹配列表**
- 相似度排名
- 历史时间区间
- 后续涨跌幅

**收益分布**
- 历史相似走势的收益率分布

## 🤖 Telegram Bot 使用

### 1. 获取 Bot Token

在 Telegram 上与 @BotFather 交互，创建新机器人

### 2. 配置 Token

编辑 `.env` 文件：

```env
TELEGRAM_BOT_TOKEN=your-token-here
```

### 3. 启动 Bot

```bash
python -m app.telegram_bot
```

### 4. 使用 Bot

在 Telegram 中：
1. 找到您的机器人
2. 发送 `/start` 查看帮助
3. 发送 K 线截图
4. 机器人会自动分析并返回结果

**Bot 命令**
- `/start` - 开始
- `/help` - 帮助
- `/set_pair BTC/USDT` - 设置交易对
- `/set_timeframe 4h` - 设置时间周期

## 🐳 Docker 快速部署

### 一键启动

```bash
docker-compose up -d
```

### 查看日志

```bash
docker-compose logs -f
```

### 停止服务

```bash
docker-compose down
```

## 🧪 运行测试

```bash
# 安装测试依赖
pip install pytest pytest-cov

# 运行所有测试
pytest tests/ -v

# 运行特定测试
pytest tests/test_pattern_matcher.py -v

# 生成覆盖率报告
pytest tests/ --cov=app --cov-report=html
```

## 📊 初始化数据

首次运行时需要初始化历史数据：

```bash
python scripts/init_data.py
```

这将拉取以下交易对的历史数据：
- BTC/USDT (1h, 4h, 1d)
- ETH/USDT (1h, 4h, 1d)

**预计耗时：** 5-10 分钟

## 🔍 API 测试

### 使用 curl

```bash
# 上传图片进行分析
curl -X POST http://localhost:8000/api/analyze \
  -F "file=@chart.png" \
  -F "symbol=BTC/USDT" \
  -F "timeframe=4h"

# 检查健康状态
curl http://localhost:8000/api/health

# 查看数据状态
curl http://localhost:8000/api/data/status
```

### 使用 Python

```python
import requests

# 上传图片
with open('chart.png', 'rb') as f:
    files = {'file': f}
    data = {
        'symbol': 'BTC/USDT',
        'timeframe': '4h',
        'top_n': 10,
        'min_similarity': 0.5
    }
    response = requests.post(
        'http://localhost:8000/api/analyze',
        files=files,
        data=data
    )
    result = response.json()
    print(result)
```

## 📁 项目结构速览

```
chart-similarity-engine/
├── app/                    # 后端代码
├── frontend/               # 前端代码
├── scripts/                # 工具脚本
├── tests/                  # 测试代码
├── data/                   # 数据目录
├── .env.example            # 环境变量模板
├── requirements.txt        # Python 依赖
├── run.sh                  # 启动脚本
└── README.md               # 详细文档
```

## 🆘 常见问题

### Q: 无法连接 Binance API

**A:** 检查网络连接，或尝试使用代理

```python
# 在 data_manager.py 中配置代理
self.exchange = ccxt.binance({
    'proxies': {
        'http': 'http://proxy.example.com:8080',
        'https': 'http://proxy.example.com:8080',
    }
})
```

### Q: Claude Vision API 超时

**A:** 增加超时时间或重试

```python
# 在 vision_analyzer.py 中配置
self.client = anthropic.Anthropic(
    api_key=api_key,
    timeout=60.0  # 增加到 60 秒
)
```

### Q: 数据库文件过大

**A:** 清理旧数据

```bash
sqlite3 data/klines.db "DELETE FROM klines WHERE timestamp < $(date -d '1 year ago' +%s)000;"
sqlite3 data/klines.db "VACUUM;"
```

### Q: 前端无法加载

**A:** 检查前端依赖

```bash
cd frontend
npm install
npm run dev
```

## 📚 下一步

1. **阅读详细文档**
   - [README.md](README.md) - 完整项目文档
   - [ARCHITECTURE.md](ARCHITECTURE.md) - 系统架构
   - [DEPLOYMENT.md](DEPLOYMENT.md) - 部署指南

2. **自定义配置**
   - 添加更多交易对
   - 调整匹配参数
   - 优化性能

3. **扩展功能**
   - 集成更多数据源
   - 添加新的相似度维度
   - 实现用户认证

## 💡 提示

- 📌 首次运行会花费较长时间初始化数据，请耐心等待
- 🔑 保管好您的 API 密钥，不要提交到版本控制
- 📊 定期备份数据库文件
- 🚀 在生产环境中使用 HTTPS
- 🔒 配置防火墙限制 API 访问

## 📞 获取帮助

- 📖 查看 [TROUBLESHOOTING.md](TROUBLESHOOTING.md)
- 🐛 提交 GitHub Issue
- 💬 加入社区讨论
- 📧 联系开发者

---

**祝您使用愉快！** 🎉

如有任何问题，欢迎反馈。
