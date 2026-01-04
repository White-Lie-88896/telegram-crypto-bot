"""
价格汇报管理指令处理器
包含 /report 相关指令
"""
from telegram import Update
from telegram.ext import ContextTypes
from sqlalchemy import select

from src.database.connection import db_manager
from src.database.models import ReportConfig
from src.utils.logger import bot_logger
from src.notifier.price_reporter import price_reporter


async def report_config_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """
    /report 指令处理器
    配置和管理价格汇报功能

    用法：
    /report config <间隔分钟> <币种列表>  - 配置汇报参数
    /report start                        - 启动汇报
    /report stop                         - 停止汇报
    /report status                       - 查看当前配置
    """
    user_id = update.effective_user.id

    # 检查子命令
    if not context.args or len(context.args) == 0:
        await _show_report_help(update)
        return

    subcommand = context.args[0].lower()

    if subcommand == 'config':
        await _handle_config(update, context, user_id)
    elif subcommand == 'start':
        await _handle_start(update, user_id)
    elif subcommand == 'stop':
        await _handle_stop(update, user_id)
    elif subcommand == 'status':
        await _handle_status(update, user_id)
    else:
        await _show_report_help(update)


async def _show_report_help(update: Update):
    """显示帮助信息"""
    help_text = """
📊 *价格汇报功能*

━━━━━━━━━━━━━━━━━━━━━━

*配置汇报参数：*
`/report config <间隔> <币种>`

   示例：`/report config 30 BTC,ETH,SOL`
   说明：每30分钟汇报BTC、ETH、SOL价格

*启动汇报：*
`/report start`

*停止汇报：*
`/report stop`

*查看当前配置：*
`/report status`

━━━━━━━━━━━━━━━━━━━━━━

*参数说明：*
• 间隔：汇报间隔（分钟），建议30-1440（30分钟到24小时）
• 币种：用逗号分隔，例如 BTC,ETH,ADA

*注意事项：*
• 配置后需要手动启动汇报
• 修改配置不会自动重启，需要先stop再start
• 支持的币种：BTC、ETH、SOL、ADA、BNB等主流币种
"""
    await update.message.reply_text(help_text, parse_mode='Markdown')


async def _handle_config(update: Update, context: ContextTypes.DEFAULT_TYPE, user_id: int):
    """处理配置命令"""
    if len(context.args) < 3:
        await update.message.reply_text(
            "❌ 参数不足\n\n"
            "*用法：*\n"
            "`/report config <间隔分钟> <币种列表>`\n\n"
            "*示例：*\n"
            "`/report config 30 BTC,ETH,SOL`",
            parse_mode='Markdown'
        )
        return

    try:
        # 解析参数
        interval_minutes = int(context.args[1])
        symbols_str = context.args[2].upper()

        # 验证参数
        if interval_minutes < 5:
            await update.message.reply_text(
                "❌ 汇报间隔不能小于5分钟\n\n"
                "建议设置为30-1440分钟（30分钟到24小时）"
            )
            return

        if interval_minutes > 10080:  # 7天
            await update.message.reply_text(
                "❌ 汇报间隔不能超过7天（10080分钟）"
            )
            return

        # 解析币种列表
        symbols = [s.strip() for s in symbols_str.split(',') if s.strip()]
        if not symbols:
            await update.message.reply_text("❌ 请至少指定一个币种")
            return

        if len(symbols) > 10:
            await update.message.reply_text("❌ 币种数量不能超过10个")
            return

        # 保存配置到数据库
        async with db_manager.get_session() as session:
            stmt = select(ReportConfig).where(ReportConfig.user_id == user_id)
            result = await session.execute(stmt)
            config = result.scalar_one_or_none()

            if config is None:
                # 创建新配置
                config = ReportConfig(
                    user_id=user_id,
                    enabled=False,  # 默认不启动，需要用户手动start
                    interval_minutes=interval_minutes,
                    symbols=','.join(symbols)
                )
                session.add(config)
            else:
                # 更新现有配置
                config.interval_minutes = interval_minutes
                config.symbols = ','.join(symbols)

            await session.commit()

        # 构建确认消息
        symbols_display = ', '.join(symbols)
        message = f"""
✅ *汇报配置已保存*

━━━━━━━━━━━━━━━━━━━━━━
⏰ 汇报间隔: `{interval_minutes}` 分钟
📊 监控币种: `{symbols_display}`
━━━━━━━━━━━━━━━━━━━━━━

💡 使用 `/report start` 启动汇报
"""
        await update.message.reply_text(message.strip(), parse_mode='Markdown')
        bot_logger.info(f"User {user_id} configured report: {interval_minutes}min, {symbols}")

    except ValueError:
        await update.message.reply_text("❌ 间隔时间必须是数字")
    except Exception as e:
        bot_logger.error(f"Error in report config: {e}", exc_info=True)
        await update.message.reply_text("❌ 配置失败，请稍后再试")


async def _handle_start(update: Update, user_id: int):
    """处理启动汇报命令"""
    try:
        async with db_manager.get_session() as session:
            stmt = select(ReportConfig).where(ReportConfig.user_id == user_id)
            result = await session.execute(stmt)
            config = result.scalar_one_or_none()

            if config is None:
                await update.message.reply_text(
                    "❌ 尚未配置汇报参数\n\n"
                    "请先使用 `/report config` 配置汇报参数\n"
                    "例如：`/report config 30 BTC,ETH,SOL`",
                    parse_mode='Markdown'
                )
                return

            if config.enabled:
                await update.message.reply_text(
                    "ℹ️ 汇报功能已经在运行中\n\n"
                    f"⏰ 汇报间隔: {config.interval_minutes} 分钟\n"
                    f"📊 监控币种: {', '.join(config.get_symbols_list())}"
                )
                return

            # 启动汇报
            config.enabled = True
            await session.commit()

            # 通知price_reporter添加该用户的汇报任务
            await price_reporter.add_user_report(
                user_id=user_id,
                interval_minutes=config.interval_minutes,
                symbols=config.get_symbols_list()
            )

            symbols_display = ', '.join(config.get_symbols_list())
            message = f"""
✅ *汇报功能已启动*

━━━━━━━━━━━━━━━━━━━━━━
⏰ 汇报间隔: `{config.interval_minutes}` 分钟
📊 监控币种: `{symbols_display}`
━━━━━━━━━━━━━━━━━━━━━━

💡 使用 `/report stop` 可以停止汇报
💡 使用 `/report status` 查看状态
"""
            await update.message.reply_text(message.strip(), parse_mode='Markdown')
            bot_logger.info(f"User {user_id} started price report")

    except Exception as e:
        bot_logger.error(f"Error starting report: {e}", exc_info=True)
        await update.message.reply_text("❌ 启动失败，请稍后再试")


async def _handle_stop(update: Update, user_id: int):
    """处理停止汇报命令"""
    try:
        async with db_manager.get_session() as session:
            stmt = select(ReportConfig).where(ReportConfig.user_id == user_id)
            result = await session.execute(stmt)
            config = result.scalar_one_or_none()

            if config is None or not config.enabled:
                await update.message.reply_text("ℹ️ 汇报功能未运行")
                return

            # 停止汇报
            config.enabled = False
            await session.commit()

            # 通知price_reporter移除该用户的汇报任务
            await price_reporter.remove_user_report(user_id)

            await update.message.reply_text(
                "✅ *汇报功能已停止*\n\n"
                "💡 使用 `/report start` 可以重新启动",
                parse_mode='Markdown'
            )
            bot_logger.info(f"User {user_id} stopped price report")

    except Exception as e:
        bot_logger.error(f"Error stopping report: {e}", exc_info=True)
        await update.message.reply_text("❌ 停止失败，请稍后再试")


async def _handle_status(update: Update, user_id: int):
    """处理查看状态命令"""
    try:
        async with db_manager.get_session() as session:
            stmt = select(ReportConfig).where(ReportConfig.user_id == user_id)
            result = await session.execute(stmt)
            config = result.scalar_one_or_none()

            if config is None:
                await update.message.reply_text(
                    "📊 *汇报功能状态*\n\n"
                    "❌ 尚未配置\n\n"
                    "💡 使用 `/report config` 进行配置",
                    parse_mode='Markdown'
                )
                return

            status_emoji = "✅ 运行中" if config.enabled else "⏸ 已停止"
            symbols_display = ', '.join(config.get_symbols_list())

            message = f"""
📊 *汇报功能状态*

━━━━━━━━━━━━━━━━━━━━━━
📌 状态: {status_emoji}
⏰ 汇报间隔: `{config.interval_minutes}` 分钟
📊 监控币种: `{symbols_display}`
━━━━━━━━━━━━━━━━━━━━━━

💡 使用 `/report start` 启动汇报
💡 使用 `/report stop` 停止汇报
💡 使用 `/report config` 修改配置
"""
            await update.message.reply_text(message.strip(), parse_mode='Markdown')

    except Exception as e:
        bot_logger.error(f"Error getting report status: {e}", exc_info=True)
        await update.message.reply_text("❌ 获取状态失败，请稍后再试")


__all__ = ['report_config_command']
