import ccxt
import sqlite3
import numpy as np
import os
from datetime import datetime, timedelta
from typing import List, Optional, Tuple, Dict

class HistoricalDataManager:
    # 支持的时间周期
    TIMEFRAMES = ['5m', '15m', '30m', '1h', '4h', '1d']
    
    # 默认拉取的历史深度 (天)
    HISTORY_DEPTH = {
        '5m': 90,
        '15m': 180,
        '30m': 365,
        '1h': 730,
        '4h': 1095,
        '1d': 1825
    }
    
    def __init__(self, db_path: str = "data/klines.db"):
        # Ensure data directory exists
        os.makedirs(os.path.dirname(db_path), exist_ok=True)
        self.db_path = db_path
        self.exchange = ccxt.binance({
            'enableRateLimit': True,
        })
        self._init_db()
    
    def _init_db(self):
        """初始化数据库表和索引"""
        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.cursor()
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS klines (
                    symbol TEXT,
                    timeframe TEXT,
                    timestamp INTEGER,
                    open REAL,
                    high REAL,
                    low REAL,
                    close REAL,
                    volume REAL,
                    PRIMARY KEY (symbol, timeframe, timestamp)
                )
            """)
            cursor.execute("CREATE INDEX IF NOT EXISTS idx_klines_lookup ON klines(symbol, timeframe, timestamp)")
            conn.commit()
    
    async def ensure_data(self, symbol: str, timeframe: str):
        """确保指定交易对和周期的历史数据已缓存且最新"""
        if timeframe not in self.TIMEFRAMES:
            raise ValueError(f"Unsupported timeframe: {timeframe}")
            
        # 1. 检查数据库中该交易对+周期的最新时间戳
        last_ts = self._get_last_timestamp(symbol, timeframe)
        
        # 2. 确定开始拉取的时间
        if last_ts:
            # 从最后一条数据的下一个周期开始
            start_ts = last_ts + self.exchange.parse_timeframe(timeframe) * 1000
        else:
            # 从历史深度开始
            days = self.HISTORY_DEPTH.get(timeframe, 30)
            start_ts = int((datetime.now() - timedelta(days=days)).timestamp() * 1000)
            
        # 3. 循环拉取数据直到最新
        now_ts = int(datetime.now().timestamp() * 1000)
        limit = 1000
        
        while start_ts < now_ts - self.exchange.parse_timeframe(timeframe) * 1000:
            try:
                print(f"Fetching {symbol} {timeframe} from {datetime.fromtimestamp(start_ts/1000)}")
                ohlcv = self.exchange.fetch_ohlcv(symbol, timeframe, since=start_ts, limit=limit)
                if not ohlcv:
                    break
                
                self._save_klines(symbol, timeframe, ohlcv)
                
                # 更新下一次拉取的开始时间
                last_fetched_ts = ohlcv[-1][0]
                if last_fetched_ts <= start_ts: # 防止死循环
                    break
                start_ts = last_fetched_ts + self.exchange.parse_timeframe(timeframe) * 1000
                
                # 如果返回的数据少于limit，说明已经拉取到最新
                if len(ohlcv) < limit:
                    break
                    
            except Exception as e:
                print(f"Error fetching data for {symbol}: {e}")
                break

    def _get_last_timestamp(self, symbol: str, timeframe: str) -> Optional[int]:
        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.cursor()
            cursor.execute(
                "SELECT MAX(timestamp) FROM klines WHERE symbol = ? AND timeframe = ?",
                (symbol, timeframe)
            )
            result = cursor.fetchone()
            return result[0] if result and result[0] else None

    def _save_klines(self, symbol: str, timeframe: str, ohlcv: List[List]):
        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.cursor()
            data = [(symbol, timeframe, *row) for row in ohlcv]
            cursor.executemany(
                "INSERT OR IGNORE INTO klines VALUES (?, ?, ?, ?, ?, ?, ?, ?)",
                data
            )
            conn.commit()

    def get_close_prices(self, symbol: str, timeframe: str) -> np.ndarray:
        """获取指定交易对和周期的所有收盘价序列"""
        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.cursor()
            cursor.execute(
                "SELECT close FROM klines WHERE symbol = ? AND timeframe = ? ORDER BY timestamp ASC",
                (symbol, timeframe)
            )
            rows = cursor.fetchall()
            return np.array([row[0] for row in rows], dtype=np.float64)

    def get_ohlcv(self, symbol: str, timeframe: str, 
                   start_ts: int = None, end_ts: int = None) -> np.ndarray:
        """获取完整OHLCV数据，返回 shape=(N, 6) 的数组"""
        query = "SELECT timestamp, open, high, low, close, volume FROM klines WHERE symbol = ? AND timeframe = ?"
        params = [symbol, timeframe]
        
        if start_ts:
            query += " AND timestamp >= ?"
            params.append(start_ts)
        if end_ts:
            query += " AND timestamp <= ?"
            params.append(end_ts)
            
        query += " ORDER BY timestamp ASC"
        
        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.cursor()
            cursor.execute(query, tuple(params))
            rows = cursor.fetchall()
            return np.array(rows, dtype=np.float64)

    def get_timestamps(self, symbol: str, timeframe: str) -> np.ndarray:
        """获取时间戳序列"""
        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.cursor()
            cursor.execute(
                "SELECT timestamp FROM klines WHERE symbol = ? AND timeframe = ? ORDER BY timestamp ASC",
                (symbol, timeframe)
            )
            rows = cursor.fetchall()
            return np.array([row[0] for row in rows], dtype=np.int64)
