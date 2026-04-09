"""
FastAPI 主应用

提供 K 线模式匹配分析的 REST API
"""

import logging
import os
from pathlib import Path
from typing import Optional
from contextlib import asynccontextmanager

from fastapi import FastAPI, UploadFile, File, Query, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from fastapi.staticfiles import StaticFiles

from .config import config
from .logging_config import setup_logging, get_logger
from .vision_analyzer import ChartVisionAnalyzer
from .data_manager import HistoricalDataManager
from .pattern_matcher import PatternMatcher
from .result_analyzer import ResultAnalyzer

# 设置日志
setup_logging()
logger = get_logger(__name__)

# 初始化组件（全局单例）
vision_analyzer: Optional[ChartVisionAnalyzer] = None
data_manager: Optional[HistoricalDataManager] = None
pattern_matcher: Optional[PatternMatcher] = None
result_analyzer: Optional[ResultAnalyzer] = None


@asynccontextmanager
async def lifespan(app: FastAPI):
    """
    应用生命周期管理
    
    startup: 应用启动时初始化资源
    shutdown: 应用关闭时清理资源
    """
    # 启动
    logger.info("Starting Chart Similarity Engine...")
    
    try:
        global vision_analyzer, data_manager, pattern_matcher, result_analyzer
        
        # 验证配置
        if not config.validate():
            raise RuntimeError("Configuration validation failed")
        
        # 记录配置
        config.log_config()
        
        # 初始化数据库目录
        db_dir = Path(config.DB_PATH).parent
        db_dir.mkdir(parents=True, exist_ok=True)
        logger.info(f"Database directory: {db_dir}")
        
        # 初始化上传目录
        upload_dir = Path(config.UPLOAD_DIR)
        upload_dir.mkdir(parents=True, exist_ok=True)
        logger.info(f"Upload directory: {upload_dir}")
        
        # 初始化组件
        logger.info("Initializing components...")
        vision_analyzer = ChartVisionAnalyzer()
        data_manager = HistoricalDataManager(config.DB_PATH)
        pattern_matcher = PatternMatcher()
        result_analyzer = ResultAnalyzer()
        
        logger.info("✅ All components initialized successfully")
        
    except Exception as e:
        logger.error(f"❌ Startup failed: {str(e)}", exc_info=True)
        raise
    
    yield
    
    # 关闭
    logger.info("Shutting down Chart Similarity Engine...")
    try:
        # 清理资源
        if data_manager:
            logger.info("Closing database connections...")
        logger.info("✅ Shutdown completed successfully")
    except Exception as e:
        logger.error(f"❌ Shutdown error: {str(e)}", exc_info=True)


# 创建 FastAPI 应用
app = FastAPI(
    title="Chart Similarity Engine",
    description="K线模式匹配分析工具 - 通过 DeepSeek Vision 识别图表特征，使用 DTW 算法找到历史相似走势",
    version="1.0.0",
    lifespan=lifespan
)

# 添加 CORS 中间件
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# 挂载静态文件（前端）
frontend_dist = Path(__file__).parent.parent / "frontend" / "dist"
if frontend_dist.exists():
    app.mount("/static", StaticFiles(directory=str(frontend_dist)), name="static")
    logger.info(f"Frontend static files mounted: {frontend_dist}")


@app.get("/api/health")
async def health() -> dict:
    """
    健康检查端点
    
    Returns:
        健康状态信息
    """
    return {
        "status": "ok",
        "environment": config.ENVIRONMENT,
        "debug": config.DEBUG,
    }


@app.get("/api/config")
async def get_config_info() -> dict:
    """
    获取应用配置信息
    
    Returns:
        配置信息（不包含敏感数据）
    """
    return config.to_dict()


@app.post("/api/analyze")
async def analyze_chart(
    file: UploadFile = File(...),
    symbol: Optional[str] = Query(None, description="交易对，如 BTC/USDT"),
    timeframe: Optional[str] = Query(None, description="时间周期，如 1h, 4h, 1d"),
    top_n: int = Query(config.DEFAULT_TOP_N, description="返回前 N 个匹配结果"),
    min_similarity: float = Query(config.DEFAULT_MIN_SIMILARITY, description="最低相似度阈值"),
) -> dict:
    """
    主分析接口：上传 K 线截图并返回匹配结果
    
    Args:
        file: K 线截图文件
        symbol: 交易对（可选，如不指定则自动识别）
        timeframe: 时间周期（可选，如不指定则自动识别）
        top_n: 返回结果数量
        min_similarity: 最低相似度阈值
        
    Returns:
        分析结果，包含识别信息、匹配列表和预测摘要
    """
    request_id = None
    
    try:
        import uuid
        request_id = str(uuid.uuid4())[:8]
        logger.info(f"[{request_id}] Starting analysis for file: {file.filename}")
        
        # 验证文件
        if not file.filename:
            raise HTTPException(status_code=400, detail="Filename is required")
        
        # 检查文件类型
        file_ext = file.filename.split(".")[-1].lower()
        if file_ext not in config.ALLOWED_EXTENSIONS:
            raise HTTPException(
                status_code=400,
                detail=f"File type not allowed. Allowed: {', '.join(config.ALLOWED_EXTENSIONS)}"
            )
        
        # 读取文件内容
        logger.info(f"[{request_id}] Reading file content...")
        file_content = await file.read()
        
        # 检查文件大小
        if len(file_content) > config.MAX_UPLOAD_SIZE:
            raise HTTPException(
                status_code=413,
                detail=f"File too large. Max size: {config.MAX_UPLOAD_SIZE} bytes"
            )
        
        # 1. Vision 分析
        logger.info(f"[{request_id}] Analyzing chart with Vision API...")
        try:
            analysis = await vision_analyzer.analyze_chart(image_bytes=file_content)
        except Exception as e:
            logger.error(f"[{request_id}] Vision analysis failed: {str(e)}", exc_info=True)
            raise HTTPException(status_code=500, detail=f"Vision analysis failed: {str(e)}")
        
        # 2. 确定交易对和时间周期
        detected_symbol = symbol or analysis.get("symbol", config.DEFAULT_SYMBOL)
        detected_timeframe = timeframe or analysis.get("timeframe", config.DEFAULT_TIMEFRAME)
        
        logger.info(f"[{request_id}] Detected: {detected_symbol} {detected_timeframe}")
        
        # 3. 确保历史数据可用
        logger.info(f"[{request_id}] Syncing historical data...")
        try:
            await data_manager.ensure_data(detected_symbol, detected_timeframe)
        except Exception as e:
            logger.warning(f"[{request_id}] Data sync warning: {str(e)}")
        
        # 4. 获取历史数据
        logger.info(f"[{request_id}] Retrieving historical data...")
        try:
            hist_ohlcv = data_manager.get_ohlcv(detected_symbol, detected_timeframe)
            hist_timestamps = data_manager.get_timestamps(detected_symbol, detected_timeframe)
        except Exception as e:
            logger.error(f"[{request_id}] Failed to retrieve data: {str(e)}", exc_info=True)
            raise HTTPException(status_code=500, detail=f"Failed to retrieve historical data: {str(e)}")
        
        if len(hist_ohlcv) < 100:
            raise HTTPException(
                status_code=400,
                detail=f"Insufficient historical data. Need at least 100 candles, got {len(hist_ohlcv)}"
            )
        
        # 5. 模式匹配
        logger.info(f"[{request_id}] Performing pattern matching...")
        try:
            import numpy as np
            query_seq = np.array(analysis.get("normalized_price_sequence", []))
            
            if len(query_seq) < 10:
                raise HTTPException(
                    status_code=400,
                    detail="Failed to extract valid price sequence from chart"
                )
            
            matches = pattern_matcher.find_similar_patterns(
                query_sequence=query_seq,
                historical_ohlcv=hist_ohlcv,
                historical_timestamps=hist_timestamps,
                top_n=top_n,
                query_ema_state=analysis.get("indicators", {}).get("ema_arrangement", "tangled"),
                query_volume_pattern=analysis.get("indicators", {}).get("volume_pattern", "normal"),
                min_similarity=min_similarity
            )
            
            logger.info(f"[{request_id}] Found {len(matches)} matches")
            
        except Exception as e:
            logger.error(f"[{request_id}] Pattern matching failed: {str(e)}", exc_info=True)
            raise HTTPException(status_code=500, detail=f"Pattern matching failed: {str(e)}")
        
        # 6. 结果分析
        logger.info(f"[{request_id}] Analyzing results...")
        try:
            summary = result_analyzer.summarize(matches)
        except Exception as e:
            logger.error(f"[{request_id}] Result analysis failed: {str(e)}", exc_info=True)
            raise HTTPException(status_code=500, detail=f"Result analysis failed: {str(e)}")
        
        # 7. 组装返回数据
        result = {
            "request_id": request_id,
            "chart_analysis": analysis,
            "matches": matches,
            "prediction": summary,
            "chart_data": {
                "query_normalized": analysis.get("normalized_price_sequence", []),
                "best_match_normalized": matches[0].get("normalized_sequence", []) if matches else [],
                "best_match_future": matches[0].get("future_sequence", []) if matches else [],
            }
        }
        
        logger.info(f"[{request_id}] ✅ Analysis completed successfully")
        return result
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"[{request_id}] Unexpected error: {str(e)}", exc_info=True)
        raise HTTPException(status_code=500, detail=f"Internal server error: {str(e)}")


@app.get("/api/data/status")
async def data_status() -> dict:
    """
    查看已缓存的历史数据状态
    
    Returns:
        数据库中已缓存的交易对和时间周期信息
    """
    try:
        logger.info("Fetching data status...")
        import sqlite3
        with sqlite3.connect(config.DB_PATH) as conn:
            cursor = conn.cursor()
            cursor.execute("SELECT symbol, timeframe, COUNT(*), MIN(timestamp), MAX(timestamp) FROM klines GROUP BY symbol, timeframe")
            rows = cursor.fetchall()
            status = []
            for r in rows:
                status.append({
                    "symbol": r[0],
                    "timeframe": r[1],
                    "count": r[2],
                    "start": r[3],
                    "end": r[4]
                })
            return {"status": "ok", "data": status}
    except Exception as e:
        logger.error(f"Failed to get data status: {str(e)}", exc_info=True)
        raise HTTPException(status_code=500, detail=f"Failed to get data status: {str(e)}")


@app.get("/")
async def root():
    """根路径重定向到 API 文档"""
    return {
        "message": "Chart Similarity Engine API",
        "docs": "/docs",
        "health": "/api/health"
    }


if __name__ == "__main__":
    import uvicorn
    
    uvicorn.run(
        app,
        host=config.API_HOST,
        port=config.API_PORT,
        reload=config.API_RELOAD,
        log_level=config.LOG_LEVEL.lower()
    )
