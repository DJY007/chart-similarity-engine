import pytest
import numpy as np
from app.result_analyzer import ResultAnalyzer, PredictionSummary
from app.pattern_matcher import MatchResult

class TestResultAnalyzer:
    """结果分析器测试"""
    
    def setup_method(self):
        """每个测试前的初始化"""
        self.analyzer = ResultAnalyzer()
    
    def test_summarize_empty_matches(self):
        """测试空匹配列表"""
        summary = self.analyzer.summarize([])
        
        assert summary.total_matches == 0
        assert summary.avg_similarity == 0
        assert summary.bullish_count == 0
        assert summary.bearish_count == 0
        assert summary.confidence == "low"
    
    def test_summarize_single_match_bullish(self):
        """测试单个上涨匹配"""
        match = MatchResult(
            start_index=0,
            end_index=10,
            start_time="2024-01-01",
            end_time="2024-01-02",
            similarity_score=0.85,
            price_similarity=0.85,
            ema_similarity=0.8,
            volume_similarity=0.8,
            volatility_similarity=0.8,
            trend_similarity=0.8,
            future_return_1x=0.05,  # 5% 上涨
            future_return_half=0.02,
            future_max_drawdown=-0.02,
            future_max_gain=0.08,
            future_trend="up",
            history_segment=[1]*10,
            future_segment=[1]*10
        )
        
        summary = self.analyzer.summarize([match])
        
        assert summary.total_matches == 1
        assert summary.bullish_count == 1
        assert summary.bearish_count == 0
        assert summary.bullish_probability == 100.0
        assert summary.avg_future_return == 0.05
    
    def test_summarize_single_match_bearish(self):
        """测试单个下跌匹配"""
        match = MatchResult(
            start_index=0,
            end_index=10,
            start_time="2024-01-01",
            end_time="2024-01-02",
            similarity_score=0.82,
            price_similarity=0.82,
            ema_similarity=0.8,
            volume_similarity=0.8,
            volatility_similarity=0.8,
            trend_similarity=0.8,
            future_return_1x=-0.03,  # 3% 下跌
            future_return_half=-0.01,
            future_max_drawdown=-0.05,
            future_max_gain=0.01,
            future_trend="down",
            history_segment=[1]*10,
            future_segment=[1]*10
        )
        
        summary = self.analyzer.summarize([match])
        
        assert summary.total_matches == 1
        assert summary.bearish_count == 1
        assert summary.bullish_count == 0
        assert summary.bullish_probability == 0.0
        assert summary.avg_future_return == -0.03
    
    def test_summarize_multiple_matches_mixed(self):
        """测试混合的多个匹配"""
        matches = [
            MatchResult(
                start_index=0, end_index=10, start_time="2024-01-01", end_time="2024-01-02",
                similarity_score=0.90, price_similarity=0.9, ema_similarity=0.9,
                volume_similarity=0.9, volatility_similarity=0.9, trend_similarity=0.9,
                future_return_1x=0.05, future_return_half=0.02, future_max_drawdown=-0.02,
                future_max_gain=0.08, future_trend="up", history_segment=[1]*10, future_segment=[1]*10
            ),
            MatchResult(
                start_index=20, end_index=30, start_time="2024-02-01", end_time="2024-02-02",
                similarity_score=0.85, price_similarity=0.85, ema_similarity=0.8,
                volume_similarity=0.8, volatility_similarity=0.8, trend_similarity=0.8,
                future_return_1x=0.03, future_return_half=0.01, future_max_drawdown=-0.01,
                future_max_gain=0.06, future_trend="up", history_segment=[1]*10, future_segment=[1]*10
            ),
            MatchResult(
                start_index=40, end_index=50, start_time="2024-03-01", end_time="2024-03-02",
                similarity_score=0.80, price_similarity=0.8, ema_similarity=0.75,
                volume_similarity=0.75, volatility_similarity=0.75, trend_similarity=0.75,
                future_return_1x=-0.02, future_return_half=-0.01, future_max_drawdown=-0.04,
                future_max_gain=0.01, future_trend="down", history_segment=[1]*10, future_segment=[1]*10
            ),
        ]
        
        summary = self.analyzer.summarize(matches)
        
        assert summary.total_matches == 3
        assert summary.bullish_count == 2
        assert summary.bearish_count == 1
        assert summary.neutral_count == 0
        assert summary.bullish_probability == pytest.approx(66.67, rel=0.01)
        assert summary.avg_similarity == pytest.approx(0.85, rel=0.01)
    
    def test_confidence_high(self):
        """测试高置信度判断"""
        # 5个匹配，75% 上涨
        matches = [
            MatchResult(
                start_index=i*10, end_index=i*10+10, start_time="2024-01-01", end_time="2024-01-02",
                similarity_score=0.85, price_similarity=0.85, ema_similarity=0.8,
                volume_similarity=0.8, volatility_similarity=0.8, trend_similarity=0.8,
                future_return_1x=0.05, future_return_half=0.02, future_max_drawdown=-0.02,
                future_max_gain=0.08, future_trend="up", history_segment=[1]*10, future_segment=[1]*10
            )
            for i in range(4)
        ] + [
            MatchResult(
                start_index=40, end_index=50, start_time="2024-05-01", end_time="2024-05-02",
                similarity_score=0.80, price_similarity=0.8, ema_similarity=0.75,
                volume_similarity=0.75, volatility_similarity=0.75, trend_similarity=0.75,
                future_return_1x=-0.02, future_return_half=-0.01, future_max_drawdown=-0.04,
                future_max_gain=0.01, future_trend="down", history_segment=[1]*10, future_segment=[1]*10
            )
        ]
        
        summary = self.analyzer.summarize(matches)
        
        assert summary.confidence == "high"
        assert summary.bullish_probability == 80.0
    
    def test_confidence_medium(self):
        """测试中置信度判断"""
        # 3个匹配，67% 上涨
        matches = [
            MatchResult(
                start_index=i*10, end_index=i*10+10, start_time="2024-01-01", end_time="2024-01-02",
                similarity_score=0.85, price_similarity=0.85, ema_similarity=0.8,
                volume_similarity=0.8, volatility_similarity=0.8, trend_similarity=0.8,
                future_return_1x=0.05, future_return_half=0.02, future_max_drawdown=-0.02,
                future_max_gain=0.08, future_trend="up", history_segment=[1]*10, future_segment=[1]*10
            )
            for i in range(2)
        ] + [
            MatchResult(
                start_index=20, end_index=30, start_time="2024-03-01", end_time="2024-03-02",
                similarity_score=0.80, price_similarity=0.8, ema_similarity=0.75,
                volume_similarity=0.75, volatility_similarity=0.75, trend_similarity=0.75,
                future_return_1x=-0.02, future_return_half=-0.01, future_max_drawdown=-0.04,
                future_max_gain=0.01, future_trend="down", history_segment=[1]*10, future_segment=[1]*10
            )
        ]
        
        summary = self.analyzer.summarize(matches)
        
        assert summary.confidence == "medium"
    
    def test_confidence_low(self):
        """测试低置信度判断"""
        # 2个匹配，50% 上涨
        matches = [
            MatchResult(
                start_index=0, end_index=10, start_time="2024-01-01", end_time="2024-01-02",
                similarity_score=0.85, price_similarity=0.85, ema_similarity=0.8,
                volume_similarity=0.8, volatility_similarity=0.8, trend_similarity=0.8,
                future_return_1x=0.05, future_return_half=0.02, future_max_drawdown=-0.02,
                future_max_gain=0.08, future_trend="up", history_segment=[1]*10, future_segment=[1]*10
            ),
            MatchResult(
                start_index=10, end_index=20, start_time="2024-02-01", end_time="2024-02-02",
                similarity_score=0.80, price_similarity=0.8, ema_similarity=0.75,
                volume_similarity=0.75, volatility_similarity=0.75, trend_similarity=0.75,
                future_return_1x=-0.02, future_return_half=-0.01, future_max_drawdown=-0.04,
                future_max_gain=0.01, future_trend="down", history_segment=[1]*10, future_segment=[1]*10
            )
        ]
        
        summary = self.analyzer.summarize(matches)
        
        assert summary.confidence == "low"
    
    def test_median_return_calculation(self):
        """测试中位数收益率计算"""
        matches = [
            MatchResult(
                start_index=i*10, end_index=i*10+10, start_time="2024-01-01", end_time="2024-01-02",
                similarity_score=0.85, price_similarity=0.85, ema_similarity=0.8,
                volume_similarity=0.8, volatility_similarity=0.8, trend_similarity=0.8,
                future_return_1x=ret, future_return_half=ret/2, future_max_drawdown=-0.02,
                future_max_gain=ret*2, future_trend="up", history_segment=[1]*10, future_segment=[1]*10
            )
            for i, ret in enumerate([0.01, 0.02, 0.03, 0.04, 0.05])
        ]
        
        summary = self.analyzer.summarize(matches)
        
        # 中位数应该是 0.03
        assert summary.median_future_return == pytest.approx(0.03, rel=0.01)
    
    def test_max_gain_and_drawdown(self):
        """测试最大涨幅和最大回撤"""
        matches = [
            MatchResult(
                start_index=0, end_index=10, start_time="2024-01-01", end_time="2024-01-02",
                similarity_score=0.85, price_similarity=0.85, ema_similarity=0.8,
                volume_similarity=0.8, volatility_similarity=0.8, trend_similarity=0.8,
                future_return_1x=0.05, future_return_half=0.02, future_max_drawdown=-0.10,
                future_max_gain=0.15, future_trend="up", history_segment=[1]*10, future_segment=[1]*10
            ),
            MatchResult(
                start_index=10, end_index=20, start_time="2024-02-01", end_time="2024-02-02",
                similarity_score=0.80, price_similarity=0.8, ema_similarity=0.75,
                volume_similarity=0.75, volatility_similarity=0.75, trend_similarity=0.75,
                future_return_1x=-0.02, future_return_half=-0.01, future_max_drawdown=-0.08,
                future_max_gain=0.05, future_trend="down", history_segment=[1]*10, future_segment=[1]*10
            )
        ]
        
        summary = self.analyzer.summarize(matches)
        
        assert summary.avg_max_gain == pytest.approx(0.10, rel=0.01)
        assert summary.avg_max_drawdown == pytest.approx(-0.09, rel=0.01)
    
    def test_suggestion_generation(self):
        """测试建议文字生成"""
        # 高置信度上涨
        bullish_matches = [
            MatchResult(
                start_index=i*10, end_index=i*10+10, start_time="2024-01-01", end_time="2024-01-02",
                similarity_score=0.85, price_similarity=0.85, ema_similarity=0.8,
                volume_similarity=0.8, volatility_similarity=0.8, trend_similarity=0.8,
                future_return_1x=0.05, future_return_half=0.02, future_max_drawdown=-0.02,
                future_max_gain=0.08, future_trend="up", history_segment=[1]*10, future_segment=[1]*10
            )
            for i in range(5)
        ]
        
        summary = self.analyzer.summarize(bullish_matches)
        
        assert "强烈看涨" in summary.suggestion or "看涨" in summary.suggestion
        assert summary.confidence == "high"
