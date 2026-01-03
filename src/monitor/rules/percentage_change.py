"""
百分比涨跌监控规则
监控价格相对于参考价格的涨跌幅
"""
from typing import Dict, Any
from src.monitor.rules.base import MonitorRule, RuleEvaluationResult
from src.utils.logger import exchange_logger


class PercentageChangeRule(MonitorRule):
    """百分比涨跌规则"""

    def __init__(self, config: Dict[str, Any]):
        """
        初始化百分比涨跌规则

        Args:
            config: 配置字典，包含：
                - reference_price: 参考价格（必需）
                - percentage_high: 上涨百分比阈值（可选）
                - percentage_low: 下跌百分比阈值（可选，负数）
        """
        super().__init__(config)
        self.reference_price = config.get('reference_price')
        self.percentage_high = config.get('percentage_high')  # 例如：5 表示涨5%
        self.percentage_low = config.get('percentage_low')    # 例如：-5 表示跌5%

        if self.reference_price is None:
            raise ValueError("reference_price is required")

        if self.percentage_high is None and self.percentage_low is None:
            raise ValueError("Must specify at least one percentage threshold")

    async def evaluate(self, current_price: float, symbol: str) -> RuleEvaluationResult:
        """
        评估百分比涨跌

        Args:
            current_price: 当前价格
            symbol: 交易对符号

        Returns:
            评估结果
        """
        # 计算当前涨跌幅
        change_percent = ((current_price - self.reference_price) / self.reference_price) * 100

        triggered = False
        trigger_condition = ""
        message = ""

        # 检查上涨幅度
        if self.percentage_high is not None and change_percent >= self.percentage_high:
            triggered = True
            trigger_condition = f"涨幅 >= {self.percentage_high}%"
            message = f"📈 *{symbol} 涨幅预警*\n\n"
            message += f"当前价格: `${current_price:,.2f}`\n"
            message += f"参考价格: `${self.reference_price:,.2f}`\n"
            message += f"涨幅: `{change_percent:+.2f}%`\n\n"
            message += f"🔥 涨幅已达 {self.percentage_high}%！"

        # 检查下跌幅度
        elif self.percentage_low is not None and change_percent <= self.percentage_low:
            triggered = True
            trigger_condition = f"跌幅 <= {self.percentage_low}%"
            message = f"📉 *{symbol} 跌幅预警*\n\n"
            message += f"当前价格: `${current_price:,.2f}`\n"
            message += f"参考价格: `${self.reference_price:,.2f}`\n"
            message += f"跌幅: `{change_percent:+.2f}%`\n\n"
            message += f"⚠️ 跌幅已达 {abs(self.percentage_low)}%！"

        return RuleEvaluationResult(
            triggered=triggered,
            message=message,
            current_value=current_price,
            trigger_condition=trigger_condition
        )

    def get_description(self) -> str:
        """获取规则描述"""
        desc_parts = [f"参考价 ${self.reference_price:,.2f}"]
        if self.percentage_high is not None:
            desc_parts.append(f"涨 {self.percentage_high}%")
        if self.percentage_low is not None:
            desc_parts.append(f"跌 {abs(self.percentage_low)}%")
        return " | ".join(desc_parts)


__all__ = ['PercentageChangeRule']
