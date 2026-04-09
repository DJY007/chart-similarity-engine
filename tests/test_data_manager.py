import pytest
import sqlite3
import numpy as np
import tempfile
import os
from app.data_manager import HistoricalDataManager

class TestHistoricalDataManager:
    """历史数据管理器测试"""
    
    def setup_method(self):
        """每个测试前创建临时数据库"""
        self.temp_db = tempfile.NamedTemporaryFile(delete=False, suffix=".db")
        self.temp_db.close()
        self.manager = HistoricalDataManager(db_path=self.temp_db.name)
    
    def teardown_method(self):
        """测试后清理临时数据库"""
        if os.path.exists(self.temp_db.name):
            os.remove(self.temp_db.name)
    
    def test_init_db(self):
        """测试数据库初始化"""
        # 检查表是否存在
        with sqlite3.connect(self.manager.db_path) as conn:
            cursor = conn.cursor()
            cursor.execute(
                "SELECT name FROM sqlite_master WHERE type='table' AND name='klines'"
            )
            result = cursor.fetchone()
            assert result is not None
    
    def test_save_and_retrieve_klines(self):
        """测试保存和检索 K 线数据"""
        symbol = "BTC/USDT"
        timeframe = "1h"
        
        # 构造测试数据
        ohlcv = [
            [1609459200000, 29000, 29500, 28500, 29200, 100],
            [1609462800000, 29200, 29800, 29000, 29500, 110],
            [1609466400000, 29500, 30000, 29300, 29800, 120],
        ]
        
        # 保存数据
        self.manager._save_klines(symbol, timeframe, ohlcv)
        
        # 检索数据
        closes = self.manager.get_close_prices(symbol, timeframe)
        
        assert len(closes) == 3
        assert closes[0] == 29200
        assert closes[1] == 29500
        assert closes[2] == 29800
    
    def test_get_ohlcv(self):
        """测试获取完整 OHLCV 数据"""
        symbol = "ETH/USDT"
        timeframe = "4h"
        
        ohlcv = [
            [1609459200000, 1000, 1100, 900, 1050, 50],
            [1609473600000, 1050, 1150, 1000, 1100, 60],
        ]
        
        self.manager._save_klines(symbol, timeframe, ohlcv)
        
        result = self.manager.get_ohlcv(symbol, timeframe)
        
        assert result.shape == (2, 6)
        assert result[0, 4] == 1050  # 第一条的收盘价
        assert result[1, 4] == 1100  # 第二条的收盘价
    
    def test_get_timestamps(self):
        """测试获取时间戳序列"""
        symbol = "SOL/USDT"
        timeframe = "1d"
        
        timestamps = [1609459200000, 1609545600000, 1609632000000]
        ohlcv = [
            [ts, 100, 110, 90, 105, 1000] for ts in timestamps
        ]
        
        self.manager._save_klines(symbol, timeframe, ohlcv)
        
        result = self.manager.get_timestamps(symbol, timeframe)
        
        assert len(result) == 3
        assert result[0] == timestamps[0]
        assert result[-1] == timestamps[-1]
    
    def test_get_last_timestamp(self):
        """测试获取最后的时间戳"""
        symbol = "BTC/USDT"
        timeframe = "1h"
        
        ohlcv = [
            [1609459200000, 100, 110, 90, 105, 1000],
            [1609462800000, 105, 115, 100, 110, 1100],
            [1609466400000, 110, 120, 105, 115, 1200],
        ]
        
        self.manager._save_klines(symbol, timeframe, ohlcv)
        
        last_ts = self.manager._get_last_timestamp(symbol, timeframe)
        
        assert last_ts == 1609466400000
    
    def test_get_last_timestamp_empty(self):
        """测试空数据库中获取最后时间戳"""
        last_ts = self.manager._get_last_timestamp("NONEXISTENT/USDT", "1h")
        
        assert last_ts is None
    
    def test_duplicate_insert_ignored(self):
        """测试重复插入被忽略"""
        symbol = "BTC/USDT"
        timeframe = "1h"
        
        ohlcv = [[1609459200000, 100, 110, 90, 105, 1000]]
        
        # 插入两次相同的数据
        self.manager._save_klines(symbol, timeframe, ohlcv)
        self.manager._save_klines(symbol, timeframe, ohlcv)
        
        closes = self.manager.get_close_prices(symbol, timeframe)
        
        # 应该只有一条记录
        assert len(closes) == 1
    
    def test_get_ohlcv_with_time_range(self):
        """测试按时间范围查询 OHLCV"""
        symbol = "ETH/USDT"
        timeframe = "1h"
        
        ohlcv = [
            [1000, 100, 110, 90, 105, 1000],
            [2000, 105, 115, 100, 110, 1100],
            [3000, 110, 120, 105, 115, 1200],
            [4000, 115, 125, 110, 120, 1300],
        ]
        
        self.manager._save_klines(symbol, timeframe, ohlcv)
        
        # 查询时间戳在 1500-3500 之间的数据
        result = self.manager.get_ohlcv(symbol, timeframe, start_ts=1500, end_ts=3500)
        
        assert len(result) == 2
        assert result[0, 0] == 2000
        assert result[1, 0] == 3000
    
    def test_timeframe_support(self):
        """测试支持的时间周期"""
        for tf in self.manager.TIMEFRAMES:
            assert tf in ['5m', '15m', '30m', '1h', '4h', '1d']
    
    def test_history_depth_config(self):
        """测试历史深度配置"""
        assert self.manager.HISTORY_DEPTH['5m'] == 90
        assert self.manager.HISTORY_DEPTH['1d'] == 1825
        assert len(self.manager.HISTORY_DEPTH) == len(self.manager.TIMEFRAMES)


class TestDataConsistency:
    """数据一致性测试"""
    
    def setup_method(self):
        self.temp_db = tempfile.NamedTemporaryFile(delete=False, suffix=".db")
        self.temp_db.close()
        self.manager = HistoricalDataManager(db_path=self.temp_db.name)
    
    def teardown_method(self):
        if os.path.exists(self.temp_db.name):
            os.remove(self.temp_db.name)
    
    def test_ohlc_relationships(self):
        """测试 OHLC 数据的逻辑关系"""
        symbol = "BTC/USDT"
        timeframe = "1h"
        
        # 构造有效的 OHLC 数据（High >= Open, Close, Low <= Open, Close, Low）
        ohlcv = [
            [1000, 100, 150, 80, 120, 1000],  # Open=100, High=150, Low=80, Close=120
            [2000, 120, 140, 110, 130, 1100],
        ]
        
        self.manager._save_klines(symbol, timeframe, ohlcv)
        result = self.manager.get_ohlcv(symbol, timeframe)
        
        # 验证 High >= Low
        assert all(result[:, 2] >= result[:, 3])
        # 验证 High >= Open 和 Close
        assert all(result[:, 2] >= result[:, 1])
        assert all(result[:, 2] >= result[:, 4])
    
    def test_volume_positive(self):
        """测试成交量为正"""
        symbol = "ETH/USDT"
        timeframe = "4h"
        
        ohlcv = [
            [1000, 100, 110, 90, 105, 1000],
            [2000, 105, 115, 100, 110, 0],  # 零成交量
        ]
        
        self.manager._save_klines(symbol, timeframe, ohlcv)
        result = self.manager.get_ohlcv(symbol, timeframe)
        
        # 成交量应该 >= 0
        assert all(result[:, 5] >= 0)
    
    def test_close_prices_array_type(self):
        """测试收盘价返回类型"""
        symbol = "BTC/USDT"
        timeframe = "1d"
        
        ohlcv = [
            [1000, 100, 110, 90, 105, 1000],
            [2000, 105, 115, 100, 110, 1100],
        ]
        
        self.manager._save_klines(symbol, timeframe, ohlcv)
        closes = self.manager.get_close_prices(symbol, timeframe)
        
        assert isinstance(closes, np.ndarray)
        assert closes.dtype == np.float64
        assert len(closes) == 2
