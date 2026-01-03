"""
自定义异常类定义
"""


class BotException(Exception):
    """基础异常类"""
    pass


class ConfigurationError(BotException):
    """配置错误"""
    pass


class DatabaseError(BotException):
    """数据库相关错误"""
    pass


class BinanceAPIError(BotException):
    """Binance API 相关错误"""
    pass


class RateLimitExceeded(BotException):
    """速率限制超出"""
    pass


class InvalidSymbolError(BotException):
    """无效的交易对"""
    pass


class AlertSendError(BotException):
    """消息发送失败"""
    pass


class TaskExecutionError(BotException):
    """任务执行错误"""
    pass


class ValidationError(BotException):
    """数据验证错误"""
    pass


__all__ = [
    'BotException',
    'ConfigurationError',
    'DatabaseError',
    'BinanceAPIError',
    'RateLimitExceeded',
    'InvalidSymbolError',
    'AlertSendError',
    'TaskExecutionError',
    'ValidationError'
]
