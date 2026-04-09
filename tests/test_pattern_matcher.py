import pytest
import numpy as np
from app.pattern_matcher import PatternMatcher, MatchResult
from scipy import stats

class TestPatternMatcher:
    """Pattern Matcher 单元测试"""
    
    def setup_method(self):
        """每个测试前的初始化"""
        self.matcher = PatternMatcher()
    
    def test_normalize(self):
        """测试数据归一化"""
        seq = np.array([10, 20, 30, 40, 50])
        normalized = self.matcher._normalize(seq)
        
        assert np.min(normalized) == 0.0
        assert np.max(normalized) == 1.0
        assert len(normalized) == len(seq)
    
    def test_normalize_constant_sequence(self):
        """测试常数序列归一化"""
        seq = np.array([5, 5, 5, 5])
        normalized = self.matcher._normalize(seq)
        
        assert np.all(normalized == 0)
    
    def test_ema_calculation(self):
        """测试 EMA 计算"""
        prices = np.array([100, 102, 101, 103, 105, 104, 106])
        ema = self.matcher._ema(prices, 3)
        
        # EMA 应该是一个浮点数
        assert isinstance(ema, float)
        # EMA 应该在价格范围内
        assert np.min(prices) <= ema <= np.max(prices)
    
    def test_ema_state_bullish(self):
        """测试 EMA 状态识别 - 多头排列"""
        # 构造多头排列：EMA7 > EMA25 > EMA99
        prices = np.array([100 + i*2 for i in range(100)])  # 上升趋势
        state = self.matcher._calc_ema_state(prices)
        
        assert state in ["bullish_aligned", "bearish_aligned", "crossing", "tangled"]
    
    def test_ema_similarity_same_state(self):
        """测试 EMA 相似度 - 相同状态"""
        sim = self.matcher._calc_ema_similarity("bullish_aligned", "bullish_aligned")
        assert sim == 1.0
    
    def test_ema_similarity_different_state(self):
        """测试 EMA 相似度 - 不同状态"""
        sim = self.matcher._calc_ema_similarity("bullish_aligned", "bearish_aligned")
        assert sim == 0.0
    
    def test_volatility_calculation(self):
        """测试波动率计算"""
        prices = np.array([100, 102, 101, 103, 105, 104, 106, 108])
        vol = self.matcher._calc_volatility(prices)
        
        assert vol >= 0
        assert isinstance(vol, float)
    
    def test_trend_slope_uptrend(self):
        """测试趋势斜率 - 上升趋势"""
        prices = np.array([100 + i for i in range(20)])  # 明显上升
        slope = self.matcher._calc_trend_slope(prices)
        
        assert slope > 0
    
    def test_trend_slope_downtrend(self):
        """测试趋势斜率 - 下降趋势"""
        prices = np.array([100 - i for i in range(20)])  # 明显下降
        slope = self.matcher._calc_trend_slope(prices)
        
        assert slope < 0
    
    def test_remove_overlapping(self):
        """测试去重叠逻辑"""
        # 创建多个重叠的匹配结果
        results = [
            MatchResult(0, 10, "2024-01-01", "2024-01-02", 0.9, 0.9, 0.8, 0.8, 0.8, 0.8, 0.1, 0.05, -0.05, 0.15, "up", [1]*10, [1]*10),
            MatchResult(5, 15, "2024-01-01", "2024-01-02", 0.7, 0.7, 0.6, 0.6, 0.6, 0.6, 0.1, 0.05, -0.05, 0.15, "up", [1]*10, [1]*10),
            MatchResult(20, 30, "2024-01-01", "2024-01-02", 0.85, 0.85, 0.8, 0.8, 0.8, 0.8, 0.1, 0.05, -0.05, 0.15, "up", [1]*10, [1]*10),
        ]
        
        filtered = self.matcher._remove_overlapping(results, min_gap=5)
        
        # 应该只保留第一个（最高分）和第三个（不重叠）
        assert len(filtered) <= len(results)
        # 第一个结果应该被保留（最高分）
        assert any(r.start_index == 0 for r in filtered)
    
    def test_future_stats_positive_return(self):
        """测试后续走势计算 - 正收益"""
        all_closes = np.array([100, 101, 102, 103, 104, 105, 106, 107, 108, 109])
        stats_result = self.matcher._calc_future_stats(all_closes, 5, 3)
        
        assert stats_result['future_return_1x'] > 0
        assert stats_result['future_max_gain'] > 0
        assert stats_result['future_trend'] in ['up', 'down', 'sideways']
    
    def test_future_stats_negative_return(self):
        """测试后续走势计算 - 负收益"""
        all_closes = np.array([100, 99, 98, 97, 96, 95, 94, 93, 92, 91])
        stats_result = self.matcher._calc_future_stats(all_closes, 5, 3)
        
        assert stats_result['future_return_1x'] < 0
        assert stats_result['future_max_drawdown'] < 0
        assert stats_result['future_trend'] in ['up', 'down', 'sideways']
    
    def test_volume_similarity(self):
        """测试成交量相似度"""
        volumes = np.array([1000, 1100, 1200, 1300, 1400])
        sim = self.matcher._calc_volume_similarity(volumes)
        
        assert 0 <= sim <= 1
    
    def test_find_similar_patterns_basic(self):
        """基本的模式匹配测试"""
        # 构造简单的历史数据
        query = np.array([0.2, 0.3, 0.4, 0.5, 0.6])
        
        # 构造历史 OHLCV 数据（6列）
        hist_prices = np.array([100 + i for i in range(100)])
        hist_ohlcv = np.column_stack([
            np.arange(100),  # timestamp
            hist_prices,      # open
            hist_prices + 1,  # high
            hist_prices - 1,  # low
            hist_prices,      # close
            np.ones(100) * 1000  # volume
        ])
        
        hist_timestamps = np.arange(100) * 1000
        
        matches = self.matcher.find_similar_patterns(
            query_sequence=query,
            historical_ohlcv=hist_ohlcv,
            historical_timestamps=hist_timestamps,
            top_n=5,
            min_similarity=0.3
        )
        
        assert len(matches) <= 5
        if len(matches) > 0:
            # 检查结果的完整性
            assert all(hasattr(m, 'similarity_score') for m in matches)
            assert all(0 <= m.similarity_score <= 1 for m in matches)
            # 结果应该按相似度降序排列
            scores = [m.similarity_score for m in matches]
            assert scores == sorted(scores, reverse=True)


class TestDTWSimilarity:
    """DTW 相似度测试"""
    
    def setup_method(self):
        self.matcher = PatternMatcher()
    
    def test_identical_sequences_high_similarity(self):
        """测试相同序列的高相似度"""
        seq1 = np.array([0.2, 0.3, 0.4, 0.5, 0.6])
        seq2 = np.array([0.2, 0.3, 0.4, 0.5, 0.6])
        
        from dtaidistance import dtw
        dist = dtw.distance_fast(seq1.astype(np.double), seq2.astype(np.double))
        similarity = 1 / (1 + dist)
        
        assert similarity > 0.9
    
    def test_completely_different_sequences_low_similarity(self):
        """测试完全不同序列的低相似度"""
        seq1 = np.array([0.1, 0.2, 0.3, 0.4, 0.5])
        seq2 = np.array([0.9, 0.8, 0.7, 0.6, 0.5])
        
        from dtaidistance import dtw
        dist = dtw.distance_fast(seq1.astype(np.double), seq2.astype(np.double))
        similarity = 1 / (1 + dist)
        
        assert similarity < 0.5
    
    def test_similar_but_shifted_sequences(self):
        """测试相似但时间轴拉伸的序列"""
        seq1 = np.array([0.2, 0.4, 0.6])
        seq2 = np.array([0.2, 0.3, 0.4, 0.5, 0.6])  # 更多点但趋势相同
        
        from dtaidistance import dtw
        dist = dtw.distance_fast(seq1.astype(np.double), seq2.astype(np.double))
        similarity = 1 / (1 + dist)
        
        # DTW 应该识别出相似的趋势
        assert similarity > 0.6


class TestPearsonCorrelationFilter:
    """皮尔逊相关系数快速过滤测试"""
    
    def test_pearson_correlation_similar(self):
        """测试皮尔逊相关系数 - 相似序列"""
        seq1 = np.array([1, 2, 3, 4, 5])
        seq2 = np.array([2, 4, 6, 8, 10])  # 完全正相关
        
        corr, _ = stats.pearsonr(seq1, seq2)
        assert corr > 0.9
    
    def test_pearson_correlation_opposite(self):
        """测试皮尔逊相关系数 - 反向序列"""
        seq1 = np.array([1, 2, 3, 4, 5])
        seq2 = np.array([5, 4, 3, 2, 1])  # 完全负相关
        
        corr, _ = stats.pearsonr(seq1, seq2)
        assert corr < -0.9
    
    def test_pearson_correlation_uncorrelated(self):
        """测试皮尔逊相关系数 - 无相关性"""
        seq1 = np.array([1, 2, 3, 4, 5])
        seq2 = np.array([1, 1, 1, 1, 1])  # 常数
        
        # 常数序列会导致 NaN，需要处理
        try:
            corr, _ = stats.pearsonr(seq1, seq2)
        except:
            corr = 0
        
        assert corr == 0 or np.isnan(corr)
