"""
测试监控规则
"""
import pytest

from src.monitor.rules.price_threshold import PriceThresholdRule
from src.monitor.rules.percentage_change import PercentageChangeRule


class TestPriceThresholdRule:
    """价格阈值规则测试"""

    def test_init_without_thresholds_should_raise(self):
        """测试没有阈值应该抛出异常"""
        with pytest.raises(ValueError, match="Must specify at least one threshold"):
            PriceThresholdRule({})

    def test_init_with_high_threshold(self):
        """测试初始化上限阈值"""
        rule = PriceThresholdRule({'threshold_high': 50000})
        assert rule.threshold_high == 50000
        assert rule.threshold_low is None

    def test_init_with_low_threshold(self):
        """测试初始化下限阈值"""
        rule = PriceThresholdRule({'threshold_low': 40000})
        assert rule.threshold_low == 40000
        assert rule.threshold_high is None

    def test_init_with_both_thresholds(self):
        """测试初始化上下限阈值"""
        rule = PriceThresholdRule({'threshold_high': 50000, 'threshold_low': 40000})
        assert rule.threshold_high == 50000
        assert rule.threshold_low == 40000

    @pytest.mark.asyncio
    async def test_evaluate_above_high_threshold(self):
        """测试价格超过上限"""
        rule = PriceThresholdRule({'threshold_high': 50000})
        result = await rule.evaluate(51000, 'BTC')

        assert result.triggered is True
        assert 'BTC' in result.message
        assert '51,000' in result.message
        assert '50,000' in result.message

    @pytest.mark.asyncio
    async def test_evaluate_below_high_threshold(self):
        """测试价格未超过上限"""
        rule = PriceThresholdRule({'threshold_high': 50000})
        result = await rule.evaluate(49000, 'BTC')

        assert result.triggered is False

    @pytest.mark.asyncio
    async def test_evaluate_below_low_threshold(self):
        """测试价格低于下限"""
        rule = PriceThresholdRule({'threshold_low': 40000})
        result = await rule.evaluate(39000, 'BTC')

        assert result.triggered is True
        assert 'BTC' in result.message
        assert '39,000' in result.message
        assert '40,000' in result.message

    @pytest.mark.asyncio
    async def test_evaluate_above_low_threshold(self):
        """测试价格未低于下限"""
        rule = PriceThresholdRule({'threshold_low': 40000})
        result = await rule.evaluate(41000, 'BTC')

        assert result.triggered is False

    def test_get_description(self):
        """测试获取规则描述"""
        rule = PriceThresholdRule({'threshold_high': 50000, 'threshold_low': 40000})
        desc = rule.get_description()

        assert '50,000' in desc
        assert '40,000' in desc


class TestPercentageChangeRule:
    """百分比涨跌规则测试"""

    def test_init_without_reference_price_should_raise(self):
        """测试没有参考价格应该抛出异常"""
        with pytest.raises(ValueError, match="reference_price is required"):
            PercentageChangeRule({})

    def test_init_without_percentage_thresholds_should_raise(self):
        """测试没有百分比阈值应该抛出异常"""
        with pytest.raises(ValueError, match="Must specify at least one percentage threshold"):
            PercentageChangeRule({'reference_price': 90000})

    def test_init_with_high_percentage(self):
        """测试初始化上涨百分比"""
        rule = PercentageChangeRule({
            'reference_price': 90000,
            'percentage_high': 5
        })
        assert rule.reference_price == 90000
        assert rule.percentage_high == 5
        assert rule.percentage_low is None

    def test_init_with_low_percentage(self):
        """测试初始化下跌百分比"""
        rule = PercentageChangeRule({
            'reference_price': 90000,
            'percentage_low': -5
        })
        assert rule.reference_price == 90000
        assert rule.percentage_low == -5
        assert rule.percentage_high is None

    @pytest.mark.asyncio
    async def test_evaluate_above_high_percentage(self):
        """测试涨幅超过上限"""
        rule = PercentageChangeRule({
            'reference_price': 90000,
            'percentage_high': 5
        })
        result = await rule.evaluate(95000, 'BTC')  # 涨幅约 5.56%

        assert result.triggered is True
        assert 'BTC' in result.message
        assert '95,000' in result.message
        assert '90,000' in result.message

    @pytest.mark.asyncio
    async def test_evaluate_below_high_percentage(self):
        """测试涨幅未超过上限"""
        rule = PercentageChangeRule({
            'reference_price': 90000,
            'percentage_high': 5
        })
        result = await rule.evaluate(91000, 'BTC')  # 涨幅约 1.11%

        assert result.triggered is False

    @pytest.mark.asyncio
    async def test_evaluate_below_low_percentage(self):
        """测试跌幅超过下限"""
        rule = PercentageChangeRule({
            'reference_price': 90000,
            'percentage_low': -5
        })
        result = await rule.evaluate(85000, 'BTC')  # 跌幅约 -5.56%

        assert result.triggered is True
        assert 'BTC' in result.message
        assert '85,000' in result.message
        assert '90,000' in result.message

    @pytest.mark.asyncio
    async def test_evaluate_above_low_percentage(self):
        """测试跌幅未超过下限"""
        rule = PercentageChangeRule({
            'reference_price': 90000,
            'percentage_low': -5
        })
        result = await rule.evaluate(89000, 'BTC')  # 跌幅约 -1.11%

        assert result.triggered is False

    def test_get_description(self):
        """测试获取规则描述"""
        rule = PercentageChangeRule({
            'reference_price': 90000,
            'percentage_high': 5,
            'percentage_low': -5
        })
        desc = rule.get_description()

        assert '90,000' in desc
        assert '5%' in desc


if __name__ == '__main__':
    pytest.main([__file__, '-v'])
