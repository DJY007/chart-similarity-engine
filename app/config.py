"""
配置管理模块

支持从环境变量、.env 文件和代码中加载配置
"""

import os
import logging
from typing import Optional, Dict, Any
from pathlib import Path
from dotenv import load_dotenv

# 加载 .env 文件
env_file = Path(__file__).parent.parent / ".env"
if env_file.exists():
    load_dotenv(env_file)

logger = logging.getLogger(__name__)


class Config:
    """应用配置类"""
    
    # API 配置
    DEEPSEEK_API_KEY: str = os.environ.get("DEEPSEEK_API_KEY", "")
    DEEPSEEK_API_URL: str = os.environ.get("DEEPSEEK_API_URL", "https://api.deepseek.com/chat/completions")
    DEEPSEEK_MODEL: str = os.environ.get("DEEPSEEK_MODEL", "deepseek-vision")
    DEEPSEEK_TIMEOUT: float = float(os.environ.get("DEEPSEEK_TIMEOUT", "60.0"))
    
    # Telegram Bot 配置
    TELEGRAM_BOT_TOKEN: str = os.environ.get("TELEGRAM_BOT_TOKEN", "")
    TELEGRAM_ENABLED: bool = os.environ.get("TELEGRAM_ENABLED", "false").lower() == "true"
    
    # Binance 配置
    BINANCE_API_KEY: str = os.environ.get("BINANCE_API_KEY", "")
    BINANCE_SECRET: str = os.environ.get("BINANCE_SECRET", "")
    
    # 数据库配置
    DB_PATH: str = os.environ.get("DB_PATH", "data/klines.db")
    DB_TIMEOUT: float = float(os.environ.get("DB_TIMEOUT", "30.0"))
    
    # API 服务器配置
    API_HOST: str = os.environ.get("API_HOST", "0.0.0.0")
    API_PORT: int = int(os.environ.get("API_PORT", "8000"))
    API_BASE_URL: str = os.environ.get("API_BASE_URL", "http://localhost:8000")
    API_RELOAD: bool = os.environ.get("API_RELOAD", "false").lower() == "true"
    
    # 模式匹配配置
    DEFAULT_SYMBOL: str = os.environ.get("DEFAULT_SYMBOL", "BTC/USDT")
    DEFAULT_TIMEFRAME: str = os.environ.get("DEFAULT_TIMEFRAME", "4h")
    DEFAULT_TOP_N: int = int(os.environ.get("DEFAULT_TOP_N", "10"))
    DEFAULT_MIN_SIMILARITY: float = float(os.environ.get("DEFAULT_MIN_SIMILARITY", "0.5"))
    
    # 性能配置
    PEARSON_THRESHOLD: float = float(os.environ.get("PEARSON_THRESHOLD", "0.3"))
    DOWNSAMPLE_THRESHOLD: int = int(os.environ.get("DOWNSAMPLE_THRESHOLD", "10000"))
    DOWNSAMPLE_TARGET: int = int(os.environ.get("DOWNSAMPLE_TARGET", "5000"))
    
    # 日志配置
    LOG_LEVEL: str = os.environ.get("LOG_LEVEL", "INFO")
    LOG_FORMAT: str = os.environ.get("LOG_FORMAT", "%(asctime)s - %(name)s - %(levelname)s - %(message)s")
    LOG_FILE: Optional[str] = os.environ.get("LOG_FILE", None)
    
    # 环境
    ENVIRONMENT: str = os.environ.get("ENVIRONMENT", "development")
    DEBUG: bool = os.environ.get("DEBUG", "false").lower() == "true"
    
    # 上传配置
    UPLOAD_DIR: str = os.environ.get("UPLOAD_DIR", "data/uploads")
    MAX_UPLOAD_SIZE: int = int(os.environ.get("MAX_UPLOAD_SIZE", "10485760"))  # 10MB
    ALLOWED_EXTENSIONS: tuple = ("jpg", "jpeg", "png", "gif", "webp")
    
    @classmethod
    def validate(cls) -> bool:
        """验证必需的配置"""
        errors = []
        
        if not cls.DEEPSEEK_API_KEY:
            errors.append("DEEPSEEK_API_KEY is required")
        
        if not cls.TELEGRAM_BOT_TOKEN:
            logger.warning("TELEGRAM_BOT_TOKEN not set, Telegram Bot will be disabled")
        
        if errors:
            for error in errors:
                logger.error(f"Configuration error: {error}")
            return False
        
        return True
    
    @classmethod
    def to_dict(cls) -> Dict[str, Any]:
        """将配置转换为字典（不包含敏感信息）"""
        return {
            "environment": cls.ENVIRONMENT,
            "debug": cls.DEBUG,
            "api_host": cls.API_HOST,
            "api_port": cls.API_PORT,
            "db_path": cls.DB_PATH,
            "default_symbol": cls.DEFAULT_SYMBOL,
            "default_timeframe": cls.DEFAULT_TIMEFRAME,
            "default_top_n": cls.DEFAULT_TOP_N,
            "default_min_similarity": cls.DEFAULT_MIN_SIMILARITY,
            "telegram_enabled": cls.TELEGRAM_ENABLED,
            "log_level": cls.LOG_LEVEL,
        }
    
    @classmethod
    def log_config(cls) -> None:
        """记录配置信息"""
        logger.info("=" * 60)
        logger.info("Application Configuration")
        logger.info("=" * 60)
        for key, value in cls.to_dict().items():
            logger.info(f"{key}: {value}")
        logger.info("=" * 60)


class DevelopmentConfig(Config):
    """开发环境配置"""
    ENVIRONMENT = "development"
    DEBUG = True
    API_RELOAD = True
    LOG_LEVEL = "DEBUG"


class ProductionConfig(Config):
    """生产环境配置"""
    ENVIRONMENT = "production"
    DEBUG = False
    API_RELOAD = False
    LOG_LEVEL = "INFO"


class TestingConfig(Config):
    """测试环境配置"""
    ENVIRONMENT = "testing"
    DEBUG = True
    DB_PATH = "data/test_klines.db"
    LOG_LEVEL = "DEBUG"


def get_config() -> Config:
    """根据环境变量获取配置"""
    environment = os.environ.get("ENVIRONMENT", "development")
    
    if environment == "production":
        return ProductionConfig()
    elif environment == "testing":
        return TestingConfig()
    else:
        return DevelopmentConfig()


# 全局配置实例
config = get_config()
