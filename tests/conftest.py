import pytest
import sys
import os

# Add the parent directory to sys.path so we can import app modules
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

@pytest.fixture
def sample_ohlcv_data():
    """提供示例 OHLCV 数据"""
    import numpy as np
    return np.array([
        [1609459200000, 100, 110, 90, 105, 1000],
        [1609462800000, 105, 115, 100, 110, 1100],
        [1609466400000, 110, 120, 105, 115, 1200],
        [1609470000000, 115, 125, 110, 120, 1300],
        [1609473600000, 120, 130, 115, 125, 1400],
    ])

@pytest.fixture
def sample_price_sequence():
    """提供示例价格序列"""
    import numpy as np
    return np.array([0.1, 0.2, 0.3, 0.4, 0.5, 0.6, 0.7, 0.8, 0.9, 1.0])

@pytest.fixture
def sample_match_result():
    """提供示例匹配结果"""
    from app.pattern_matcher import MatchResult
    return MatchResult(
        start_index=0,
        end_index=10,
        start_time="2024-01-01 10:00",
        end_time="2024-01-01 11:00",
        similarity_score=0.85,
        price_similarity=0.85,
        ema_similarity=0.80,
        volume_similarity=0.80,
        volatility_similarity=0.80,
        trend_similarity=0.80,
        future_return_1x=0.05,
        future_return_half=0.02,
        future_max_drawdown=-0.02,
        future_max_gain=0.08,
        future_trend="up",
        history_segment=[1.0]*10,
        future_segment=[1.0]*10
    )
