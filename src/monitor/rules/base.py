"""
监控规则基类
定义所有监控规则的接口
"""
from abc import ABC, abstractmethod
from typing import Dict, Any, Optional
from dataclasses import dataclass

from src.utils.logger import exchange_logger


@dataclass
class RuleEvaluationResult:
    """规则评估结果"""
    triggered: bool  # 是否触发
    message: str  # 触发消息
    current_value: float  # 当前值（价格）
    trigger_condition: str  # 触发条件描述


class MonitorRule(ABC):
    """监控规则基类"""

    def __init__(self, config: Dict[str, Any]):
        """
        初始化规则

        Args:
            config: 规则配置字典
        """
        self.config = config

    @abstractmethod
    async def evaluate(self, current_price: float, symbol: str) -> RuleEvaluationResult:
        """
        评估规则是否触发

        Args:
            current_price: 当前价格
            symbol: 交易对符号

        Returns:
            评估结果
        """
        pass

    @abstractmethod
    def get_description(self) -> str:
        """获取规则描述"""
        pass

    def __repr__(self):
        return f"{self.__class__.__name__}({self.config})"


__all__ = ['MonitorRule', 'RuleEvaluationResult']
