"""
查询功能指令处理器
包含价格查询等功能
"""
from telegram import Update
from telegram.ext import ContextTypes

from src.exchange.cryptocompare_client import cryptocompare_client
from src.notifier.message_formatter import MessageFormatter
from src.utils.logger import bot_logger
from src.utils.exceptions import BinanceAPIError, InvalidSymbolError


async def price_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """
    /price 指令处理器
    查询实时价格

    用法: /price BTC 或 /price ETH
    """
    user_id = update.effective_user.id

    # 检查参数
    if not context.args:
        await update.message.reply_text(
            "请提供币种名称\n\n"
            "用法：\n"
            "/price BTC\n"
            "/price ETH\n"
            "/price SOL"
        )
        return

    symbol = context.args[0].strip()

    try:
        # 发送加载消息
        loading_msg = await update.message.reply_text(
            f"正在查询 {symbol.upper()} 价格..."
        )

        # 获取 24h ticker 数据（来自 Binance）
        ticker_data = await cryptocompare_client.get_24h_ticker(symbol)

        # 格式化并发送结果
        message = MessageFormatter.format_price_info(ticker_data)

        # 删除加载消息
        await loading_msg.delete()

        # 发送结果
        await update.message.reply_text(message, parse_mode='Markdown')

        bot_logger.info(f"User {user_id} queried price for {symbol}")

    except InvalidSymbolError as e:
        await loading_msg.delete()
        error_msg = MessageFormatter.format_error(
            f"无效的币种: {symbol}\n\n"
            f"请检查币种名称是否正确\n"
            f"支持的币种: BTC, ETH, SOL, DOGE 等"
        )
        await update.message.reply_text(error_msg)
        bot_logger.warning(f"User {user_id} queried invalid symbol: {symbol}")

    except BinanceAPIError as e:
        await loading_msg.delete()
        error_msg = MessageFormatter.format_error(
            "无法获取价格数据，请稍后再试"
        )
        await update.message.reply_text(error_msg)
        bot_logger.error(f"API error for {symbol}: {e}")

    except Exception as e:
        await loading_msg.delete()
        error_msg = MessageFormatter.format_error("发生未知错误")
        await update.message.reply_text(error_msg)
        bot_logger.error(f"Unexpected error in price_command: {e}", exc_info=True)


__all__ = ['price_command']
