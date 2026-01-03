"""
定时价格汇报模块
每5分钟自动推送加密货币价格
"""
import asyncio
from datetime import datetime
from apscheduler.schedulers.asyncio import AsyncIOScheduler
from telegram import Bot

from config.settings import settings
from src.exchange.cryptocompare_client import cryptocompare_client
from src.utils.logger import bot_logger


class PriceReporter:
    """定时价格汇报器"""

    def __init__(self):
        """初始化汇报器"""
        self.scheduler = AsyncIOScheduler()
        self.bot: Bot = None
        self.user_id = None  # 接收汇报的用户ID
        self.symbols = ['BTC', 'ETH', 'ADA']  # 监控的币种

        bot_logger.info("Price reporter initialized")

    def set_bot(self, bot: Bot):
        """设置 Bot 实例"""
        self.bot = bot

    def set_user(self, user_id: int):
        """设置接收汇报的用户"""
        self.user_id = user_id
        bot_logger.info(f"Price reporter set to notify user: {user_id}")

    async def send_price_report(self):
        """发送价格汇报"""
        if not self.bot or not self.user_id:
            bot_logger.warning("Bot or user_id not set, skipping price report")
            return

        try:
            bot_logger.info(f"Sending price report to user {self.user_id}")

            # 并发获取所有价格
            tasks = [
                cryptocompare_client.get_current_price(symbol)
                for symbol in self.symbols
            ]
            prices = await asyncio.gather(*tasks, return_exceptions=True)

            # 构建汇报消息
            message = self._format_report(prices)

            # 发送消息
            await self.bot.send_message(
                chat_id=self.user_id,
                text=message,
                parse_mode='Markdown'
            )

            bot_logger.info(f"Price report sent successfully to user {self.user_id}")

        except Exception as e:
            bot_logger.error(f"Error sending price report: {e}", exc_info=True)

    def _format_report(self, prices: list) -> str:
        """
        格式化价格汇报消息

        Args:
            prices: 价格列表

        Returns:
            格式化的消息
        """
        now = datetime.now()
        time_str = now.strftime("%H:%M")  # 只显示小时和分钟

        # 表情符号映射
        emoji_map = {
            'BTC': '₿',
            'ETH': '⟠',
            'ADA': '₳'
        }

        # 构建消息
        lines = [
            "┌─────────────────────────┐",
            f"│  📊 *价格汇报* `{time_str}`  │",
            "└─────────────────────────┘",
            ""
        ]

        for i, symbol in enumerate(self.symbols):
            price = prices[i]
            emoji = emoji_map.get(symbol, '•')

            if isinstance(price, Exception):
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
        lines.append("💡 _数据来源: Binance_")

        return "\n".join(lines)

    def start(self):
        """启动定时任务"""
        if not self.user_id:
            bot_logger.warning("Cannot start scheduler: user_id not set")
            return

        # 添加定时任务：每5分钟执行一次
        self.scheduler.add_job(
            self.send_price_report,
            'interval',
            minutes=5,
            id='price_report',
            replace_existing=True
        )

        self.scheduler.start()
        bot_logger.info("Price reporter scheduler started (every 5 minutes)")

    def stop(self):
        """停止定时任务"""
        if self.scheduler.running:
            self.scheduler.shutdown()
            bot_logger.info("Price reporter scheduler stopped")


# 全局实例
price_reporter = PriceReporter()

__all__ = ['PriceReporter', 'price_reporter']
