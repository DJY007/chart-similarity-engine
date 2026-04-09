import numpy as np
from dataclasses import dataclass
from typing import List
from .pattern_matcher import MatchResult

@dataclass
class PredictionSummary:
    total_matches: int
    avg_similarity: float
    
    # 后续走势统计
    bullish_count: int          # 后续上涨的匹配数
    bearish_count: int          # 后续下跌的匹配数
    neutral_count: int          # 后续横盘的匹配数
    bullish_probability: float  # 上涨概率
    
    avg_future_return: float    # 平均后续收益率
    median_future_return: float # 中位数后续收益率
    avg_max_gain: float         # 平均最大涨幅
    avg_max_drawdown: float     # 平均最大回撤
    
    confidence: str             # low/medium/high
    suggestion: str             # 简要建议文字


class ResultAnalyzer:
    def summarize(self, matches: List[MatchResult]) -> PredictionSummary:
        """汇总所有匹配结果，生成预测摘要"""
        if not matches:
            return self._get_empty_summary()
            
        total = len(matches)
        avg_sim = float(np.mean([m.similarity_score for m in matches]))
        
        returns = [m.future_return_1x for m in matches]
        max_gains = [m.future_max_gain for m in matches]
        max_dds = [m.future_max_drawdown for m in matches]
        
        bullish = sum(1 for r in returns if r > 0.01) # 涨幅超过1%
        bearish = sum(1 for r in returns if r < -0.01) # 跌幅超过1%
        neutral = total - bullish - bearish
        
        bull_prob = (bullish / total) * 100 if total > 0 else 0
        
        # 置信度逻辑
        confidence = "low"
        if total >= 5:
            if bull_prob >= 70 or bull_prob <= 30:
                confidence = "high"
            elif bull_prob >= 60 or bull_prob <= 40:
                confidence = "medium"
        elif total >= 3:
            if bull_prob >= 60 or bull_prob <= 40:
                confidence = "medium"
        
        # 建议文字
        suggestion = "观望为主，形态一致性较低。"
        if confidence == "high":
            suggestion = "强烈看涨，历史相似走势后续表现强劲。" if bull_prob >= 70 else "强烈看跌，历史相似走势后续表现疲软。"
        elif confidence == "medium":
            suggestion = "倾向于看涨，建议轻仓尝试。" if bull_prob >= 60 else "倾向于看跌，注意风险控制。"
            
        return PredictionSummary(
            total_matches=total,
            avg_similarity=avg_sim,
            bullish_count=bullish,
            bearish_count=bearish,
            neutral_count=neutral,
            bullish_probability=float(bull_prob),
            avg_future_return=float(np.mean(returns)),
            median_future_return=float(np.median(returns)),
            avg_max_gain=float(np.mean(max_gains)),
            avg_max_drawdown=float(np.mean(max_dds)),
            confidence=confidence,
            suggestion=suggestion
        )

    def _get_empty_summary(self) -> PredictionSummary:
        return PredictionSummary(
            total_matches=0,
            avg_similarity=0,
            bullish_count=0,
            bearish_count=0,
            neutral_count=0,
            bullish_probability=0,
            avg_future_return=0,
            median_future_return=0,
            avg_max_gain=0,
            avg_max_drawdown=0,
            confidence="low",
            suggestion="未找到足够相似的历史走势。"
        )
