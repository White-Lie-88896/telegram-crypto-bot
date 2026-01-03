"""
Telegram Bot 主框架
管理 Bot 的启动、指令注册和生命周期
"""
from telegram.ext import ApplicationBuilder, CommandHandler, filters
from telegram import Update

from config.settings import settings
from src.utils.logger import bot_logger
from src.bot.handlers.basic import start_command, help_command
from src.bot.handlers.query import price_command
from src.notifier.price_reporter import price_reporter


class CryptoBot:
    """加密货币监控 Bot 主类"""

    def __init__(self):
        """初始化 Bot"""
        bot_logger.info("Initializing Crypto Monitoring Bot...")

        # 验证配置
        settings.validate()

        # 创建 Application
        self.app = ApplicationBuilder().token(settings.TELEGRAM_BOT_TOKEN).build()

        # 注册指令处理器
        self._register_handlers()

        bot_logger.info("Bot initialized successfully")

    def _register_handlers(self):
        """注册所有指令处理器"""
        bot_logger.info("Registering command handlers...")

        # 基础指令
        self.app.add_handler(CommandHandler("start", start_command))
        self.app.add_handler(CommandHandler("help", help_command))

        # 查询指令
        self.app.add_handler(CommandHandler("price", price_command))

        # TODO: 添加更多指令处理器
        # self.app.add_handler(CommandHandler("add", add_monitor_command))
        # self.app.add_handler(CommandHandler("list", list_monitors_command))
        # self.app.add_handler(CommandHandler("delete", delete_monitor_command))

        bot_logger.info("Command handlers registered")

    async def post_init(self, application):
        """Bot 启动后的初始化操作"""
        bot_logger.info("Running post-initialization tasks...")

        # 初始化数据库
        from src.database.connection import init_database
        bot_logger.info("Initializing database...")
        await init_database()
        bot_logger.info("Database initialized successfully")

        # 启动价格汇报器
        if settings.REPORT_USER_ID:
            bot_logger.info("Starting price reporter...")
            price_reporter.set_bot(application.bot)
            price_reporter.set_user(settings.REPORT_USER_ID)
            price_reporter.start()
            bot_logger.info(f"Price reporter started for user {settings.REPORT_USER_ID}")
        else:
            bot_logger.warning("REPORT_USER_ID not set, price reporter disabled")

        # TODO: 启动监控引擎
        # await monitor_engine.start()

    async def post_shutdown(self, application):
        """Bot 关闭前的清理操作"""
        bot_logger.info("Running shutdown tasks...")

        # 停止价格汇报器
        price_reporter.stop()

        # TODO: 停止监控引擎
        # await monitor_engine.stop()

    def run(self):
        """启动 Bot"""
        bot_logger.info("=" * 60)
        bot_logger.info("Starting Crypto Monitoring Bot...")
        bot_logger.info("=" * 60)

        # 显示配置信息
        if settings.DEBUG:
            settings.display()

        # 添加生命周期回调
        self.app.post_init = self.post_init
        self.app.post_shutdown = self.post_shutdown

        # 运行 Bot
        bot_logger.info("Bot is now running. Press Ctrl+C to stop.")
        self.app.run_polling(
            allowed_updates=Update.ALL_TYPES,
            drop_pending_updates=True,
            close_loop=False  # 避免事件循环冲突
        )


__all__ = ['CryptoBot']
