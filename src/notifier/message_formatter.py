"""
消息格式化器
标准化所有发送给用户的消息格式
"""
from datetime import datetime
from typing import Dict, Any


class MessageFormatter:
    """消息格式化工具类"""

    @staticmethod
    def format_price_info(ticker_data: Dict[str, Any]) -> str:
        """
        格式化价格查询结果

        Args:
            ticker_data: 24h ticker 数据

        Returns:
            格式化的消息文本
        """
        symbol = ticker_data['symbol']
        price = ticker_data['lastPrice']
        change_pct = ticker_data['priceChangePercent']
        high = ticker_data['highPrice']
        low = ticker_data['lowPrice']
        volume = ticker_data['volume']

        # 选择 emoji
        emoji = "💰"
        trend = "↗️" if change_pct >= 0 else "↘️"

        # 格式化价格显示
        if price >= 1000:
            price_str = f"${price:,.2f}"
            high_str = f"${high:,.2f}"
            low_str = f"${low:,.2f}"
        elif price >= 1:
            price_str = f"${price:.4f}"
            high_str = f"${high:.4f}"
            low_str = f"${low:.4f}"
        else:
            price_str = f"${price:.6f}"
            high_str = f"${high:.6f}"
            low_str = f"${low:.6f}"

        # 格式化成交量
        if volume >= 1000:
            volume_str = f"{volume:,.2f}"
        else:
            volume_str = f"{volume:.4f}"

        message = f"""
{emoji} *{symbol.replace('USDT', '')} 价格信息*

━━━━━━━━━━━━━━━━━━━━━━
📊 当前价格：`{price_str}`
━━━━━━━━━━━━━━━━━━━━━━

24h 最高：`{high_str}`
24h 最低：`{low_str}`
24h 涨跌：`{change_pct:+.2f}%` {trend}
24h 成交量：`{volume_str}` {symbol.replace('USDT', '')}

⏰ 更新时间：`{datetime.now().strftime('%H:%M:%S')}`
💡 数据来源：Binance
"""
        return message.strip()

    @staticmethod
    def format_price_threshold_alert(alert_data: Dict[str, Any]) -> str:
        """
        格式化价格阈值预警消息

        Args:
            alert_data: 预警数据

        Returns:
            格式化的消息文本
        """
        symbol = alert_data['symbol']
        current_price = alert_data['current_price']
        target_price = alert_data['target_price']
        condition = alert_data['condition']  # 'ABOVE' or 'BELOW'

        emoji = "🔔"
        condition_text = "突破" if condition == 'ABOVE' else "跌破"

        message = f"""
{emoji} *价格预警触发*

交易对: `{symbol}`
当前价格: `{current_price:.8f}` USDT
目标价格: `{target_price:.8f}` USDT

{condition_text}价格阈值！

触发时间: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}
数据来源: Binance
"""
        return message.strip()

    @staticmethod
    def format_percentage_alert(alert_data: Dict[str, Any]) -> str:
        """
        格式化百分比涨跌预警消息

        Args:
            alert_data: 预警数据

        Returns:
            格式化的消息文本
        """
        symbol = alert_data['symbol']
        current_price = alert_data['current_price']
        reference_price = alert_data['reference_price']
        change_pct = alert_data['change_pct']

        emoji = "📈" if change_pct > 0 else "📉"
        direction = "上涨" if change_pct > 0 else "下跌"

        message = f"""
{emoji} *{direction}预警触发*

交易对: `{symbol}`
当前价格: `{current_price:.8f}` USDT
参考价格: `{reference_price:.8f}` USDT
涨跌幅: `{change_pct:+.2f}%`

触发时间: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}
数据来源: Binance
"""
        return message.strip()

    @staticmethod
    def format_task_list(tasks: list) -> str:
        """
        格式化任务列表

        Args:
            tasks: 任务列表

        Returns:
            格式化的消息文本
        """
        if not tasks:
            return "您还没有创建任何监控任务\n\n使用 /add 创建第一个任务"

        message_lines = ["*您的监控任务*\n"]

        for task in tasks:
            status_emoji = "✅" if task['status'] == 'ACTIVE' else "⏸"
            rule_type_map = {
                'PRICE_THRESHOLD': '价格阈值',
                'PERCENTAGE': '百分比涨跌'
            }
            rule_type_name = rule_type_map.get(task['rule_type'], task['rule_type'])

            message_lines.append(
                f"{status_emoji} `#{task['task_id']}` *{task['symbol']}*\n"
                f"   规则: {rule_type_name}\n"
                f"   状态: {task['status']}\n"
            )

        message_lines.append(f"\n共 {len(tasks)} 个任务")
        message_lines.append("\n使用 /delete <task_id> 删除任务")

        return '\n'.join(message_lines)

    @staticmethod
    def format_error(error_message: str) -> str:
        """
        格式化错误消息

        Args:
            error_message: 错误信息

        Returns:
            格式化的消息文本
        """
        return f"❌ 错误: {error_message}"

    @staticmethod
    def format_success(success_message: str) -> str:
        """
        格式化成功消息

        Args:
            success_message: 成功信息

        Returns:
            格式化的消息文本
        """
        return f"✅ {success_message}"


__all__ = ['MessageFormatter']
