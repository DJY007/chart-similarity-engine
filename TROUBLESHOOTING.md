# 故障排除指南

本文档列出常见问题及其解决方案。

## 🔴 常见错误

### 1. API 密钥错误

**错误信息：**
```
AuthenticationError: Invalid API key provided
```

**解决方案：**
1. 检查 `.env` 文件中的 `ANTHROPIC_API_KEY`
2. 确保密钥格式正确（以 `sk-ant-` 开头）
3. 访问 https://console.anthropic.com 验证密钥
4. 确保密钥未过期或被禁用

### 2. 数据库连接失败

**错误信息：**
```
sqlite3.OperationalError: unable to open database file
```

**解决方案：**
1. 检查 `data/` 目录是否存在：
   ```bash
   mkdir -p data
   ```
2. 检查目录权限：
   ```bash
   chmod 755 data
   ```
3. 确保有足够的磁盘空间
4. 尝试删除损坏的数据库：
   ```bash
   rm data/klines.db
   python scripts/init_data.py
   ```

### 3. 前端无法连接后端

**错误信息：**
```
CORS error: Access to XMLHttpRequest has been blocked
```

**解决方案：**
1. 确保后端服务正在运行：
   ```bash
   curl http://localhost:8000/api/health
   ```
2. 检查防火墙设置
3. 验证 CORS 配置在 `app/main.py` 中正确
4. 检查浏览器控制台获取详细错误

### 4. Binance API 限制

**错误信息：**
```
ccxt.RateLimitExceeded: rate limit exceeded
```

**解决方案：**
1. 等待一段时间后重试
2. 减少并发请求数
3. 使用 Binance API 密钥提高限额（可选）
4. 检查网络连接

### 5. 内存不足

**错误信息：**
```
MemoryError: Unable to allocate memory
```

**解决方案：**
1. 减少历史数据量
2. 增加系统内存或虚拟内存
3. 使用降采样策略
4. 分批处理数据

## ⚠️ 性能问题

### 匹配速度慢

**症状：** 分析一张图片需要很长时间

**解决方案：**
1. 启用皮尔逊相关系数预过滤：
   ```python
   matches = matcher.find_similar_patterns(
       ...,
       use_pearson_filter=True,
       pearson_threshold=0.3
   )
   ```
2. 减少 `top_n` 参数
3. 增加 `min_similarity` 阈值
4. 使用更少的历史数据

### 数据库查询慢

**症状：** 获取历史数据很慢

**解决方案：**
1. 检查数据库索引：
   ```sql
   CREATE INDEX IF NOT EXISTS idx_klines_lookup 
   ON klines(symbol, timeframe, timestamp);
   ```
2. 分析数据库大小：
   ```bash
   ls -lh data/klines.db
   ```
3. 清理旧数据：
   ```sql
   DELETE FROM klines WHERE timestamp < ?;
   ```
4. 定期进行数据库维护：
   ```bash
   sqlite3 data/klines.db "VACUUM;"
   ```

### 高 CPU 使用率

**症状：** 后端进程占用大量 CPU

**解决方案：**
1. 检查是否有大量并发请求
2. 实现请求队列
3. 增加工作进程数
4. 使用负载均衡

## 🔧 调试技巧

### 启用详细日志

编辑 `app/main.py`：
```python
import logging

logging.basicConfig(level=logging.DEBUG)
logger = logging.getLogger(__name__)
```

### 检查 Vision API 响应

```python
from app.vision_analyzer import ChartVisionAnalyzer

analyzer = ChartVisionAnalyzer()
result = analyzer.analyze_chart("path/to/image.png")
print(result)
```

### 测试数据管理器

```python
from app.data_manager import HistoricalDataManager
import asyncio

manager = HistoricalDataManager()
asyncio.run(manager.ensure_data("BTC/USDT", "1h"))
closes = manager.get_close_prices("BTC/USDT", "1h")
print(f"Loaded {len(closes)} candles")
```

### 测试匹配引擎

```python
from app.pattern_matcher import PatternMatcher
import numpy as np

matcher = PatternMatcher()
query = np.array([0.1, 0.2, 0.3, 0.4, 0.5])
# 测试相似度计算
```

## 📋 检查清单

在报告问题前，请检查：

- [ ] Python 版本 >= 3.11
- [ ] Node.js 版本 >= 18
- [ ] 所有依赖已安装
- [ ] `.env` 文件已配置
- [ ] API 密钥有效
- [ ] 网络连接正常
- [ ] 磁盘空间充足
- [ ] 防火墙允许端口 8000 和 5173

## 🆘 获取帮助

如果问题未解决：

1. **查看日志**
   ```bash
   tail -f app.log
   docker-compose logs -f
   ```

2. **运行测试**
   ```bash
   pytest tests/ -v
   ```

3. **检查依赖版本**
   ```bash
   pip list
   npm list
   ```

4. **提交 Issue**
   - 包含完整的错误信息
   - 提供重现步骤
   - 附加相关日志
   - 说明系统环境

5. **联系开发者**
   - Email: support@example.com
   - Discord: [链接]
   - GitHub Issues: [链接]

## 📚 相关资源

- [Anthropic API 文档](https://docs.anthropic.com)
- [FastAPI 文档](https://fastapi.tiangolo.com)
- [React 文档](https://react.dev)
- [CCXT 文档](https://docs.ccxt.com)
- [SQLite 文档](https://www.sqlite.org/docs.html)

---

**最后更新：** 2024 年

**版本：** 1.0.0
