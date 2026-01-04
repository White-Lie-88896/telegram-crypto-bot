"""
测试监控引擎
"""
import pytest
import asyncio
from unittest.mock import Mock, AsyncMock, patch
from datetime import datetime, timedelta

from src.monitor.engine import MonitorEngine
from src.database.models import MonitorTask
from src.monitor.rules.base import RuleEvaluationResult


class TestMonitorEngine:
    """监控引擎测试"""

    def test_init(self):
        """测试初始化"""
        engine = MonitorEngine()
        assert engine.bot is None
        assert engine.running is False
        assert engine.tasks_cache == {}

    def test_set_bot_none_should_raise(self):
        """测试设置 None bot 应该抛出异常"""
        engine = MonitorEngine()
        with pytest.raises(ValueError, match="Bot cannot be None"):
            engine.set_bot(None)

    def test_set_bot_success(self):
        """测试成功设置 bot"""
        engine = MonitorEngine()
        mock_bot = Mock()
        engine.set_bot(mock_bot)
        assert engine.bot == mock_bot

    def test_create_rule_invalid_json(self):
        """测试无效 JSON 应该抛出异常"""
        engine = MonitorEngine()
        with pytest.raises(ValueError, match="Invalid rule configuration JSON"):
            engine._create_rule('PRICE_THRESHOLD', 'invalid json')

    def test_create_rule_unknown_type(self):
        """测试未知规则类型应该抛出异常"""
        engine = MonitorEngine()
        with pytest.raises(ValueError, match="Unknown rule type"):
            engine._create_rule('UNKNOWN', '{}')

    def test_create_rule_price_threshold(self):
        """测试创建价格阈值规则"""
        engine = MonitorEngine()
        rule = engine._create_rule('PRICE_THRESHOLD', '{"threshold_high": 50000}')
        assert rule is not None
        assert rule.threshold_high == 50000

    def test_create_rule_percentage(self):
        """测试创建百分比规则"""
        engine = MonitorEngine()
        rule = engine._create_rule('PERCENTAGE', '{"reference_price": 90000, "percentage_high": 5, "percentage_low": -5}')
        assert rule is not None
        assert rule.reference_price == 90000

    @pytest.mark.asyncio
    async def test_start_without_bot_should_raise(self):
        """测试在没有设置 bot 的情况下启动应该抛出异常"""
        engine = MonitorEngine()
        with pytest.raises(RuntimeError, match="Bot must be set before starting"):
            await engine.start()

    @pytest.mark.asyncio
    async def test_run_check_cycle_without_bot(self):
        """测试在没有 bot 的情况下运行检查周期应该跳过"""
        engine = MonitorEngine()
        # 应该不抛出异常，只是跳过
        await engine.run_check_cycle()

    @pytest.mark.asyncio
    async def test_stop_when_not_running(self):
        """测试停止未运行的引擎"""
        engine = MonitorEngine()
        # 应该不抛出异常
        await engine.stop()

    @pytest.mark.asyncio
    async def test_check_task_in_cooldown(self):
        """测试冷却期内的任务不应触发"""
        engine = MonitorEngine()
        engine.bot = Mock()

        # 创建刚触发过的任务
        task = MonitorTask(
            task_id=1,
            user_id=123,
            symbol='BTC',
            market_type='SPOT',
            rule_type='PRICE_THRESHOLD',
            rule_config='{"threshold_high": 50000}',
            status='ACTIVE',
            cooldown_seconds=300,
            last_triggered_at=datetime.utcnow()  # 刚触发
        )

        # 应该不会发送警报
        with patch('src.monitor.engine.cryptocompare_client.get_current_price', new_callable=AsyncMock) as mock_price:
            await engine.check_task(task)
            mock_price.assert_not_called()


if __name__ == '__main__':
    pytest.main([__file__, '-v'])
