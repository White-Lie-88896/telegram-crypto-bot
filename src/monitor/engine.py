"""
监控引擎
周期性检查所有监控任务并触发预警
"""
import asyncio
import json
from datetime import datetime, timedelta
from typing import Dict, Optional
from telegram import Bot
from sqlalchemy import select

from config.settings import settings
from src.database.connection import db_manager
from src.database.models import MonitorTask, AlertHistory
from src.exchange.price_api_manager import price_api_manager
from src.monitor.rules.price_threshold import PriceThresholdRule
from src.monitor.rules.percentage_change import PercentageChangeRule
from src.utils.logger import bot_logger


class MonitorEngine:
    """监控引擎"""

    def __init__(self):
        """初始化监控引擎"""
        self.bot: Optional[Bot] = None
        self.running = False
        self.check_interval = settings.CHECK_INTERVAL  # 检查间隔（秒）
        self.tasks_cache: Dict[int, MonitorTask] = {}
        bot_logger.info(f"Monitor engine initialized (check interval: {self.check_interval}s)")

    def set_bot(self, bot: Bot):
        """设置 Bot 实例"""
        if bot is None:
            bot_logger.error("Cannot set None as bot instance")
            raise ValueError("Bot cannot be None")
        self.bot = bot
        bot_logger.info("Bot instance set for monitor engine")

    def _create_rule(self, rule_type: str, rule_config: str):
        """
        创建规则实例

        Args:
            rule_type: 规则类型
            rule_config: 规则配置（JSON字符串）

        Returns:
            规则实例
        """
        try:
            config = json.loads(rule_config)
        except json.JSONDecodeError as e:
            bot_logger.error(f"Invalid JSON in rule_config: {e}")
            raise ValueError(f"Invalid rule configuration JSON: {e}")

        if rule_type == 'PRICE_THRESHOLD':
            return PriceThresholdRule(config)
        elif rule_type == 'PERCENTAGE':
            return PercentageChangeRule(config)
        else:
            raise ValueError(f"Unknown rule type: {rule_type}")

    async def check_task(self, task: MonitorTask):
        """
        检查单个监控任务

        Args:
            task: 监控任务
        """
        try:
            # 检查冷却时间
            if task.last_triggered_at:
                cooldown_end = task.last_triggered_at + timedelta(seconds=task.cooldown_seconds)
                if datetime.utcnow() < cooldown_end:
                    # 仍在冷却期
                    return

            # 获取当前价格（使用多API故障转移）
            current_price = await price_api_manager.get_current_price(task.symbol)

            # 获取API来源
            api_source = price_api_manager.last_api_used or 'Binance'

            # 创建并评估规则
            rule = self._create_rule(task.rule_type, task.rule_config)
            result = await rule.evaluate(current_price, task.symbol)

            # 如果触发，在消息中添加API来源并发送预警
            if result.triggered:
                # 在消息末尾添加API来源信息
                result.message = result.message + f"\n\n💡 _数据来源: {api_source}_"
                await self._send_alert(task, result)

        except Exception as e:
            bot_logger.error(f"Error checking task {task.task_id}: {e}", exc_info=True)

    async def _send_alert(self, task: MonitorTask, result):
        """
        发送预警消息

        Args:
            task: 监控任务
            result: 规则评估结果
        """
        if not self.bot:
            bot_logger.error("Bot not set, cannot send alert")
            return

        try:
            # 发送消息
            await self.bot.send_message(
                chat_id=task.user_id,
                text=result.message,
                parse_mode='Markdown'
            )

            # 更新任务触发时间
            async with db_manager.get_session() as session:
                # 重新获取任务对象以避免 detached instance 错误
                stmt = select(MonitorTask).where(MonitorTask.task_id == task.task_id)
                db_result = await session.execute(stmt)
                db_task = db_result.scalar_one_or_none()

                if db_task:
                    db_task.last_triggered_at = datetime.utcnow()

                    # 记录预警历史
                    alert = AlertHistory(
                        task_id=task.task_id,
                        user_id=task.user_id,
                        symbol=task.symbol,
                        market_type=task.market_type,
                        trigger_price=result.current_value,
                        trigger_value=result.current_value,
                        message=result.message,
                        sent_success=True
                    )
                    session.add(alert)
                    await session.commit()

            bot_logger.info(f"Alert sent for task {task.task_id}, user {task.user_id}, {task.symbol}")

        except Exception as e:
            bot_logger.error(f"Error sending alert for task {task.task_id}: {e}", exc_info=True)

            # 记录失败的预警
            try:
                async with db_manager.get_session() as session:
                    alert = AlertHistory(
                        task_id=task.task_id,
                        user_id=task.user_id,
                        symbol=task.symbol,
                        market_type=task.market_type,
                        trigger_price=result.current_value,
                        trigger_value=result.current_value,
                        message=result.message,
                        sent_success=False
                    )
                    session.add(alert)
                    await session.commit()
            except Exception as log_error:
                bot_logger.error(f"Failed to log alert failure: {log_error}", exc_info=True)

    async def load_active_tasks(self):
        """从数据库加载所有活跃任务"""
        try:
            async with db_manager.get_session() as session:
                stmt = select(MonitorTask).where(MonitorTask.status == 'ACTIVE')
                result = await session.execute(stmt)
                tasks = result.scalars().all()

                self.tasks_cache = {task.task_id: task for task in tasks}
                bot_logger.info(f"Loaded {len(self.tasks_cache)} active monitor tasks")

        except Exception as e:
            bot_logger.error(f"Error loading active tasks: {e}", exc_info=True)
            # 保留现有缓存，不清空
            bot_logger.warning(f"Keeping {len(self.tasks_cache)} tasks from previous load")

    async def run_check_cycle(self):
        """执行一次检查周期"""
        if not self.bot:
            bot_logger.warning("Bot not set, skipping check cycle")
            return

        await self.load_active_tasks()

        if not self.tasks_cache:
            bot_logger.debug("No active tasks to check")
            return

        bot_logger.debug(f"Checking {len(self.tasks_cache)} tasks...")

        # 并发检查所有任务
        check_tasks = [
            self.check_task(task)
            for task in self.tasks_cache.values()
        ]

        await asyncio.gather(*check_tasks, return_exceptions=True)

    async def start(self):
        """启动监控引擎"""
        if self.running:
            bot_logger.warning("Monitor engine is already running")
            return

        if not self.bot:
            bot_logger.error("Cannot start monitor engine: Bot not set")
            raise RuntimeError("Bot must be set before starting monitor engine")

        self.running = True
        bot_logger.info("Monitor engine started")

        try:
            while self.running:
                try:
                    await self.run_check_cycle()
                except Exception as e:
                    bot_logger.error(f"Error in monitor engine cycle: {e}", exc_info=True)

                # 等待下一个周期
                await asyncio.sleep(self.check_interval)
        except asyncio.CancelledError:
            bot_logger.info("Monitor engine task cancelled")
            raise
        finally:
            self.running = False
            bot_logger.info("Monitor engine stopped")

    async def stop(self):
        """停止监控引擎"""
        if not self.running:
            bot_logger.info("Monitor engine is not running")
            return

        self.running = False
        bot_logger.info("Monitor engine stop requested")
        # 等待当前周期完成
        await asyncio.sleep(1)


# 全局监控引擎实例
monitor_engine = MonitorEngine()

__all__ = ['MonitorEngine', 'monitor_engine']
