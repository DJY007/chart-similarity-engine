# 🚀 加密货币 K 线模式匹配工具

一个 AI 驱动的加密货币行情分析工具，通过上传 K 线截图，自动识别币种和周期，在历史数据中找到相似走势，并统计后续涨跌概率。

## ✨ 核心功能

### 1. 智能图表识别
- **Claude Vision API** 自动识别 K 线截图中的币种、时间周期、形态特征
- 提取 EMA/MA 指标状态、成交量模式、关键价位等信息
- 生成归一化价格序列用于后续匹配

### 2. 历史模式匹配
- **DTW (Dynamic Time Warping)** 算法在历史数据中寻找相似走势
- **多维度加权相似度**：
  - 价格形态 (50%)
  - EMA 排列 (20%)
  - 成交量模式 (15%)
  - 波动率 (10%)
  - 趋势方向 (5%)
- 自动去重和排序，返回 Top N 匹配结果

### 3. 概率统计分析
- 统计历史相似走势的后续涨跌概率
- 计算平均收益率、最大涨幅、最大回撤
- 根据匹配数量和一致性评估置信度

### 4. 多端接入
- **Web 界面**：现代化 React 应用，支持拖拽上传、实时进度显示、图表对比
- **Telegram Bot**：随时随地发送截图获取预测

## 🏗️ 系统架构

```
用户上传K线截图
       │
       ▼
┌─────────────────────────┐
│  模块1: 图表视觉分析     │  ← Claude Vision API
│  提取: 币种、周期、形态   │
│  EMA状态、关键价位       │
└──────────┬──────────────┘
           │
           ▼
┌─────────────────────────┐
│  模块2: 历史数据管理     │  ← Binance API (ccxt)
│  拉取/缓存历史K线数据    │
│  支持多时间周期           │
└──────────┬──────────────┘
           │
           ▼
┌─────────────────────────┐
│  模块3: 模式匹配引擎     │  ← DTW + 多维相似度
│  滑动窗口扫描历史数据     │
│  多维度加权匹配           │
└──────────┬──────────────┘
           │
           ▼
┌─────────────────────────┐
│  模块4: 结果分析与展示    │
│  Top N 相似走势           │
│  后续走势统计             │
│  可视化对比图表           │
└─────────────────────────┘
```

## 📋 技术栈

### 后端
- **FastAPI** - 高性能 Web 框架
- **Python 3.11+** - 核心语言
- **ccxt** - Binance 数据获取
- **anthropic** - Claude Vision API
- **dtaidistance** - DTW 算法库
- **numpy/scipy** - 数值计算
- **SQLite** - 本地数据缓存

### 前端
- **React 18** - UI 框架
- **Vite** - 构建工具
- **TailwindCSS** - 样式框架
- **Recharts** - 图表库
- **Axios** - HTTP 客户端

### 其他
- **python-telegram-bot** - Telegram 机器人
- **Pillow** - 图片处理

## 🚀 快速开始

### 前置要求
- Python 3.11+
- Node.js 18+
- Anthropic API Key（获取：https://console.anthropic.com）
- Telegram Bot Token（可选）

### 1. 克隆项目
```bash
git clone <repo-url>
cd chart-similarity-engine
```

### 2. 安装依赖
```bash
pip install -r requirements.txt
cd frontend && npm install && cd ..
```

### 3. 配置环境变量
```bash
cp .env.example .env
# 编辑 .env 填入您的 API 密钥
```

### 4. 初始化历史数据
```bash
python scripts/init_data.py
```
这将拉取 BTC/USDT、ETH/USDT、SOL/USDT 在 1h、4h、1d 周期下的历史数据（首次运行需要几分钟）。

### 5. 启动 Web 服务
```bash
# 后端
uvicorn app.main:app --host 0.0.0.0 --port 8000 --reload

# 前端（新终端）
cd frontend && npm run dev
```

### 6. 访问应用
打开浏览器访问 `http://localhost:5173`

### 7. （可选）启动 Telegram Bot
```bash
python -m app.telegram_bot
```

## 📖 使用指南

### Web 界面
1. 打开应用首页
2. 拖拽或点击上传 K 线截图
3. 选择交易对和时间周期（可自动识别）
4. 点击"开始匹配"
5. 查看预测摘要和匹配结果

### Telegram Bot
1. 找到 Bot（@YourBotName）
2. 发送 `/start` 获取欢迎信息
3. 直接发送 K 线截图
4. Bot 自动分析并返回结果
5. 使用 `/set_pair BTC/USDT` 设置默认交易对
6. 使用 `/set_timeframe 4h` 设置默认时间周期

## 📊 API 文档

### POST /api/analyze
上传 K 线截图并获取分析结果

**请求参数：**
- `file` (UploadFile) - K 线截图文件
- `symbol` (str, optional) - 交易对，如 BTC/USDT
- `timeframe` (str, optional) - 时间周期，如 1h/4h/1d
- `top_n` (int, default=10) - 返回前 N 个匹配结果
- `min_similarity` (float, default=0.5) - 最低相似度阈值

**响应格式：**
```json
{
  "chart_analysis": {
    "symbol": "BTC/USDT",
    "timeframe": "4h",
    "pattern": {...},
    "indicators": {...},
    "normalized_price_sequence": [...]
  },
  "matches": [
    {
      "similarity_score": 0.87,
      "start_time": "2023-03-15 10:00",
      "future_return_1x": 0.123,
      "future_trend": "up",
      ...
    }
  ],
  "prediction": {
    "bullish_probability": 0.72,
    "avg_future_return": 0.083,
    "confidence": "high",
    "suggestion": "..."
  }
}
```

### GET /api/health
健康检查

### GET /api/data/status
查看已缓存的历史数据状态

## 🔧 配置说明

编辑 `.env` 文件配置以下参数：

```env
# 必需
ANTHROPIC_API_KEY=sk-ant-xxx          # Claude API 密钥

# 可选
TELEGRAM_BOT_TOKEN=xxx                # Telegram Bot Token
DEFAULT_SYMBOL=BTC/USDT               # 默认交易对
DEFAULT_TIMEFRAME=4h                  # 默认时间周期
DEFAULT_TOP_N=10                      # 默认返回匹配数
DEFAULT_MIN_SIMILARITY=0.5            # 默认最低相似度
```

## 📈 性能优化

### 数据库优化
- 使用 SQLite 本地缓存历史数据
- 建立索引加速查询
- 支持增量同步，避免重复拉取

### 匹配引擎优化
- 采用滑动窗口扫描，支持步长调整
- DTW 距离计算使用 C 扩展（dtaidistance）
- 多维度相似度加权，提高准确性

### 前端优化
- Vite 快速构建和 HMR
- 组件懒加载
- 图表虚拟化渲染

## ⚠️ 免责声明

本工具仅供参考和学习使用，**历史模式不代表未来表现**。

- 加密货币市场高度波动，风险巨大
- 本工具的预测不构成投资建议
- 使用本工具进行交易产生的任何损失，开发者不承担责任
- 请在充分了解风险的基础上谨慎使用

## 🐛 故障排除

### 问题：API 返回 401 错误
**解决方案：** 检查 `.env` 中的 `ANTHROPIC_API_KEY` 是否正确

### 问题：数据拉取失败
**解决方案：** 
- 检查网络连接
- 确保 Binance API 可访问
- 查看日志中的具体错误信息

### 问题：前端无法连接后端
**解决方案：**
- 确保后端服务运行在 `http://localhost:8000`
- 检查防火墙设置
- 查看浏览器控制台中的 CORS 错误

## 📚 项目结构

```
chart-similarity-engine/
├── app/
│   ├── main.py                 # FastAPI 主应用
│   ├── vision_analyzer.py      # Claude Vision 分析
│   ├── data_manager.py         # 历史数据管理
│   ├── pattern_matcher.py      # 匹配引擎
│   ├── result_analyzer.py      # 结果分析
│   ├── telegram_bot.py         # Telegram Bot
│   └── config.py               # 配置管理
├── frontend/                   # React 应用
├── scripts/
│   ├── init_data.py            # 初始化数据
│   └── benchmark.py            # 性能测试
├── data/                       # 数据目录
├── tests/                      # 单元测试
├── requirements.txt            # Python 依赖
├── .env.example                # 环境变量模板
└── README.md                   # 本文件
```

## 🤝 贡献

欢迎提交 Issue 和 Pull Request！

## 📄 许可证

MIT License

## 📞 联系方式

如有问题或建议，请提交 Issue。

---

**最后更新：** 2024 年
**版本：** 1.0.0
