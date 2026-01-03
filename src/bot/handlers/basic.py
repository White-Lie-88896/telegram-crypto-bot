"""
Telegram Bot 基础指令处理器
包含 /start 和 /help 指令
"""
from telegram import Update
from telegram.ext import ContextTypes
from sqlalchemy import select
from datetime import datetime

from src.database.models import User
from src.database.connection import db_manager
from src.utils.logger import bot_logger


async def start_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """
    /start 指令处理器
    注册用户并显示欢迎消息
    """
    user = update.effective_user
    bot_logger.info(f"User {user.id} ({user.username}) started the bot")

    # 注册或更新用户信息
    try:
        async with db_manager.get_session() as session:
            stmt = select(User).where(User.user_id == user.id)
            result = await session.execute(stmt)
            existing_user = result.scalar_one_or_none()

            if existing_user is None:
                # 新用户
                new_user = User(
                    user_id=user.id,
                    username=user.username,
                    first_name=user.first_name,
                    last_name=user.last_name,
                    language_code=user.language_code or 'en',
                    is_active=True
                )
                session.add(new_user)
                await session.commit()
                bot_logger.info(f"New user registered: {user.id}")
            else:
                # 更新现有用户信息
                existing_user.username = user.username
                existing_user.first_name = user.first_name
                existing_user.last_name = user.last_name
                existing_user.last_active_at = datetime.utcnow()
                existing_user.is_active = True
                await session.commit()
                bot_logger.info(f"User updated: {user.id}")

    except Exception as e:
        bot_logger.error(f"Error registering user {user.id}: {e}", exc_info=True)

    # 发送欢迎消息
    welcome_message = f"""
欢迎使用加密货币价格监控机器人！

我是您的 Binance 行情监控助手，可以帮您：

*核心功能：*
• 实时价格查询
• 价格阈值预警
• 百分比涨跌监控
• 定时价格汇报

*数据来源：* Binance 现货市场

*快速开始：*
/help - 查看完整指令列表
/price BTC - 查询 BTC 当前价格
/add - 创建监控任务

让我们开始吧！
"""

    await update.message.reply_text(welcome_message, parse_mode='Markdown')


async def help_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """
    /help 指令处理器
    显示帮助文档
    """
    help_text = """
*可用指令列表：*

*基础查询*
/price <symbol> - 查询实时价格
   示例：/price BTC 或 /price ETH

/help - 显示此帮助信息

*监控任务管理*
/add <币种> price <阈值> - 创建价格阈值监控
   示例：/add BTC price 50000
   示例：/add ETH price 3500 2800

/add <币种> percent <参考价> <涨%> <跌%> - 创建百分比监控
   示例：/add BTC percent 90000 5 -5

/list - 查看所有监控任务

/delete <任务ID> - 删除监控任务
   示例：/delete 1

*功能说明：*

📊 *价格阈值监控*
设置上限或下限价格，突破时自动预警

📈 *百分比涨跌监控*
基于参考价格，涨跌达到指定百分比时预警

⏰ *定时价格汇报*
每5分钟自动推送BTC、ETH、ADA价格到群组

*注意事项：*
• 所有价格数据来源于 Binance
• 每个监控任务有5分钟冷却时间
• 数据与 TradingView 保持一致

有问题？请联系开发者
"""

    await update.message.reply_text(help_text, parse_mode='Markdown')


__all__ = ['start_command', 'help_command']
