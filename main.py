#!/usr/bin/env python3
"""
Telegram 加密货币价格监控机器人
主程序入口

Usage:
    python main.py
"""
import sys
from pathlib import Path

# 确保项目根目录在 Python 路径中
sys.path.insert(0, str(Path(__file__).resolve().parent))

from config.settings import settings
from src.database.connection import init_database
from src.bot.main import CryptoBot
from src.utils.logger import bot_logger


def main():
    """主函数"""
    try:
        print("=" * 70)
        print("  Telegram 加密货币价格监控机器人")
        print("  Crypto Price Monitoring Bot for Telegram")
        print("=" * 70)
        print()

        # 创建并运行 Bot（Bot 内部会初始化数据库）
        bot = CryptoBot()
        bot.run()

    except KeyboardInterrupt:
        bot_logger.info("Bot stopped by user")
        print("\n\nBot stopped. Goodbye!")

    except Exception as e:
        bot_logger.error(f"Fatal error: {e}", exc_info=True)
        print(f"\n\n❌ Fatal Error: {e}")
        print("Please check logs for details.")
        sys.exit(1)


if __name__ == "__main__":
    # 直接运行主函数（不使用 asyncio.run）
    main()
