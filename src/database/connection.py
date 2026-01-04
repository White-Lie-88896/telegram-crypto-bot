"""
数据库连接管理
提供异步数据库会话管理
"""
from contextlib import asynccontextmanager
from typing import AsyncGenerator

from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession, async_sessionmaker
from sqlalchemy.pool import StaticPool

from config.settings import settings
from src.database.models import Base
from src.utils.logger import database_logger


class DatabaseManager:
    """数据库管理器（单例模式）"""

    _instance = None
    _engine = None
    _session_maker = None

    def __new__(cls):
        if cls._instance is None:
            cls._instance = super().__new__(cls)
        return cls._instance

    def initialize(self):
        """初始化数据库引擎和会话工厂"""
        if self._engine is not None:
            return

        database_logger.info(f"Initializing database: {settings.DATABASE_URL}")

        # 创建异步引擎
        # SQLite 需要特殊配置以支持多线程访问
        self._engine = create_async_engine(
            settings.DATABASE_URL,
            echo=settings.DEBUG,
            poolclass=StaticPool,  # SQLite 使用 StaticPool
            connect_args={"check_same_thread": False}  # SQLite 特定参数
        )

        # 创建会话工厂
        self._session_maker = async_sessionmaker(
            bind=self._engine,
            class_=AsyncSession,
            expire_on_commit=False
        )

        database_logger.info("Database initialized successfully")

    async def create_tables(self):
        """创建所有表"""
        if self._engine is None:
            raise RuntimeError("Database not initialized. Call initialize() first.")

        database_logger.info("Creating database tables...")
        async with self._engine.begin() as conn:
            await conn.run_sync(Base.metadata.create_all)
        database_logger.info("Database tables created successfully")

    async def drop_tables(self):
        """删除所有表（慎用！）"""
        if self._engine is None:
            raise RuntimeError("Database not initialized. Call initialize() first.")

        database_logger.warning("Dropping all database tables...")
        async with self._engine.begin() as conn:
            await conn.run_sync(Base.metadata.drop_all)
        database_logger.info("Database tables dropped")

    @asynccontextmanager
    async def get_session(self) -> AsyncGenerator[AsyncSession, None]:
        """
        获取数据库会话（上下文管理器）

        用法:
            async with db_manager.get_session() as session:
                # 执行数据库操作
                result = await session.execute(...)
        """
        if self._session_maker is None:
            raise RuntimeError("Database not initialized. Call initialize() first.")

        session: AsyncSession = self._session_maker()
        try:
            yield session
            await session.commit()
        except Exception as e:
            await session.rollback()
            database_logger.error(f"Database session error: {e}", exc_info=True)
            raise
        finally:
            await session.close()

    async def close(self):
        """关闭数据库连接"""
        try:
            if self._engine is not None:
                await self._engine.dispose()
                database_logger.info("Database connection closed")
        except Exception as e:
            database_logger.error(f"Error closing database connection: {e}", exc_info=True)


# 全局数据库管理器实例
db_manager = DatabaseManager()


# 便捷函数
async def init_database():
    """初始化数据库"""
    db_manager.initialize()
    await db_manager.create_tables()


async def get_db_session() -> AsyncGenerator[AsyncSession, None]:
    """获取数据库会话（依赖注入用）"""
    async with db_manager.get_session() as session:
        yield session


__all__ = ['DatabaseManager', 'db_manager', 'init_database', 'get_db_session']
