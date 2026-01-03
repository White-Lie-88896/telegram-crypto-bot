#!/usr/bin/env python3
"""
数据库初始化脚本
运行此脚本以创建数据库表和插入默认配置
"""
import asyncio
import sys
from pathlib import Path

# 添加项目根目录到 Python 路径
sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from sqlalchemy import select
from src.database.connection import db_manager
from src.database.models import SystemConfig
from src.utils.logger import database_logger
from config.settings import settings


async def insert_default_configs():
    """插入默认系统配置"""
    database_logger.info("Inserting default system configurations...")

    default_configs = [
        {
            'config_key': 'max_tasks_per_user',
            'config_value': '50',
            'description': '每个用户最大监控任务数'
        },
        {
            'config_key': 'default_cooldown',
            'config_value': '300',
            'description': '默认冷却时间（秒）'
        },
        {
            'config_key': 'check_interval',
            'config_value': str(settings.CHECK_INTERVAL),
            'description': '监控检查间隔（秒）'
        },
        {
            'config_key': 'max_daily_alerts',
            'config_value': str(settings.MAX_DAILY_ALERTS),
            'description': '每个用户每日最大预警数'
        },
        {
            'config_key': 'binance_request_limit',
            'config_value': str(settings.BINANCE_REQUEST_LIMIT),
            'description': 'Binance API 每分钟请求限制'
        }
    ]

    async with db_manager.get_session() as session:
        for config in default_configs:
            # 检查是否已存在
            stmt = select(SystemConfig).where(
                SystemConfig.config_key == config['config_key']
            )
            result = await session.execute(stmt)
            existing = result.scalar_one_or_none()

            if existing is None:
                # 插入新配置
                new_config = SystemConfig(**config)
                session.add(new_config)
                database_logger.info(f"Inserted config: {config['config_key']}")
            else:
                database_logger.info(f"Config already exists: {config['config_key']}")

        await session.commit()

    database_logger.info("Default configurations inserted successfully")


async def init_database():
    """执行数据库初始化"""
    try:
        print("=" * 60)
        print("Database Initialization")
        print("=" * 60)
        print(f"Database URL: {settings.DATABASE_URL}")
        print("=" * 60)

        # 验证配置
        settings.validate()

        # 初始化数据库管理器
        database_logger.info("Initializing database manager...")
        db_manager.initialize()

        # 创建表
        database_logger.info("Creating database tables...")
        await db_manager.create_tables()

        # 插入默认配置
        await insert_default_configs()

        print("=" * 60)
        print("Database initialized successfully!")
        print("=" * 60)
        print("\nNext steps:")
        print("1. Copy .env.example to .env")
        print("2. Set your TELEGRAM_BOT_TOKEN in .env")
        print("3. Run: python main.py")
        print("=" * 60)

    except Exception as e:
        database_logger.error(f"Database initialization failed: {e}", exc_info=True)
        print(f"\nERROR: {e}")
        sys.exit(1)


async def reset_database():
    """重置数据库（删除所有表并重新创建）"""
    print("=" * 60)
    print("WARNING: This will delete all existing data!")
    print("=" * 60)

    confirm = input("Are you sure you want to reset the database? (yes/no): ")

    if confirm.lower() != 'yes':
        print("Operation cancelled.")
        return

    try:
        db_manager.initialize()

        # 删除所有表
        database_logger.warning("Dropping all tables...")
        await db_manager.drop_tables()

        # 重新创建表
        database_logger.info("Recreating tables...")
        await db_manager.create_tables()

        # 插入默认配置
        await insert_default_configs()

        print("=" * 60)
        print("Database reset successfully!")
        print("=" * 60)

    except Exception as e:
        database_logger.error(f"Database reset failed: {e}", exc_info=True)
        print(f"\nERROR: {e}")
        sys.exit(1)


if __name__ == "__main__":
    import argparse

    parser = argparse.ArgumentParser(description="Database initialization script")
    parser.add_argument(
        '--reset',
        action='store_true',
        help='Reset database (delete all tables and recreate)'
    )

    args = parser.parse_args()

    if args.reset:
        asyncio.run(reset_database())
    else:
        asyncio.run(init_database())
