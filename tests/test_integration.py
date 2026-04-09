import pytest
import tempfile
import os
import numpy as np
from app.data_manager import HistoricalDataManager
from app.pattern_matcher import PatternMatcher
from app.result_analyzer import ResultAnalyzer

class TestIntegration:
    """集成测试"""
    
    def setup_method(self):
        """设置测试环境"""
        self.temp_db = tempfile.NamedTemporaryFile(delete=False, suffix=".db")
        self.temp_db.close()
        self.data_manager = HistoricalDataManager(db_path=self.temp_db.name)
        self.matcher = PatternMatcher()
        self.analyzer = ResultAnalyzer()
    
    def teardown_method(self):
        """清理测试环境"""
        if os.path.exists(self.temp_db.name):
            os.remove(self.temp_db.name)
    
    def test_end_to_end_matching_pipeline(self):
        """端到端匹配流程测试"""
        symbol = "BTC/USDT"
        timeframe = "1h"
        
        # 1. 准备历史数据
        # 构造一个上升趋势的历史数据
        base_price = 100
        ohlcv_data = []
        for i in range(200):
            price = base_price + i * 0.5
            ohlcv_data.append([
                i * 3600000,  # timestamp
                price,
                price + 1,
                price - 1,
                price,
                1000 + i * 10
            ])
        
        # 保存到数据库
        self.data_manager._save_klines(symbol, timeframe, ohlcv_data)
        
        # 2. 获取历史数据
        hist_ohlcv = self.data_manager.get_ohlcv(symbol, timeframe)
        hist_timestamps = self.data_manager.get_timestamps(symbol, timeframe)
        
        assert len(hist_ohlcv) == 200
        assert len(hist_timestamps) == 200
        
        # 3. 构造查询序列（从历史数据中提取一个片段）
        query_segment = hist_ohlcv[50:60, 4]  # 取第50-60根K线的收盘价
        query_normalized = self.matcher._normalize(query_segment)
        
        # 4. 执行匹配
        matches = self.matcher.find_similar_patterns(
            query_sequence=query_normalized,
            historical_ohlcv=hist_ohlcv,
            historical_timestamps=hist_timestamps,
            top_n=5,
            min_similarity=0.3
        )
        
        # 5. 验证匹配结果
        assert len(matches) > 0
        assert all(hasattr(m, 'similarity_score') for m in matches)
        assert all(0 <= m.similarity_score <= 1 for m in matches)
        
        # 6. 分析结果
        summary = self.analyzer.summarize(matches)
        
        assert summary.total_matches > 0
        assert 0 <= summary.bullish_probability <= 100
        assert summary.confidence in ["low", "medium", "high"]
    
    def test_matching_with_uptrend_data(self):
        """测试上升趋势数据的匹配"""
        symbol = "ETH/USDT"
        timeframe = "4h"
        
        # 构造明显的上升趋势
        ohlcv_data = []
        for i in range(100):
            price = 1000 + i * 5  # 持续上升
            ohlcv_data.append([
                i * 14400000,  # 4h timestamp
                price,
                price + 2,
                price - 2,
                price,
                5000 + i * 50
            ])
        
        self.data_manager._save_klines(symbol, timeframe, ohlcv_data)
        
        hist_ohlcv = self.data_manager.get_ohlcv(symbol, timeframe)
        hist_timestamps = self.data_manager.get_timestamps(symbol, timeframe)
        
        # 查询序列也是上升趋势
        query_segment = hist_ohlcv[10:20, 4]
        query_normalized = self.matcher._normalize(query_segment)
        
        matches = self.matcher.find_similar_patterns(
            query_sequence=query_normalized,
            historical_ohlcv=hist_ohlcv,
            historical_timestamps=hist_timestamps,
            top_n=5,
            min_similarity=0.3
        )
        
        summary = self.analyzer.summarize(matches)
        
        # 由于都是上升趋势，应该有较高的上涨概率
        if summary.total_matches > 0:
            assert summary.bullish_probability >= 50
    
    def test_matching_with_downtrend_data(self):
        """测试下降趋势数据的匹配"""
        symbol = "SOL/USDT"
        timeframe = "1d"
        
        # 构造明显的下降趋势
        ohlcv_data = []
        for i in range(100):
            price = 200 - i * 1  # 持续下降
            ohlcv_data.append([
                i * 86400000,  # 1d timestamp
                price,
                price + 1,
                price - 1,
                price,
                10000 + i * 100
            ])
        
        self.data_manager._save_klines(symbol, timeframe, ohlcv_data)
        
        hist_ohlcv = self.data_manager.get_ohlcv(symbol, timeframe)
        hist_timestamps = self.data_manager.get_timestamps(symbol, timeframe)
        
        # 查询序列也是下降趋势
        query_segment = hist_ohlcv[10:20, 4]
        query_normalized = self.matcher._normalize(query_segment)
        
        matches = self.matcher.find_similar_patterns(
            query_sequence=query_normalized,
            historical_ohlcv=hist_ohlcv,
            historical_timestamps=hist_timestamps,
            top_n=5,
            min_similarity=0.3
        )
        
        summary = self.analyzer.summarize(matches)
        
        # 由于都是下降趋势，应该有较高的下跌概率
        if summary.total_matches > 0:
            assert summary.bullish_probability <= 50
    
    def test_data_consistency_through_pipeline(self):
        """测试数据在整个流程中的一致性"""
        symbol = "BTC/USDT"
        timeframe = "1h"
        
        # 准备数据
        original_ohlcv = [
            [1000, 100, 110, 90, 105, 1000],
            [2000, 105, 115, 100, 110, 1100],
            [3000, 110, 120, 105, 115, 1200],
            [4000, 115, 125, 110, 120, 1300],
            [5000, 120, 130, 115, 125, 1400],
        ]
        
        self.data_manager._save_klines(symbol, timeframe, original_ohlcv)
        
        # 检索数据
        retrieved_ohlcv = self.data_manager.get_ohlcv(symbol, timeframe)
        
        # 验证数据一致性
        assert len(retrieved_ohlcv) == len(original_ohlcv)
        for i, orig in enumerate(original_ohlcv):
            assert retrieved_ohlcv[i, 0] == orig[0]  # timestamp
            assert retrieved_ohlcv[i, 4] == orig[4]  # close
    
    def test_overlapping_removal_in_pipeline(self):
        """测试去重叠逻辑在完整流程中的应用"""
        symbol = "BTC/USDT"
        timeframe = "1h"
        
        # 构造数据
        ohlcv_data = []
        for i in range(100):
            price = 100 + i * 0.1
            ohlcv_data.append([
                i * 3600000,
                price,
                price + 0.5,
                price - 0.5,
                price,
                1000
            ])
        
        self.data_manager._save_klines(symbol, timeframe, ohlcv_data)
        
        hist_ohlcv = self.data_manager.get_ohlcv(symbol, timeframe)
        hist_timestamps = self.data_manager.get_timestamps(symbol, timeframe)
        
        query_segment = hist_ohlcv[20:30, 4]
        query_normalized = self.matcher._normalize(query_segment)
        
        matches = self.matcher.find_similar_patterns(
            query_sequence=query_normalized,
            historical_ohlcv=hist_ohlcv,
            historical_timestamps=hist_timestamps,
            top_n=10,
            min_similarity=0.3
        )
        
        # 检查去重叠逻辑是否工作
        # 匹配结果中的起始索引应该有足够的间隔
        if len(matches) > 1:
            for i in range(len(matches) - 1):
                gap = abs(matches[i].start_index - matches[i+1].start_index)
                # 间隔应该至少是窗口大小的一半
                assert gap >= 5  # 假设窗口大小至少是10
    
    def test_error_handling_with_insufficient_data(self):
        """测试数据不足时的错误处理"""
        symbol = "BTC/USDT"
        timeframe = "1h"
        
        # 只保存很少的数据
        ohlcv_data = [
            [1000, 100, 110, 90, 105, 1000],
            [2000, 105, 115, 100, 110, 1100],
        ]
        
        self.data_manager._save_klines(symbol, timeframe, ohlcv_data)
        
        hist_ohlcv = self.data_manager.get_ohlcv(symbol, timeframe)
        hist_timestamps = self.data_manager.get_timestamps(symbol, timeframe)
        
        query_segment = np.array([0.3, 0.4, 0.5, 0.6])
        
        # 应该能够优雅地处理数据不足的情况
        matches = self.matcher.find_similar_patterns(
            query_sequence=query_segment,
            historical_ohlcv=hist_ohlcv,
            historical_timestamps=hist_timestamps,
            top_n=5,
            min_similarity=0.3
        )
        
        # 可能返回空列表或很少的匹配
        assert isinstance(matches, list)
    
    def test_result_summary_with_mixed_outcomes(self):
        """测试混合结果的汇总"""
        symbol = "BTC/USDT"
        timeframe = "1h"
        
        # 构造数据
        ohlcv_data = []
        for i in range(150):
            price = 100 + i * 0.3 + (i % 10) * 0.5  # 上升趋势 + 波动
            ohlcv_data.append([
                i * 3600000,
                price,
                price + 1,
                price - 1,
                price,
                1000 + i * 5
            ])
        
        self.data_manager._save_klines(symbol, timeframe, ohlcv_data)
        
        hist_ohlcv = self.data_manager.get_ohlcv(symbol, timeframe)
        hist_timestamps = self.data_manager.get_timestamps(symbol, timeframe)
        
        query_segment = hist_ohlcv[40:50, 4]
        query_normalized = self.matcher._normalize(query_segment)
        
        matches = self.matcher.find_similar_patterns(
            query_sequence=query_normalized,
            historical_ohlcv=hist_ohlcv,
            historical_timestamps=hist_timestamps,
            top_n=10,
            min_similarity=0.3
        )
        
        summary = self.analyzer.summarize(matches)
        
        # 验证汇总的完整性
        assert summary.total_matches >= 0
        assert summary.bullish_count + summary.bearish_count + summary.neutral_count == summary.total_matches
        assert 0 <= summary.bullish_probability <= 100
        assert summary.confidence in ["low", "medium", "high"]
