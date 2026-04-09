import numpy as np
from dtaidistance import dtw
from typing import List, Dict, Any, Tuple
from datetime import datetime

class PatternMatcher:
    def __init__(self, data_manager):
        self.data_manager = data_manager

    def find_matches(self, 
                     target_sequence: List[float], 
                     symbol: str, 
                     timeframe: str, 
                     top_n: int = 5,
                     prediction_horizon: int = 20) -> Dict[str, Any]:
        """
        在历史数据中寻找最相似的走势
        """
        # 1. 获取历史收盘价
        history_prices = self.data_manager.get_close_prices(symbol, timeframe)
        if len(history_prices) < len(target_sequence) + prediction_horizon:
            return {"error": "Insufficient historical data"}

        target_seq = np.array(target_sequence, dtype=np.float64)
        window_size = len(target_seq)
        
        # 2. 滑动窗口扫描
        scores = []
        # 为了性能，我们可以增加步长，或者只扫描最近的一部分数据
        # 这里我们全量扫描，但跳过重叠过多的窗口
        step = max(1, window_size // 4) 
        
        for i in range(0, len(history_prices) - window_size - prediction_horizon, step):
            window = history_prices[i : i + window_size]
            
            # 归一化窗口数据到 0-1
            min_val = np.min(window)
            max_val = np.max(window)
            if max_val == min_val:
                continue
            norm_window = (window - min_val) / (max_val - min_val)
            
            # 计算 DTW 距离
            distance = dtw.distance_fast(target_seq, norm_window)
            scores.append((distance, i))

        # 3. 排序并取 Top N
        scores.sort(key=lambda x: x[0])
        
        # 过滤掉时间上太接近的重复匹配
        unique_matches = []
        used_indices = set()
        for dist, idx in scores:
            if any(abs(idx - used_idx) < window_size for used_idx in used_indices):
                continue
            unique_matches.append((dist, idx))
            used_indices.add(idx)
            if len(unique_matches) >= top_n:
                break

        # 4. 分析后续走势
        results = []
        future_returns = []
        
        timestamps = self.data_manager.get_timestamps(symbol, timeframe)
        
        for dist, idx in unique_matches:
            # 获取匹配段之后的数据
            future_segment = history_prices[idx + window_size : idx + window_size + prediction_horizon]
            start_price = history_prices[idx + window_size - 1]
            end_price = future_segment[-1]
            
            price_change_pct = (end_price - start_price) / start_price * 100
            future_returns.append(price_change_pct)
            
            results.append({
                "timestamp": int(timestamps[idx]),
                "datetime": datetime.fromtimestamp(timestamps[idx]/1000).strftime('%Y-%m-%d %H:%M'),
                "distance": float(dist),
                "price_change_pct": float(price_change_pct),
                "history_segment": history_prices[idx : idx + window_size].tolist(),
                "future_segment": future_segment.tolist()
            })

        # 5. 统计概率
        up_count = sum(1 for r in future_returns if r > 0)
        down_count = sum(1 for r in future_returns if r < 0)
        total = len(future_returns)
        
        stats = {
            "win_rate": (up_count / total * 100) if total > 0 else 0,
            "avg_return": float(np.mean(future_returns)) if total > 0 else 0,
            "max_drawdown": float(np.min(future_returns)) if total > 0 else 0,
            "max_gain": float(np.max(future_returns)) if total > 0 else 0
        }

        return {
            "matches": results,
            "stats": stats,
            "target_sequence": target_sequence
        }
