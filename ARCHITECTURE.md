# 系统架构详解

## 📐 整体架构

```
┌─────────────────────────────────────────────────────────────┐
│                       用户交互层                              │
│  ┌──────────────────┐              ┌──────────────────┐    │
│  │   Web 界面       │              │  Telegram Bot    │    │
│  │  (React App)     │              │  (python-tg)     │    │
│  └────────┬─────────┘              └────────┬─────────┘    │
└───────────┼──────────────────────────────────┼──────────────┘
            │                                  │
            └──────────────┬───────────────────┘
                           │
┌──────────────────────────▼──────────────────────────────────┐
│                      API 层 (FastAPI)                        │
│  ┌─────────────────────────────────────────────────────┐   │
│  │  POST /api/analyze                                  │   │
│  │  GET /api/health                                    │   │
│  │  GET /api/data/status                              │   │
│  └─────────────────────────────────────────────────────┘   │
└──────────────────────────┬───────────────────────────────────┘
                           │
┌──────────────────────────▼──────────────────────────────────┐
│                    业务逻辑层                                 │
│  ┌──────────────────────────────────────────────────────┐  │
│  │  1. ChartVisionAnalyzer                              │  │
│  │     - Claude Vision API 调用                         │  │
│  │     - JSON 解析与验证                                │  │
│  │     - 特征提取                                       │  │
│  └──────────────────────────────────────────────────────┘  │
│  ┌──────────────────────────────────────────────────────┐  │
│  │  2. HistoricalDataManager                            │  │
│  │     - Binance API 数据拉取                           │  │
│  │     - SQLite 数据库操作                              │  │
│  │     - 增量同步逻辑                                   │  │
│  └──────────────────────────────────────────────────────┘  │
│  ┌──────────────────────────────────────────────────────┐  │
│  │  3. PatternMatcher                                   │  │
│  │     - DTW 算法实现                                   │  │
│  │     - 多维度相似度计算                               │  │
│  │     - 性能优化（皮尔逊过滤、降采样）                 │  │
│  └──────────────────────────────────────────────────────┘  │
│  ┌──────────────────────────────────────────────────────┐  │
│  │  4. ResultAnalyzer                                   │  │
│  │     - 统计分析                                       │  │
│  │     - 置信度评估                                     │  │
│  │     - 建议生成                                       │  │
│  └──────────────────────────────────────────────────────┘  │
└──────────────────────────┬───────────────────────────────────┘
                           │
┌──────────────────────────▼──────────────────────────────────┐
│                    数据层                                     │
│  ┌──────────────────┐              ┌──────────────────┐    │
│  │   SQLite DB      │              │  Binance API     │    │
│  │  (klines.db)     │              │  (CCXT)          │    │
│  └──────────────────┘              └──────────────────┘    │
└─────────────────────────────────────────────────────────────┘
```

## 🔄 数据流

### 用户上传图片的完整流程

```
1. 用户上传图片
   │
   ├─► Web 前端接收
   │   ├─ 验证文件格式
   │   ├─ 显示进度条
   │   └─ 发送 POST /api/analyze
   │
   ├─► FastAPI 后端接收
   │   ├─ 保存临时文件
   │   └─ 调用业务逻辑
   │
   ├─► ChartVisionAnalyzer
   │   ├─ 图片转 Base64
   │   ├─ 调用 Claude Vision API
   │   ├─ 解析 JSON 响应
   │   └─ 返回结构化特征
   │       {
   │         "symbol": "BTC/USDT",
   │         "timeframe": "4h",
   │         "normalized_price_sequence": [0.1, 0.2, ...],
   │         "indicators": {...}
   │       }
   │
   ├─► HistoricalDataManager
   │   ├─ 检查本地缓存
   │   ├─ 从 Binance 拉取新数据
   │   ├─ 存储到 SQLite
   │   └─ 返回历史 OHLCV 数据
   │
   ├─► PatternMatcher
   │   ├─ 皮尔逊相关系数预过滤
   │   ├─ 滑动窗口扫描
   │   ├─ 计算多维度相似度
   │   │   ├─ 价格形态 (DTW)
   │   │   ├─ EMA 排列
   │   │   ├─ 成交量模式
   │   │   ├─ 波动率
   │   │   └─ 趋势方向
   │   ├─ 去重叠处理
   │   └─ 返回 Top N 匹配
   │
   ├─► ResultAnalyzer
   │   ├─ 统计涨跌比例
   │   ├─ 计算平均收益
   │   ├─ 评估置信度
   │   └─ 生成建议
   │
   └─► 返回结果给前端
       ├─ 图表分析结果
       ├─ 匹配列表
       ├─ 预测摘要
       └─ 前端渲染展示
```

## 📊 数据模型

### ChartAnalysis (Vision 分析结果)

```python
{
    "symbol": str,                          # 交易对
    "timeframe": str,                       # 时间周期
    "candle_count": int,                    # K线数量
    "pattern": {
        "trend": str,                       # 整体趋势
        "recent_trend": str,                # 最近趋势
        "volatility": str,                  # 波动性
        "key_patterns": List[str]           # 关键形态
    },
    "indicators": {
        "ema_arrangement": str,             # EMA排列
        "ema_cross_signal": str,            # EMA交叉
        "price_vs_ema": str,                # 价格vs EMA
        "volume_pattern": str               # 成交量模式
    },
    "price_structure": {
        "recent_high_position": float,      # 高点位置
        "recent_low_position": float,       # 低点位置
        "price_range_percent": float,       # 波动幅度
        "current_position_in_range": float  # 当前位置
    },
    "normalized_price_sequence": List[float], # 归一化价格序列
    "confidence": int                       # 置信度 (0-100)
}
```

### MatchResult (匹配结果)

```python
@dataclass
class MatchResult:
    start_index: int                    # 起始索引
    end_index: int                      # 结束索引
    start_time: str                     # 开始时间
    end_time: str                       # 结束时间
    similarity_score: float             # 综合相似度 (0-1)
    price_similarity: float             # 价格相似度
    ema_similarity: float               # EMA相似度
    volume_similarity: float            # 成交量相似度
    volatility_similarity: float        # 波动率相似度
    trend_similarity: float             # 趋势相似度
    future_return_1x: float             # 后续等长收益率
    future_return_half: float           # 后续半段收益率
    future_max_drawdown: float          # 最大回撤
    future_max_gain: float              # 最大涨幅
    future_trend: str                   # 后续趋势
    history_segment: List[float]        # 历史片段
    future_segment: List[float]         # 未来片段
```

### PredictionSummary (预测摘要)

```python
@dataclass
class PredictionSummary:
    total_matches: int                  # 总匹配数
    avg_similarity: float               # 平均相似度
    bullish_count: int                  # 上涨数
    bearish_count: int                  # 下跌数
    neutral_count: int                  # 横盘数
    bullish_probability: float          # 上涨概率
    avg_future_return: float            # 平均收益
    median_future_return: float         # 中位数收益
    avg_max_gain: float                 # 平均最大涨幅
    avg_max_drawdown: float             # 平均最大回撤
    confidence: str                     # 置信度 (low/medium/high)
    suggestion: str                     # 建议文字
```

## 🧮 算法详解

### 1. DTW (Dynamic Time Warping)

**目的：** 计算两个时间序列的相似度，允许时间轴拉伸

**算法流程：**
```
1. 初始化 DTW 矩阵 D[i][j]
2. D[0][0] = 0
3. 对所有 i, j:
   D[i][j] = |query[i] - candidate[j]| + min(
       D[i-1][j],      # 插入
       D[i][j-1],      # 删除
       D[i-1][j-1]     # 匹配
   )
4. 相似度 = 1 / (1 + D[n][m])
```

**时间复杂度：** O(n*m)

**优化：** 使用 dtaidistance C 扩展，性能提升 10-100 倍

### 2. 皮尔逊相关系数快速过滤

**目的：** 快速过滤低相关性窗口，避免计算昂贵的 DTW

**公式：**
```
r = Σ((x - mean_x) * (y - mean_y)) / sqrt(Σ(x - mean_x)² * Σ(y - mean_y)²)
```

**阈值：** |r| > 0.3 才进行 DTW 计算

**性能提升：** 减少 50-80% 的 DTW 计算

### 3. 多维度加权相似度

**公式：**
```
总分 = 0.50 * price_sim 
     + 0.20 * ema_sim 
     + 0.15 * vol_sim 
     + 0.10 * volatility_sim 
     + 0.05 * trend_sim
```

**权重设计理由：**
- 价格形态最重要（50%）
- EMA 排列次之（20%）
- 成交量和波动率辅助（15% + 10%）
- 趋势方向作为确认（5%）

### 4. 降采样策略

**目的：** 处理大规模数据时加速初步扫描

**实现：**
```python
if n_hist > 10000:
    downsample_factor = max(1, n_hist // 5000)
    # 每隔 downsample_factor 个数据点采样一个
```

**效果：** 减少 50-90% 的计算量，精度损失 < 5%

## 🔐 数据库设计

### klines 表

```sql
CREATE TABLE klines (
    symbol TEXT,              -- 交易对，如 BTC/USDT
    timeframe TEXT,           -- 时间周期，如 1h
    timestamp INTEGER,        -- Unix 时间戳（毫秒）
    open REAL,               -- 开盘价
    high REAL,               -- 最高价
    low REAL,                -- 最低价
    close REAL,              -- 收盘价
    volume REAL,             -- 成交量
    PRIMARY KEY (symbol, timeframe, timestamp)
);

CREATE INDEX idx_klines_lookup 
ON klines(symbol, timeframe, timestamp);
```

### 数据统计

- 单个交易对 1 年 1h 数据：~8,760 条记录
- 单条记录大小：~50 字节
- 10 个交易对 1 年数据：~4.4 MB

## 🚀 性能优化

### 1. 缓存策略

```python
# 内存缓存最近查询
_cache = {}
_cache_ttl = 3600  # 1 小时

def get_close_prices_cached(symbol, timeframe):
    key = f"{symbol}:{timeframe}"
    if key in _cache and time.time() - _cache[key]['time'] < _cache_ttl:
        return _cache[key]['data']
    
    data = get_close_prices(symbol, timeframe)
    _cache[key] = {'data': data, 'time': time.time()}
    return data
```

### 2. 并发处理

```python
# 使用 asyncio 并发拉取多个交易对数据
async def ensure_data_concurrent(symbols, timeframes):
    tasks = [
        ensure_data(symbol, tf)
        for symbol in symbols
        for tf in timeframes
    ]
    await asyncio.gather(*tasks)
```

### 3. 数据库优化

```sql
-- 定期维护
VACUUM;
ANALYZE;

-- 批量插入
BEGIN TRANSACTION;
INSERT INTO klines VALUES (...);
INSERT INTO klines VALUES (...);
...
COMMIT;
```

## 🧪 测试策略

### 单元测试

- Vision Analyzer：JSON 解析、字段验证
- Pattern Matcher：DTW 计算、相似度评分
- Data Manager：数据库操作、查询
- Result Analyzer：统计计算、置信度评估

### 集成测试

- 端到端流程：从图片上传到结果返回
- 数据一致性：数据在各模块间的完整性
- 去重叠逻辑：重叠窗口的正确处理

### 性能测试

- 匹配速度：不同数据量下的处理时间
- 内存使用：大规模数据处理的内存占用
- 数据库查询：索引效率、查询性能

## 📡 API 设计

### REST API

```
POST /api/analyze
  请求：multipart/form-data
    - file: 图片文件
    - symbol: 交易对（可选）
    - timeframe: 时间周期（可选）
    - top_n: 返回匹配数（默认10）
    - min_similarity: 最低相似度（默认0.5）
  
  响应：application/json
    {
      "chart_analysis": {...},
      "matches": [...],
      "prediction": {...},
      "metadata": {...}
    }

GET /api/health
  响应：{"status": "ok"}

GET /api/data/status
  响应：{"status": [...]}
```

## 🔄 扩展性设计

### 支持新交易对

```python
# 只需在 init_data.py 中添加
INIT_PAIRS = [
    ("BTC/USDT", ["1h", "4h", "1d"]),
    ("ETH/USDT", ["1h", "4h", "1d"]),
    ("NEW/USDT", ["1h", "4h", "1d"]),  # 新交易对
]
```

### 支持新时间周期

```python
# 在 data_manager.py 中更新
TIMEFRAMES = ['5m', '15m', '30m', '1h', '4h', '1d', '1w']  # 添加 1w
```

### 支持新的相似度维度

```python
# 在 pattern_matcher.py 中添加新维度
def _calc_new_similarity(self, query, candidate):
    # 实现新的相似度计算
    return similarity_score

# 在 find_similar_patterns 中集成
new_sim = self._calc_new_similarity(...)
total_score = (
    price_sim * 0.45 +
    ema_sim * 0.20 +
    vol_sim * 0.15 +
    volatility_sim * 0.10 +
    trend_sim * 0.05 +
    new_sim * 0.05  # 新维度
)
```

## 📝 代码规范

### 命名约定

- 类名：PascalCase (ChartVisionAnalyzer)
- 函数名：snake_case (find_similar_patterns)
- 常量名：UPPER_SNAKE_CASE (TIMEFRAMES)
- 私有方法：_leading_underscore (_normalize)

### 文档字符串

```python
def find_similar_patterns(
    self,
    query_sequence: np.ndarray,
    ...
) -> List[MatchResult]:
    """
    在历史数据中寻找最相似的走势
    
    Args:
        query_sequence: 归一化的查询价格序列
        ...
    
    Returns:
        List[MatchResult]: 排序后的匹配结果
    
    Raises:
        ValueError: 如果输入数据无效
    """
```

---

**最后更新：** 2024 年

**版本：** 1.0.0
