"""
价格阈值监控规则
当价格突破指定阈值时触发
"""
from typing import Dict, Any
from src.monitor.rules.base import MonitorRule, RuleEvaluationResult
from src.utils.logger import exchange_logger


class PriceThresholdRule(MonitorRule):
    """价格阈值规则"""

    def __init__(self, config: Dict[str, Any]):
        """
        初始化价格阈值规则

        Args:
            config: 配置字典，包含：
                - threshold_high: 上限价格（可选）
                - threshold_low: 下限价格（可选）
        """
        super().__init__(config)
        self.threshold_high = config.get('threshold_high')
        self.threshold_low = config.get('threshold_low')

        if self.threshold_high is None and self.threshold_low is None:
            raise ValueError("Must specify at least one threshold (high or low)")

    async def evaluate(self, current_price: float, symbol: str) -> RuleEvaluationResult:
        """
        评估价格阈值

        Args:
            current_price: 当前价格
            symbol: 交易对符号

        Returns:
            评估结果
        """
        triggered = False
        trigger_condition = ""
        message = ""

        # 检查上限
        if self.threshold_high is not None and current_price >= self.threshold_high:
            triggered = True
            trigger_condition = f"价格 >= ${self.threshold_high:,.2f}"
            message = f"🔴 *{symbol} 价格预警*\n\n"
            message += f"━━━━━━━━━━━━━━━━━━━━━━\n"
            message += f"当前价格: `${current_price:,.2f}`\n"
            message += f"已达到上限: `${self.threshold_high:,.2f}`\n"
            message += f"━━━━━━━━━━━━━━━━━━━━━━\n\n"
            message += f"📈 突破上限阈值！"

        # 检查下限
        elif self.threshold_low is not None and current_price <= self.threshold_low:
            triggered = True
            trigger_condition = f"价格 <= ${self.threshold_low:,.2f}"
            message = f"🟢 *{symbol} 价格预警*\n\n"
            message += f"━━━━━━━━━━━━━━━━━━━━━━\n"
            message += f"当前价格: `${current_price:,.2f}`\n"
            message += f"已达到下限: `${self.threshold_low:,.2f}`\n"
            message += f"━━━━━━━━━━━━━━━━━━━━━━\n\n"
            message += f"📉 跌破下限阈值！"

        return RuleEvaluationResult(
            triggered=triggered,
            message=message,
            current_value=current_price,
            trigger_condition=trigger_condition
        )

    def get_description(self) -> str:
        """获取规则描述"""
        desc_parts = []
        if self.threshold_high is not None:
            desc_parts.append(f"上限 ${self.threshold_high:,.2f}")
        if self.threshold_low is not None:
            desc_parts.append(f"下限 ${self.threshold_low:,.2f}")
        return " | ".join(desc_parts)


__all__ = ['PriceThresholdRule']
