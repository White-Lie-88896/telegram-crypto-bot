"""
定时价格汇报模块
支持用户自定义汇报间隔和币种
"""
import asyncio
from datetime import datetime
from typing import Dict, List
from apscheduler.schedulers.asyncio import AsyncIOScheduler
from telegram import Bot
from sqlalchemy import select

from config.settings import settings
from src.exchange.price_api_manager import price_api_manager
from src.database.connection import db_manager
from src.database.models import ReportConfig
from src.utils.logger import bot_logger


class PriceReporter:
    """定时价格汇报器 - 支持多用户动态配置"""

    def __init__(self):
        """初始化汇报器"""
        self.scheduler = AsyncIOScheduler()
        self.bot: Bot = None
        self.active_jobs: Dict[int, str] = {}  # user_id -> job_id 映射

        bot_logger.info("Price reporter initialized")

    def set_bot(self, bot: Bot):
        """设置 Bot 实例"""
        if bot is None:
            bot_logger.error("Cannot set None as bot instance")
            raise ValueError("Bot cannot be None")
        self.bot = bot
        bot_logger.info("Bot instance set for price reporter")

    async def load_and_start_all_reports(self):
        """从数据库加载所有启用的汇报配置并启动"""
        try:
            async with db_manager.get_session() as session:
                stmt = select(ReportConfig).where(ReportConfig.enabled == True)
                result = await session.execute(stmt)
                configs = result.scalars().all()

                for config in configs:
                    await self.add_user_report(
                        user_id=config.user_id,
                        interval_minutes=config.interval_minutes,
                        symbols=config.get_symbols_list()
                    )

            bot_logger.info(f"Loaded and started {len(configs)} price reports")

        except Exception as e:
            bot_logger.error(f"Error loading report configs: {e}", exc_info=True)

    async def add_user_report(self, user_id: int, interval_minutes: int, symbols: List[str]):
        """
        为用户添加定时汇报任务

        Args:
            user_id: 用户ID
            interval_minutes: 汇报间隔（分钟）
            symbols: 币种列表
        """
        try:
            # 如果已存在该用户的任务，先移除
            await self.remove_user_report(user_id)

            job_id = f'price_report_{user_id}'

            # 添加定时任务
            self.scheduler.add_job(
                self._send_user_report,
                'interval',
                minutes=interval_minutes,
                id=job_id,
                replace_existing=True,
                args=[user_id, symbols]
            )

            self.active_jobs[user_id] = job_id
            bot_logger.info(f"Added price report job for user {user_id}: {interval_minutes}min, {symbols}")

        except Exception as e:
            bot_logger.error(f"Error adding user report for {user_id}: {e}", exc_info=True)

    async def remove_user_report(self, user_id: int):
        """
        移除用户的定时汇报任务

        Args:
            user_id: 用户ID
        """
        try:
            job_id = self.active_jobs.get(user_id)
            if job_id:
                self.scheduler.remove_job(job_id)
                del self.active_jobs[user_id]
                bot_logger.info(f"Removed price report job for user {user_id}")
        except Exception as e:
            bot_logger.error(f"Error removing user report for {user_id}: {e}", exc_info=True)

    async def _send_user_report(self, user_id: int, symbols: List[str]):
        """
        发送价格汇报给指定用户

        Args:
            user_id: 用户ID
            symbols: 币种列表
        """
        if not self.bot:
            bot_logger.warning("Bot not set, skipping price report")
            return

        try:
            bot_logger.info(f"Sending price report to user {user_id} for {symbols}")

            # 并发获取所有价格（使用多API故障转移）
            prices = await price_api_manager.get_multiple_prices(symbols)

            # 获取API来源
            api_source = price_api_manager.last_api_used or 'Binance'

            # 构建汇报消息
            message = self._format_report(symbols, prices, api_source)

            # 发送消息
            await self.bot.send_message(
                chat_id=user_id,
                text=message,
                parse_mode='Markdown'
            )

            bot_logger.info(f"Price report sent successfully to user {user_id}")

        except Exception as e:
            bot_logger.error(f"Error sending price report to user {user_id}: {e}", exc_info=True)

    def _format_report(self, symbols: List[str], prices: Dict[str, float], api_source: str = 'Binance') -> str:
        """
        格式化价格汇报消息

        Args:
            symbols: 币种列表
            prices: 币种价格字典 {symbol: price}
            api_source: API数据来源

        Returns:
            格式化的消息
        """
        now = datetime.now()
        time_str = now.strftime("%H:%M:%S")

        # 表情符号映射
        emoji_map = {
            'BTC': '₿',
            'ETH': '⟠',
            'ADA': '₳',
            'SOL': '◎',
            'BNB': '🔶'
        }

        # 构建消息
        lines = [
            "┌─────────────────────────┐",
            f"│  📊 *价格汇报* `{time_str}`  │",
            "└─────────────────────────┘",
            ""
        ]

        for symbol in symbols:
            price = prices.get(symbol)
            emoji = emoji_map.get(symbol, '•')

            if price is None:
                lines.append(f"{emoji} *{symbol}*: ❌ 获取失败")
            else:
                # 格式化价格
                if price >= 1000:
                    price_str = f"${price:,.2f}"
                elif price >= 1:
                    price_str = f"${price:.4f}"
                else:
                    price_str = f"${price:.6f}"

                lines.append(f"{emoji} *{symbol}*: `{price_str}`")

        lines.append("")
        lines.append("─────────────────────────")
        lines.append(f"💡 _数据来源: {api_source}_")

        return "\n".join(lines)

    def start(self):
        """启动调度器"""
        if not self.bot:
            bot_logger.error("Cannot start price reporter: Bot not set")
            raise RuntimeError("Bot must be set before starting price reporter")

        try:
            if not self.scheduler.running:
                self.scheduler.start()
                bot_logger.info("Price reporter scheduler started")
            else:
                bot_logger.info("Price reporter scheduler already running")
        except Exception as e:
            bot_logger.error(f"Failed to start price reporter scheduler: {e}", exc_info=True)
            raise

    def stop(self):
        """停止调度器"""
        try:
            if self.scheduler.running:
                self.scheduler.shutdown()
                self.active_jobs.clear()
                bot_logger.info("Price reporter scheduler stopped")
            else:
                bot_logger.info("Price reporter scheduler is not running")
        except Exception as e:
            bot_logger.error(f"Error stopping price reporter scheduler: {e}", exc_info=True)


# 全局实例
price_reporter = PriceReporter()

__all__ = ['PriceReporter', 'price_reporter']
