"""
日志系统配置模块
提供统一的日志记录功能
"""
import logging
import sys
from pathlib import Path
from logging.handlers import RotatingFileHandler
from typing import Optional

from config.settings import settings


def setup_logger(
    name: str,
    log_file: Optional[str] = None,
    level: Optional[str] = None,
    max_bytes: int = 10 * 1024 * 1024,  # 10 MB
    backup_count: int = 5
) -> logging.Logger:
    """
    配置并返回日志记录器

    Args:
        name: 日志记录器名称
        log_file: 日志文件路径（可选）
        level: 日志级别（可选，默认使用全局配置）
        max_bytes: 单个日志文件最大大小（字节）
        backup_count: 保留的备份文件数量

    Returns:
        配置好的 Logger 实例
    """
    # 创建 logger
    logger = logging.getLogger(name)
    log_level = level or settings.LOG_LEVEL
    logger.setLevel(getattr(logging, log_level.upper()))

    # 避免重复添加 handler
    if logger.handlers:
        return logger

    # 格式化器
    formatter = logging.Formatter(
        fmt='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
        datefmt='%Y-%m-%d %H:%M:%S'
    )

    # 控制台处理器
    console_handler = logging.StreamHandler(sys.stdout)
    console_handler.setFormatter(formatter)
    console_handler.setLevel(logging.DEBUG if settings.DEBUG else logging.INFO)
    logger.addHandler(console_handler)

    # 文件处理器（如果指定了日志文件）
    if log_file:
        # 创建日志目录
        log_path = Path(log_file)
        log_path.parent.mkdir(parents=True, exist_ok=True)

        file_handler = RotatingFileHandler(
            filename=log_file,
            maxBytes=max_bytes,
            backupCount=backup_count,
            encoding='utf-8'
        )
        file_handler.setFormatter(formatter)
        file_handler.setLevel(logging.DEBUG)
        logger.addHandler(file_handler)

    return logger


# 创建全局日志实例
bot_logger = setup_logger('bot', settings.LOG_FILE)
monitor_logger = setup_logger('monitor', settings.LOG_FILE.replace('bot.log', 'monitor.log'))
exchange_logger = setup_logger('exchange', settings.LOG_FILE.replace('bot.log', 'exchange.log'))
database_logger = setup_logger('database', settings.LOG_FILE.replace('bot.log', 'database.log'))


def get_logger(name: str) -> logging.Logger:
    """
    获取指定名称的日志记录器

    Args:
        name: 日志记录器名称

    Returns:
        Logger 实例
    """
    return setup_logger(name, settings.LOG_FILE)


__all__ = [
    'setup_logger',
    'get_logger',
    'bot_logger',
    'monitor_logger',
    'exchange_logger',
    'database_logger'
]
