import numpy as np
from dataclasses import dataclass
from typing import List, Optional, Dict, Any, Tuple
from dtaidistance import dtw
from datetime import datetime
from scipy import stats

@dataclass
class MatchResult:
    start_index: int              # 匹配片段在历史数据中的起始索引
    end_index: int                # 匹配片段结束索引
    start_time: str               # 起始时间（人类可读）
    end_time: str                 # 结束时间
    similarity_score: float       # 综合相似度 0-1
    price_similarity: float       # 价格形态相似度
    ema_similarity: float         # EMA相似度
    volume_similarity: float      # 成交量相似度
    volatility_similarity: float  # 波动率相似度
    trend_similarity: float       # 趋势相似度
    
    # 后续走势统计
    future_return_1x: float       # 匹配段后续等长区间的收益率
    future_return_half: float     # 后续半段的收益率
    future_max_drawdown: float    # 后续最大回撤
    future_max_gain: float        # 后续最大涨幅
    future_trend: str             # up/down/sideways
    
    # 序列数据用于绘图
    history_segment: List[float]
    future_segment: List[float]

class PatternMatcher:
    def __init__(self, weights: dict = None):
        self.weights = weights or {
            'price': 0.50,
            'ema': 0.20,
            'volume': 0.15,
            'volatility': 0.10,
            'trend': 0.05
        }
    
    def find_similar_patterns(
        self,
        query_sequence: np.ndarray,       # 归一化的查询价格序列
        historical_ohlcv: np.ndarray,      # 历史OHLCV数据 [timestamp, open, high, low, close, volume]
        historical_timestamps: np.ndarray,  # 历史时间戳
        window_size: int = None,            # 滑动窗口大小
        step: int = None,                   # 滑动步长
        top_n: int = 10,                    # 返回前N个最相似的
        query_ema_state: str = "tangled",   # 查询图表的EMA状态
        query_volume_pattern: str = "normal",# 查询图表的成交量模式
        min_similarity: float = 0.5,        # 最低相似度阈值
        use_pearson_filter: bool = True,    # 使用皮尔逊相关系数预过滤
        pearson_threshold: float = 0.3      # 皮尔逊相关系数阈值
    ) -> List[MatchResult]:
        
        if window_size is None:
            window_size = len(query_sequence)
        if step is None:
            step = max(1, window_size // 4)
            
        query_norm = self._normalize(query_sequence)
        query_volatility = self._calc_volatility(query_sequence)
        query_trend = self._calc_trend_slope(query_sequence)
        
        results = []
        n_hist = len(historical_ohlcv)
        
        # 如果数据量很大，先进行降采样以加速初步扫描
        downsample_factor = 1
        if n_hist > 10000:
            downsample_factor = max(1, n_hist // 5000)
        
        # 滑动窗口遍历
        for i in range(0, n_hist - window_size * 2, step):
            window_ohlcv = historical_ohlcv[i : i + window_size]
            window_closes = window_ohlcv[:, 4]
            window_volumes = window_ohlcv[:, 5]
            
            # 0. 皮尔逊相关系数快速过滤（可选）
            if use_pearson_filter:
                try:
                    corr, _ = stats.pearsonr(query_sequence, window_closes)
                    if abs(corr) < pearson_threshold:
                        continue  # 跳过低相关性的窗口
                except:
                    pass  # 如果计算失败，继续处理
            
            # 1. 价格形态相似度
            window_norm = self._normalize(window_closes)
            dist = dtw.distance_fast(query_norm.astype(np.double), window_norm.astype(np.double))
            price_sim = 1 / (1 + dist)
            
            # 2. EMA相似度
            candidate_ema_state = self._calc_ema_state(window_closes)
            ema_sim = self._calc_ema_similarity(query_ema_state, candidate_ema_state)
            
            # 3. 成交量相似度 (这里简化为成交量趋势对比)
            vol_sim = self._calc_volume_similarity(window_volumes)
            
            # 4. 波动率相似度
            window_volatility = self._calc_volatility(window_closes)
            volatility_sim = 1 - abs(query_volatility - window_volatility) / max(query_volatility, window_volatility, 1e-10)
            
            # 5. 趋势相似度
            window_trend = self._calc_trend_slope(window_closes)
            trend_sim = 1.0 if (query_trend * window_trend > 0) else 0.0
            
            # 综合评分
            total_score = (
                price_sim * self.weights['price'] +
                ema_sim * self.weights['ema'] +
                vol_sim * self.weights['volume'] +
                volatility_sim * self.weights['volatility'] +
                trend_sim * self.weights['trend']
            )
            
            if total_score >= min_similarity:
                # 计算后续走势
                future_stats = self._calc_future_stats(historical_ohlcv[:, 4], i + window_size, window_size)
                
                res = MatchResult(
                    start_index=i,
                    end_index=i + window_size,
                    start_time=datetime.fromtimestamp(historical_timestamps[i]/1000).strftime('%Y-%m-%d %H:%M'),
                    end_time=datetime.fromtimestamp(historical_timestamps[i+window_size]/1000).strftime('%Y-%m-%d %H:%M'),
                    similarity_score=float(total_score),
                    price_similarity=float(price_sim),
                    ema_similarity=float(ema_sim),
                    volume_similarity=float(vol_sim),
                    volatility_similarity=float(volatility_sim),
                    trend_similarity=float(trend_sim),
                    history_segment=window_closes.tolist(),
                    future_segment=historical_ohlcv[i + window_size : i + window_size * 2, 4].tolist(),
                    **future_stats
                )
                results.append(res)
        
        # 排序并去重
        results.sort(key=lambda x: x.similarity_score, reverse=True)
        results = self._remove_overlapping(results, window_size // 2)
        
        return results[:top_n]

    def _normalize(self, seq: np.ndarray) -> np.ndarray:
        min_val, max_val = np.min(seq), np.max(seq)
        if max_val == min_val:
            return np.zeros_like(seq)
        return (seq - min_val) / (max_val - min_val)

    def _ema(self, data: np.ndarray, period: int) -> float:
        if len(data) < period:
            return data[-1]
        alpha = 2 / (period + 1)
        ema = data[0]
        for price in data[1:]:
            ema = (price * alpha) + (ema * (1 - alpha))
        return ema

    def _calc_ema_state(self, closes: np.ndarray) -> str:
        e7 = self._ema(closes, 7)
        e25 = self._ema(closes, 25)
        e99 = self._ema(closes, 99)
        
        if e7 > e25 > e99: return "bullish_aligned"
        if e7 < e25 < e99: return "bearish_aligned"
        
        # 检查最近是否有交叉 (简化判断)
        recent_closes = closes[-10:]
        re7 = self._ema(recent_closes, 7)
        re25 = self._ema(recent_closes, 25)
        if (e7 - e25) * (re7 - re25) < 0: return "crossing"
        
        return "tangled"

    def _calc_ema_similarity(self, query_state: str, candidate_state: str) -> float:
        if query_state == candidate_state: return 1.0
        pairs = {tuple(sorted([query_state, candidate_state])): 0.5}
        return pairs.get(tuple(sorted([query_state, candidate_state])), 0.0)

    def _calc_volume_similarity(self, volumes: np.ndarray) -> float:
        # 简单判断成交量是否在放大
        if len(volumes) < 10: return 0.5
        first_half = np.mean(volumes[:len(volumes)//2])
        second_half = np.mean(volumes[len(volumes)//2:])
        return 1.0 if (second_half > first_half) else 0.5

    def _calc_volatility(self, prices: np.ndarray) -> float:
        returns = np.diff(prices) / (prices[:-1] + 1e-10)
        return float(np.std(returns))

    def _calc_trend_slope(self, prices: np.ndarray) -> float:
        x = np.arange(len(prices))
        slope, _, _, _, _ = stats.linregress(x, prices)
        return float(slope)

    def _remove_overlapping(self, results: List[MatchResult], min_gap: int) -> List[MatchResult]:
        keep = []
        for res in results:
            if not any(abs(res.start_index - k.start_index) < min_gap for k in keep):
                keep.append(res)
        return keep

    def _calc_future_stats(self, all_closes: np.ndarray, start_idx: int, horizon: int) -> dict:
        future = all_closes[start_idx : start_idx + horizon]
        if len(future) == 0:
            return {"future_return_1x": 0, "future_return_half": 0, "future_max_drawdown": 0, "future_max_gain": 0, "future_trend": "unknown"}
        
        start_price = all_closes[start_idx - 1]
        ret_1x = (future[-1] - start_price) / start_price
        
        half_idx = len(future) // 2
        ret_half = (future[half_idx] - start_price) / start_price if half_idx > 0 else ret_1x
        
        # 最大涨跌幅
        max_val = np.max(future)
        min_val = np.min(future)
        max_gain = (max_val - start_price) / start_price
        max_dd = (min_val - start_price) / start_price
        
        trend = "sideways"
        if ret_1x > 0.02: trend = "up"
        elif ret_1x < -0.02: trend = "down"
        
        return {
            "future_return_1x": float(ret_1x),
            "future_return_half": float(ret_half),
            "future_max_drawdown": float(max_dd),
            "future_max_gain": float(max_gain),
            "future_trend": trend
        }
