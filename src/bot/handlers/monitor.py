"""
监控任务管理指令处理器
包含 /add, /list, /delete 等指令
"""
import json
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import ContextTypes
from sqlalchemy import select, delete
from datetime import datetime

from src.database.connection import db_manager
from src.database.models import MonitorTask, User
from src.exchange.price_api_manager import price_api_manager
from src.utils.logger import bot_logger
from src.utils.exceptions import InvalidSymbolError


async def add_monitor_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """
    /add 指令处理器
    添加监控任务

    用法：
    /add BTC price 50000         - BTC价格达到50000时预警
    /add ETH price 3000 2500     - ETH价格突破3000或跌破2500时预警
    /add BTC percent 90000 5 -5  - BTC相对90000涨5%或跌5%时预警
    """
    user_id = update.effective_user.id

    # 检查参数
    if not context.args or len(context.args) < 3:
        await update.message.reply_text(
            "❌ 参数错误\n\n"
            "*用法：*\n"
            "`/add <币种> <类型> <参数...>`\n\n"
            "*价格阈值监控示例：*\n"
            "• `/add BTC price 50000` - BTC达到50000时预警\n"
            "• `/add BTC price high 50000` - BTC达到50000时预警（明确上限）\n"
            "• `/add BTC price low 40000` - BTC跌破40000时预警（明确下限）\n"
            "• `/add ETH price 3000 2500` - ETH突破3000或跌破2500\n\n"
            "*百分比监控示例：*\n"
            "• `/add BTC percent 90000 5 -5` - BTC相对90000涨5%或跌5%\n\n"
            "*说明：*\n"
            "• 币种：BTC, ETH, ADA, SOL等\n"
            "• 类型：`price`（价格）或 `percent`（百分比）",
            parse_mode='Markdown'
        )
        return

    symbol = context.args[0].upper()
    rule_type_arg = context.args[1].lower()

    try:
        # 验证交易对（使用多API故障转移）
        await price_api_manager.validate_symbol(symbol)

        # 解析规则类型和配置
        if rule_type_arg == 'price':
            rule_type = 'PRICE_THRESHOLD'
            rule_config = {}

            # 支持多种格式：
            # /add BTC price 50000           - 只设上限
            # /add BTC price high 50000      - 只设上限（明确）
            # /add BTC price low 40000       - 只设下限（明确）
            # /add BTC price 50000 40000     - 设上下限

            if len(context.args) >= 3:
                third_arg = context.args[2].lower()

                if third_arg == 'high':
                    # /add BTC price high 50000
                    if len(context.args) < 4:
                        await update.message.reply_text("❌ 请指定上限价格\n示例：`/add BTC price high 50000`", parse_mode='Markdown')
                        return
                    rule_config['threshold_high'] = float(context.args[3])

                elif third_arg == 'low':
                    # /add BTC price low 40000
                    if len(context.args) < 4:
                        await update.message.reply_text("❌ 请指定下限价格\n示例：`/add BTC price low 40000`", parse_mode='Markdown')
                        return
                    rule_config['threshold_low'] = float(context.args[3])

                else:
                    # /add BTC price 50000 [40000]
                    try:
                        threshold_value = float(context.args[2])
                        rule_config['threshold_high'] = threshold_value

                        # 如果提供了第二个数字，作为下限
                        if len(context.args) >= 4:
                            rule_config['threshold_low'] = float(context.args[3])
                    except ValueError:
                        await update.message.reply_text("❌ 价格必须是数字")
                        return

            if not rule_config:
                await update.message.reply_text("❌ 请至少指定一个价格阈值")
                return

        elif rule_type_arg in ['percent', 'percentage']:
            rule_type = 'PERCENTAGE'

            if len(context.args) < 4:
                await update.message.reply_text("❌ 百分比监控需要：参考价格、上涨阈值、下跌阈值\n示例：`/add BTC percent 90000 5 -5`", parse_mode='Markdown')
                return

            rule_config = {
                'reference_price': float(context.args[2]),
                'percentage_high': float(context.args[3]) if len(context.args) > 3 else None,
                'percentage_low': float(context.args[4]) if len(context.args) > 4 else None
            }

        else:
            await update.message.reply_text("❌ 未知的规则类型，请使用 `price` 或 `percent`", parse_mode='Markdown')
            return

        # 创建监控任务
        async with db_manager.get_session() as session:
            task = MonitorTask(
                user_id=user_id,
                symbol=symbol,
                market_type='SPOT',
                rule_type=rule_type,
                rule_config=json.dumps(rule_config),
                status='ACTIVE',
                cooldown_seconds=300  # 默认5分钟冷却
            )
            session.add(task)
            await session.commit()
            await session.refresh(task)

            # 构建确认消息
            message = f"✅ *监控任务已创建*\n\n"
            message += f"📊 币种: `{symbol}`\n"

            if rule_type == 'PRICE_THRESHOLD':
                if 'threshold_high' in rule_config:
                    message += f"🔺 上限: `${rule_config['threshold_high']:,.2f}`\n"
                if 'threshold_low' in rule_config:
                    message += f"🔻 下限: `${rule_config['threshold_low']:,.2f}`\n"
            else:
                message += f"📌 参考价: `${rule_config['reference_price']:,.2f}`\n"
                if rule_config.get('percentage_high'):
                    message += f"📈 涨幅预警: `{rule_config['percentage_high']}%`\n"
                if rule_config.get('percentage_low'):
                    message += f"📉 跌幅预警: `{abs(rule_config['percentage_low'])}%`\n"

            message += f"\n⏱ 冷却时间: 5分钟\n"
            message += f"🆔 任务ID: `{task.task_id}`\n\n"
            message += f"💡 使用 `/list` 查看所有任务"

            await update.message.reply_text(message, parse_mode='Markdown')
            bot_logger.info(f"User {user_id} created monitor task {task.task_id} for {symbol}")

    except InvalidSymbolError:
        await update.message.reply_text(f"❌ 无效的币种: {symbol}\n\n请检查币种名称是否正确")
    except ValueError as e:
        await update.message.reply_text(f"❌ 参数错误: {e}")
    except Exception as e:
        bot_logger.error(f"Error in add_monitor_command: {e}", exc_info=True)
        await update.message.reply_text("❌ 创建监控任务失败，请稍后再试")


async def list_monitors_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """
    /list 指令处理器
    查看所有监控任务
    """
    user_id = update.effective_user.id

    try:
        async with db_manager.get_session() as session:
            stmt = select(MonitorTask).where(
                MonitorTask.user_id == user_id,
                MonitorTask.status.in_(['ACTIVE', 'PAUSED'])
            ).order_by(MonitorTask.created_at.desc())

            result = await session.execute(stmt)
            tasks = result.scalars().all()

            if not tasks:
                await update.message.reply_text(
                    "📭 *暂无监控任务*\n\n"
                    "使用 `/add` 创建新的监控任务\n\n"
                    "*示例：*\n"
                    "`/add BTC price 50000`",
                    parse_mode='Markdown'
                )
                return

            # 构建任务列表消息
            message = f"📊 *监控任务列表* ({len(tasks)})\n\n"

            for task in tasks:
                status_emoji = "✅" if task.status == 'ACTIVE' else "⏸"
                message += f"{status_emoji} *{task.symbol}*\n"

                config = json.loads(task.rule_config)

                if task.rule_type == 'PRICE_THRESHOLD':
                    if 'threshold_high' in config:
                        message += f"   🔺 上限: ${config['threshold_high']:,.2f}\n"
                    if 'threshold_low' in config:
                        message += f"   🔻 下限: ${config['threshold_low']:,.2f}\n"
                elif task.rule_type == 'PERCENTAGE':
                    message += f"   📌 参考: ${config['reference_price']:,.2f}\n"
                    if config.get('percentage_high'):
                        message += f"   📈 涨 {config['percentage_high']}%\n"
                    if config.get('percentage_low'):
                        message += f"   📉 跌 {abs(config['percentage_low'])}%\n"

                message += f"   🆔 ID: `{task.task_id}`\n\n"

            message += "💡 使用 `/delete <ID>` 删除任务"

            await update.message.reply_text(message, parse_mode='Markdown')

    except Exception as e:
        bot_logger.error(f"Error in list_monitors_command: {e}", exc_info=True)
        await update.message.reply_text("❌ 获取任务列表失败")


async def delete_monitor_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """
    /delete 指令处理器
    删除监控任务

    用法: /delete <task_id>
    """
    user_id = update.effective_user.id

    if not context.args or len(context.args) < 1:
        await update.message.reply_text(
            "❌ 请指定任务ID\n\n"
            "用法: `/delete <任务ID>`\n"
            "示例: `/delete 1`\n\n"
            "使用 `/list` 查看所有任务ID",
            parse_mode='Markdown'
        )
        return

    try:
        task_id = int(context.args[0])

        async with db_manager.get_session() as session:
            # 查找任务
            stmt = select(MonitorTask).where(
                MonitorTask.task_id == task_id,
                MonitorTask.user_id == user_id
            )
            result = await session.execute(stmt)
            task = result.scalar_one_or_none()

            if not task:
                await update.message.reply_text(f"❌ 未找到任务ID {task_id}")
                return

            # 删除任务
            task.status = 'DELETED'
            await session.commit()

            await update.message.reply_text(
                f"✅ *任务已删除*\n\n"
                f"🆔 任务ID: `{task_id}`\n"
                f"📊 币种: `{task.symbol}`",
                parse_mode='Markdown'
            )

            bot_logger.info(f"User {user_id} deleted monitor task {task_id}")

    except ValueError:
        await update.message.reply_text("❌ 无效的任务ID，请输入数字")
    except Exception as e:
        bot_logger.error(f"Error in delete_monitor_command: {e}", exc_info=True)
        await update.message.reply_text("❌ 删除任务失败")


__all__ = ['add_monitor_command', 'list_monitors_command', 'delete_monitor_command']
