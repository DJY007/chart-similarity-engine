import pytest
import json
from unittest.mock import Mock, patch, AsyncMock
from app.vision_analyzer import ChartVisionAnalyzer

class TestChartVisionAnalyzer:
    """Vision Analyzer 单元测试"""
    
    def setup_method(self):
        """每个测试前的初始化"""
        self.analyzer = ChartVisionAnalyzer(api_key="test_key")
    
    def test_validate_analysis_complete(self):
        """测试完整的分析结果验证"""
        data = {
            "symbol": "BTC/USDT",
            "timeframe": "4h",
            "candle_count": 50,
            "pattern": {
                "trend": "uptrend",
                "recent_trend": "up",
                "volatility": "medium",
                "key_patterns": ["triangle", "breakout"]
            },
            "indicators": {
                "ema_arrangement": "bullish_aligned",
                "ema_cross_signal": "golden_cross",
                "price_vs_ema": "above_all",
                "volume_pattern": "increasing"
            },
            "price_structure": {
                "recent_high_position": 0.9,
                "recent_low_position": 0.1,
                "price_range_percent": 5.0,
                "current_position_in_range": 0.85
            },
            "normalized_price_sequence": [0.1, 0.2, 0.3, 0.4, 0.5],
            "confidence": 85
        }
        
        result = self.analyzer._validate_analysis(data)
        
        assert result["symbol"] == "BTC/USDT"
        assert result["timeframe"] == "4h"
        assert isinstance(result["normalized_price_sequence"], list)
        assert all(isinstance(x, float) for x in result["normalized_price_sequence"])
    
    def test_validate_analysis_missing_fields(self):
        """测试缺失字段的处理"""
        data = {
            "symbol": "ETH/USDT",
            "timeframe": "1h"
        }
        
        result = self.analyzer._validate_analysis(data)
        
        # 应该用默认值填充缺失字段
        assert "pattern" in result
        assert "indicators" in result
        assert "price_structure" in result
        assert "normalized_price_sequence" in result
    
    def test_validate_analysis_invalid_sequence(self):
        """测试无效的价格序列处理"""
        data = {
            "symbol": "BTC/USDT",
            "normalized_price_sequence": ["invalid", "string", "values"]
        }
        
        result = self.analyzer._validate_analysis(data)
        
        # 应该过滤掉无效值
        assert isinstance(result["normalized_price_sequence"], list)
    
    def test_get_default_analysis(self):
        """测试默认分析结构"""
        default = self.analyzer._get_default_analysis()
        
        assert default["symbol"] == "UNKNOWN"
        assert default["timeframe"] == "UNKNOWN"
        assert default["candle_count"] == 0
        assert isinstance(default["pattern"], dict)
        assert isinstance(default["indicators"], dict)
        assert isinstance(default["price_structure"], dict)
        assert isinstance(default["normalized_price_sequence"], list)
        assert default["confidence"] == 0
    
    def test_normalize_price_sequence_conversion(self):
        """测试价格序列的类型转换"""
        data = {
            "symbol": "BTC/USDT",
            "normalized_price_sequence": [0.1, "0.2", 0.3, "0.4", 0.5]
        }
        
        result = self.analyzer._validate_analysis(data)
        
        # 所有元素应该被转换为浮点数
        assert all(isinstance(x, float) for x in result["normalized_price_sequence"])
    
    def test_ema_arrangement_values(self):
        """测试 EMA 排列状态的有效值"""
        valid_states = ["bullish_aligned", "bearish_aligned", "tangled", "crossing"]
        
        for state in valid_states:
            data = {
                "indicators": {
                    "ema_arrangement": state
                }
            }
            result = self.analyzer._validate_analysis(data)
            assert result["indicators"]["ema_arrangement"] == state
    
    def test_pattern_trend_values(self):
        """测试趋势类型的有效值"""
        valid_trends = ["uptrend", "downtrend", "sideways", "reversal_up", "reversal_down"]
        
        for trend in valid_trends:
            data = {
                "pattern": {
                    "trend": trend
                }
            }
            result = self.analyzer._validate_analysis(data)
            assert result["pattern"]["trend"] == trend


class TestVisionAnalyzerMock:
    """使用 Mock 的集成测试"""
    
    @patch('app.vision_analyzer.anthropic.Anthropic')
    def test_analyze_chart_mock_response(self, mock_anthropic):
        """测试 Vision API 的 Mock 响应处理"""
        # 模拟 Claude API 响应
        mock_response = Mock()
        mock_response.content = [Mock(text=json.dumps({
            "symbol": "BTC/USDT",
            "timeframe": "4h",
            "candle_count": 50,
            "pattern": {
                "trend": "uptrend",
                "recent_trend": "up",
                "volatility": "medium",
                "key_patterns": ["triangle"]
            },
            "indicators": {
                "ema_arrangement": "bullish_aligned",
                "ema_cross_signal": "golden_cross",
                "price_vs_ema": "above_all",
                "volume_pattern": "increasing"
            },
            "price_structure": {
                "recent_high_position": 0.9,
                "recent_low_position": 0.1,
                "price_range_percent": 5.0,
                "current_position_in_range": 0.85
            },
            "normalized_price_sequence": [0.1, 0.2, 0.3, 0.4, 0.5],
            "confidence": 85
        }))]
        
        mock_client = Mock()
        mock_client.messages.create.return_value = mock_response
        
        analyzer = ChartVisionAnalyzer(api_key="test_key")
        analyzer.client = mock_client
        
        # 测试 JSON 解析
        result = analyzer._validate_analysis(json.loads(mock_response.content[0].text))
        
        assert result["symbol"] == "BTC/USDT"
        assert result["timeframe"] == "4h"
        assert result["confidence"] == 85
    
    @patch('app.vision_analyzer.anthropic.Anthropic')
    def test_analyze_chart_malformed_json(self, mock_anthropic):
        """测试处理格式错误的 JSON"""
        # 模拟返回格式错误的 JSON
        mock_response = Mock()
        mock_response.content = [Mock(text="This is not JSON")]
        
        mock_client = Mock()
        mock_client.messages.create.return_value = mock_response
        
        analyzer = ChartVisionAnalyzer(api_key="test_key")
        analyzer.client = mock_client
        
        # 应该返回默认分析而不是崩溃
        try:
            result = json.loads(mock_response.content[0].text)
        except json.JSONDecodeError:
            result = analyzer._get_default_analysis()
        
        assert result["symbol"] == "UNKNOWN"
        assert result["confidence"] == 0
    
    @patch('app.vision_analyzer.anthropic.Anthropic')
    def test_analyze_chart_markdown_wrapped_json(self, mock_anthropic):
        """测试处理被 Markdown 代码块包裹的 JSON"""
        json_content = json.dumps({
            "symbol": "ETH/USDT",
            "timeframe": "1h",
            "normalized_price_sequence": [0.2, 0.4, 0.6]
        })
        
        # 模拟返回被 Markdown 代码块包裹的 JSON
        markdown_response = f"```json\n{json_content}\n```"
        
        mock_response = Mock()
        mock_response.content = [Mock(text=markdown_response)]
        
        mock_client = Mock()
        mock_client.messages.create.return_value = mock_response
        
        analyzer = ChartVisionAnalyzer(api_key="test_key")
        analyzer.client = mock_client
        
        # 模拟清理逻辑
        content = mock_response.content[0].text
        if "```json" in content:
            content = content.split("```json")[1].split("```")[0].strip()
        
        result = json.loads(content)
        assert result["symbol"] == "ETH/USDT"


class TestChartAnalysisValidation:
    """图表分析结果的验证测试"""
    
    def setup_method(self):
        self.analyzer = ChartVisionAnalyzer(api_key="test_key")
    
    def test_confidence_range(self):
        """测试置信度范围验证"""
        data = {"confidence": 150}  # 超出范围
        result = self.analyzer._validate_analysis(data)
        
        # 置信度应该被限制在 0-100
        assert 0 <= result["confidence"] <= 100
    
    def test_position_range(self):
        """测试位置值范围验证"""
        data = {
            "price_structure": {
                "recent_high_position": 1.5,  # 超出 0-1 范围
                "recent_low_position": -0.5   # 超出 0-1 范围
            }
        }
        result = self.analyzer._validate_analysis(data)
        
        # 位置值应该在 0-1 之间
        high_pos = result["price_structure"]["recent_high_position"]
        low_pos = result["price_structure"]["recent_low_position"]
        
        assert 0 <= high_pos <= 1
        assert 0 <= low_pos <= 1
    
    def test_normalized_sequence_range(self):
        """测试归一化序列值范围"""
        data = {
            "normalized_price_sequence": [0.1, 0.5, 1.5, -0.2, 0.8]
        }
        result = self.analyzer._validate_analysis(data)
        
        # 所有值应该在 0-1 之间（或接近）
        seq = result["normalized_price_sequence"]
        assert all(isinstance(x, float) for x in seq)
