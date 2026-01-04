"""
测试价格汇报器
"""
import pytest
from unittest.mock import Mock, AsyncMock, patch

from src.notifier.price_reporter import PriceReporter


class TestPriceReporter:
    """价格汇报器测试"""

    def test_init(self):
        """测试初始化"""
        reporter = PriceReporter()
        assert reporter.bot is None
        assert reporter.user_id is None
        assert reporter.symbols == ['BTC', 'ETH', 'ADA']

    def test_set_bot_none_should_raise(self):
        """测试设置 None bot 应该抛出异常"""
        reporter = PriceReporter()
        with pytest.raises(ValueError, match="Bot cannot be None"):
            reporter.set_bot(None)

    def test_set_bot_success(self):
        """测试成功设置 bot"""
        reporter = PriceReporter()
        mock_bot = Mock()
        reporter.set_bot(mock_bot)
        assert reporter.bot == mock_bot

    def test_set_user(self):
        """测试设置用户 ID"""
        reporter = PriceReporter()
        reporter.set_user(123456)
        assert reporter.user_id == 123456

    def test_start_without_bot_should_raise(self):
        """测试在没有设置 bot 的情况下启动应该抛出异常"""
        reporter = PriceReporter()
        reporter.set_user(123456)
        with pytest.raises(RuntimeError, match="Bot must be set before starting"):
            reporter.start()

    def test_start_without_user_should_return(self):
        """测试在没有设置 user_id 的情况下启动应该返回"""
        reporter = PriceReporter()
        mock_bot = Mock()
        reporter.set_bot(mock_bot)
        # 不应抛出异常
        reporter.start()

    def test_format_report_with_prices(self):
        """测试格式化价格汇报"""
        reporter = PriceReporter()
        prices = [89915.0, 3102.17, 0.8524]
        message = reporter._format_report(prices)

        assert '₿ *BTC*:' in message
        assert '⟠ *ETH*:' in message
        assert '₳ *ADA*:' in message
        assert 'Binance' in message

    def test_format_report_with_error(self):
        """测试格式化含错误的价格汇报"""
        reporter = PriceReporter()
        prices = [89915.0, Exception("API Error"), 0.8524]
        message = reporter._format_report(prices)

        assert '₿ *BTC*:' in message
        assert '❌ 获取失败' in message
        assert '₳ *ADA*:' in message

    @pytest.mark.asyncio
    async def test_send_price_report_without_bot(self):
        """测试在没有 bot 的情况下发送汇报应该跳过"""
        reporter = PriceReporter()
        # 不应抛出异常
        await reporter.send_price_report()

    @pytest.mark.asyncio
    async def test_send_price_report_without_user(self):
        """测试在没有 user_id 的情况下发送汇报应该跳过"""
        reporter = PriceReporter()
        reporter.bot = Mock()
        # 不应抛出异常
        await reporter.send_price_report()


if __name__ == '__main__':
    pytest.main([__file__, '-v'])
