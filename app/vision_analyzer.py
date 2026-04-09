import base64
import json
import os
import logging
from pathlib import Path
from typing import Optional, Dict, Any, List
import httpx

logger = logging.getLogger(__name__)

CHART_ANALYSIS_PROMPT = """
你是一个专业的加密货币K线图分析器。请仔细观察这张K线图截图，提取以下信息并以严格的JSON格式返回，不要返回任何其他内容：

{
  "symbol": "交易对，如 BTC/USDT，如果无法确定写 UNKNOWN",
  "timeframe": "K线周期，如 1m/5m/15m/30m/1h/4h/1d/1w，如果无法确定写 UNKNOWN",
  "candle_count": "截图中大约有多少根K线，整数",
  "pattern": {
    "trend": "整体趋势: uptrend/downtrend/sideways/reversal_up/reversal_down",
    "recent_trend": "最近10-20根K线的趋势: up/down/sideways",
    "volatility": "波动性: low/medium/high",
    "key_patterns": ["识别到的形态，如: double_top, head_shoulders, triangle, wedge, channel, flag, cup_handle, consolidation, breakout, breakdown 等"]
  },
  "indicators": {
    "ema_arrangement": "EMA/MA排列状态: bullish_aligned(多头排列)/bearish_aligned(空头排列)/tangled(缠绕)/crossing(交叉中)",
    "ema_cross_signal": "最近是否有EMA交叉: golden_cross/death_cross/none",
    "price_vs_ema": "价格相对于主要EMA的位置: above_all/below_all/between",
    "volume_pattern": "成交量模式: increasing/decreasing/spike/normal/unknown"
  },
  "price_structure": {
    "recent_high_position": "近期高点在截图中的相对位置(0-1，0=最左，1=最右)",
    "recent_low_position": "近期低点在截图中的相对位置(0-1)",
    "price_range_percent": "截图中价格波动幅度百分比估算",
    "current_position_in_range": "当前价格在整个截图价格区间的位置(0=最低,1=最高)"
  },
  "normalized_price_sequence": [
    "将截图中的K线收盘价走势归一化为0-1之间的序列",
    "采样约30-50个点，均匀分布",
    "例如: [0.2, 0.25, 0.3, 0.28, ...]",
    "这是最关键的数据，请尽可能准确"
  ],
  "confidence": "你对以上分析的置信度: 0-100"
}

注意事项：
1. normalized_price_sequence 是最重要的字段，请仔细观察K线走势，提取尽可能准确的归一化价格序列
2. 如果图表中有明确的EMA/MA线，请仔细观察它们的排列和交叉情况
3. 如果某些信息无法从截图中确定，请如实标注为 UNKNOWN
4. 只返回JSON，不要有任何额外文字
"""

class ChartVisionAnalyzer:
    """使用 DeepSeek API 进行 K 线图表视觉分析"""
    
    def __init__(self, api_key: Optional[str] = None):
        """
        初始化视觉分析器
        
        Args:
            api_key: DeepSeek API 密钥，如果不提供则从环境变量获取
        """
        self.api_key = api_key or os.environ.get("DEEPSEEK_API_KEY")
        if not self.api_key:
            raise ValueError("DEEPSEEK_API_KEY not found in environment variables")
        
        self.api_url = "https://api.deepseek.com/chat/completions"
        self.model = "deepseek-vision"
        self.timeout = 60.0
    
    async def analyze_chart(self, image_path: str = None, image_bytes: bytes = None) -> Dict[str, Any]:
        """
        分析K线截图，返回结构化特征数据
        
        Args:
            image_path: 图片文件路径
            image_bytes: 图片字节数据
            
        Returns:
            包含分析结果的字典
            
        Raises:
            ValueError: 如果没有提供图片数据
            Exception: 如果 API 调用失败
        """
        if image_path:
            with open(image_path, "rb") as f:
                image_bytes = f.read()
        
        if not image_bytes:
            raise ValueError("No image data provided")

        base64_image = base64.b64encode(image_bytes).decode("utf-8")
        
        try:
            # 调用 DeepSeek API
            async with httpx.AsyncClient(timeout=self.timeout) as client:
                response = await client.post(
                    self.api_url,
                    json={
                        "model": self.model,
                        "messages": [
                            {
                                "role": "user",
                                "content": [
                                    {
                                        "type": "text",
                                        "text": CHART_ANALYSIS_PROMPT
                                    },
                                    {
                                        "type": "image_url",
                                        "image_url": {
                                            "url": f"data:image/jpeg;base64,{base64_image}"
                                        }
                                    }
                                ]
                            }
                        ],
                        "max_tokens": 2048,
                        "temperature": 0.3  # 降低温度以获得更稳定的结果
                    },
                    headers={
                        "Authorization": f"Bearer {self.api_key}",
                        "Content-Type": "application/json"
                    }
                )
                
                if response.status_code != 200:
                    logger.error(f"DeepSeek API error: {response.status_code} - {response.text}")
                    raise Exception(f"DeepSeek API returned {response.status_code}")
                
                result = response.json()
                content = result["choices"][0]["message"]["content"]
                
                # 解析 JSON 响应
                analysis = self._parse_response(content)
                return analysis
                
        except json.JSONDecodeError as e:
            logger.error(f"Failed to parse JSON response: {e}")
            raise Exception(f"Invalid JSON response from DeepSeek API: {e}")
        except Exception as e:
            logger.error(f"Vision analysis error: {e}")
            raise

    def _parse_response(self, content: str) -> Dict[str, Any]:
        """
        解析 API 响应并验证字段
        
        Args:
            content: API 返回的文本内容
            
        Returns:
            验证后的分析结果字典
        """
        # 尝试提取 JSON（可能包含额外文本）
        json_match = content.find('{')
        if json_match == -1:
            raise ValueError("No JSON found in response")
        
        json_str = content[json_match:]
        # 找到匹配的闭合括号
        brace_count = 0
        for i, char in enumerate(json_str):
            if char == '{':
                brace_count += 1
            elif char == '}':
                brace_count -= 1
                if brace_count == 0:
                    json_str = json_str[:i+1]
                    break
        
        data = json.loads(json_str)
        return self._validate_analysis(data)

    def _validate_analysis(self, data: Dict[str, Any]) -> Dict[str, Any]:
        """
        验证和修正分析结果
        
        Args:
            data: 原始分析数据
            
        Returns:
            验证后的数据
        """
        # 确保必要字段存在
        required_fields = ["symbol", "timeframe", "normalized_price_sequence", "confidence"]
        for field in required_fields:
            if field not in data:
                logger.warning(f"Missing field: {field}")
                if field == "normalized_price_sequence":
                    data[field] = []
                elif field == "confidence":
                    data[field] = 50
                else:
                    data[field] = "UNKNOWN"
        
        # 验证 normalized_price_sequence
        if isinstance(data["normalized_price_sequence"], list):
            # 过滤非数字元素
            prices = []
            for p in data["normalized_price_sequence"]:
                try:
                    prices.append(float(p))
                except (ValueError, TypeError):
                    pass
            data["normalized_price_sequence"] = prices
        else:
            data["normalized_price_sequence"] = []
        
        # 确保价格序列不为空
        if not data["normalized_price_sequence"]:
            logger.warning("Empty price sequence, using default")
            data["normalized_price_sequence"] = [0.5] * 30
        
        # 验证置信度
        try:
            confidence = int(data["confidence"])
            data["confidence"] = max(0, min(100, confidence))
        except (ValueError, TypeError):
            data["confidence"] = 50
        
        # 确保指标字段存在
        if "indicators" not in data:
            data["indicators"] = {}
        if "pattern" not in data:
            data["pattern"] = {}
        if "price_structure" not in data:
            data["price_structure"] = {}
        
        return data
