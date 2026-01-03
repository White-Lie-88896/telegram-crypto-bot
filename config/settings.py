"""
全局配置管理模块
从环境变量加载配置
"""
import os
from pathlib import Path
from dotenv import load_dotenv

# 加载 .env 文件
load_dotenv()

# 项目根目录
BASE_DIR = Path(__file__).resolve().parent.parent


class Settings:
    """全局配置类"""

    # ======================
    # Telegram Bot 配置
    # ======================
    TELEGRAM_BOT_TOKEN: str = os.getenv('TELEGRAM_BOT_TOKEN', '')

    # ======================
    # Binance API 配置
    # ======================
    BINANCE_API_KEY: str = os.getenv('BINANCE_API_KEY', '')
    BINANCE_API_SECRET: str = os.getenv('BINANCE_API_SECRET', '')

    # ======================
    # 数据库配置
    # ======================
    DATABASE_URL: str = os.getenv(
        'DATABASE_URL',
        f'sqlite+aiosqlite:///{BASE_DIR}/data/crypto_bot.db'
    )

    # ======================
    # 监控引擎配置
    # ======================
    CHECK_INTERVAL: int = int(os.getenv('CHECK_INTERVAL', '5'))
    MAX_CONCURRENT_TASKS: int = int(os.getenv('MAX_CONCURRENT_TASKS', '100'))

    # ======================
    # 日志配置
    # ======================
    LOG_LEVEL: str = os.getenv('LOG_LEVEL', 'INFO')
    LOG_FILE: str = os.getenv('LOG_FILE', str(BASE_DIR / 'logs' / 'bot.log'))

    # ======================
    # 限流配置
    # ======================
    BINANCE_REQUEST_LIMIT: int = int(os.getenv('BINANCE_REQUEST_LIMIT', '1200'))
    DEFAULT_COOLDOWN: int = int(os.getenv('DEFAULT_COOLDOWN', '300'))
    MAX_DAILY_ALERTS: int = int(os.getenv('MAX_DAILY_ALERTS', '100'))

    # ======================
    # 价格汇报配置
    # ======================
    REPORT_USER_ID: int = int(os.getenv('REPORT_USER_ID', '0'))

    # ======================
    # 其他配置
    # ======================
    DEBUG: bool = os.getenv('DEBUG', 'False').lower() == 'true'

    @classmethod
    def validate(cls):
        """验证必需的配置项"""
        if not cls.TELEGRAM_BOT_TOKEN:
            raise ValueError(
                "TELEGRAM_BOT_TOKEN is required. "
                "Please set it in .env file or environment variables."
            )

        if cls.CHECK_INTERVAL < 1:
            raise ValueError("CHECK_INTERVAL must be at least 1 second")

        if cls.MAX_CONCURRENT_TASKS < 1:
            raise ValueError("MAX_CONCURRENT_TASKS must be at least 1")

    @classmethod
    def display(cls):
        """显示当前配置（隐藏敏感信息）"""
        print("=" * 50)
        print("Current Configuration:")
        print("=" * 50)
        print(f"TELEGRAM_BOT_TOKEN: {'*' * 10 if cls.TELEGRAM_BOT_TOKEN else 'NOT SET'}")
        print(f"BINANCE_API_KEY: {'*' * 10 if cls.BINANCE_API_KEY else 'NOT SET'}")
        print(f"DATABASE_URL: {cls.DATABASE_URL}")
        print(f"CHECK_INTERVAL: {cls.CHECK_INTERVAL}s")
        print(f"MAX_CONCURRENT_TASKS: {cls.MAX_CONCURRENT_TASKS}")
        print(f"LOG_LEVEL: {cls.LOG_LEVEL}")
        print(f"LOG_FILE: {cls.LOG_FILE}")
        print(f"DEBUG: {cls.DEBUG}")
        print("=" * 50)


# 全局配置实例
settings = Settings()

# 导出
__all__ = ['settings', 'Settings']
