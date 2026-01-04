"""
价格API管理器
支持多API源的故障转移机制和价格缓存
"""
from typing import Dict, Any, Optional
import asyncio
from datetime import datetime, timedelta

from src.exchange.cryptocompare_client import cryptocompare_client
from src.exchange.coingecko_client import coingecko_client
from src.exchange.binance_client import binance_client
from src.utils.logger import exchange_logger
from src.utils.exceptions import BinanceAPIError


class PriceAPIManager:
    """
    价格API管理器

    支持多个API源的自动故障转移：
    1. Cryptocompare (Binance数据源) - 主API
    2. CoinGecko - 备用API1
    3. Binance直接API - 备用API2

    价格缓存机制：
    - 缓存时间：30秒
    - 减少API调用频率
    - 多任务共享缓存
    """

    def __init__(self):
        """初始化API管理器"""
        self.apis = [
            ('Cryptocompare', cryptocompare_client),
            ('CoinGecko', coingecko_client),
            ('Binance', binance_client),
        ]

        # 记录当前可用的API（用于优先选择）
        self.current_api_index = 0

        # 价格缓存：{symbol: {'price': float, 'timestamp': datetime}}
        self.price_cache: Dict[str, Dict[str, Any]] = {}
        self.cache_duration = timedelta(seconds=30)  # 缓存30秒

        # Ticker数据缓存
        self.ticker_cache: Dict[str, Dict[str, Any]] = {}

        exchange_logger.info(f"Price API Manager initialized with {len(self.apis)} API sources and 30s cache")

    async def get_current_price(self, symbol: str) -> float:
        """
        获取当前价格（带缓存和故障转移）

        Args:
            symbol: 交易对符号

        Returns:
            当前价格

        Raises:
            BinanceAPIError: 所有API都失败时抛出
        """
        # 检查缓存
        if symbol in self.price_cache:
            cached_data = self.price_cache[symbol]
            cache_age = datetime.utcnow() - cached_data['timestamp']

            if cache_age < self.cache_duration:
                exchange_logger.debug(f"Using cached price for {symbol}: ${cached_data['price']} (age: {cache_age.total_seconds():.1f}s)")
                return cached_data['price']
            else:
                exchange_logger.debug(f"Cache expired for {symbol} (age: {cache_age.total_seconds():.1f}s)")

        errors = []

        # 从当前可用API开始尝试
        for attempt in range(len(self.apis)):
            api_index = (self.current_api_index + attempt) % len(self.apis)
            api_name, api_client = self.apis[api_index]

            try:
                exchange_logger.debug(f"Trying {api_name} for {symbol}")
                price = await api_client.get_current_price(symbol)

                # 成功！更新当前可用API
                if api_index != self.current_api_index:
                    exchange_logger.info(f"Switched to {api_name} as primary API")
                    self.current_api_index = api_index

                # 更新缓存
                self.price_cache[symbol] = {
                    'price': price,
                    'timestamp': datetime.utcnow()
                }

                exchange_logger.debug(f"Got price from {api_name}: {symbol} = ${price} (cached)")
                return price

            except Exception as e:
                error_msg = f"{api_name} failed: {str(e)}"
                errors.append(error_msg)
                exchange_logger.warning(error_msg)

                # 如果不是最后一个API，继续尝试
                if attempt < len(self.apis) - 1:
                    exchange_logger.info(f"Falling back to next API...")
                    continue

        # 所有API都失败
        error_summary = "; ".join(errors)
        exchange_logger.error(f"All APIs failed for {symbol}: {error_summary}")
        raise BinanceAPIError(f"Failed to get price from all sources: {error_summary}")

    async def get_24h_ticker(self, symbol: str) -> Dict[str, Any]:
        """
        获取24小时行情数据（带缓存和故障转移）

        Args:
            symbol: 交易对符号

        Returns:
            行情数据字典

        Raises:
            BinanceAPIError: 所有API都失败时抛出
        """
        # 检查缓存
        if symbol in self.ticker_cache:
            cached_data = self.ticker_cache[symbol]
            cache_age = datetime.utcnow() - cached_data['timestamp']

            if cache_age < self.cache_duration:
                exchange_logger.debug(f"Using cached ticker for {symbol} (age: {cache_age.total_seconds():.1f}s)")
                return cached_data['ticker']
            else:
                exchange_logger.debug(f"Ticker cache expired for {symbol} (age: {cache_age.total_seconds():.1f}s)")

        errors = []

        # 从当前可用API开始尝试
        for attempt in range(len(self.apis)):
            api_index = (self.current_api_index + attempt) % len(self.apis)
            api_name, api_client = self.apis[api_index]

            try:
                exchange_logger.debug(f"Trying {api_name} for ticker {symbol}")
                ticker = await api_client.get_24h_ticker(symbol)

                # 成功！更新当前可用API
                if api_index != self.current_api_index:
                    exchange_logger.info(f"Switched to {api_name} as primary API")
                    self.current_api_index = api_index

                # 更新缓存
                self.ticker_cache[symbol] = {
                    'ticker': ticker,
                    'timestamp': datetime.utcnow()
                }

                exchange_logger.debug(f"Got ticker from {api_name}: {symbol} (cached)")
                return ticker

            except Exception as e:
                error_msg = f"{api_name} failed: {str(e)}"
                errors.append(error_msg)
                exchange_logger.warning(error_msg)

                # 如果不是最后一个API，继续尝试
                if attempt < len(self.apis) - 1:
                    exchange_logger.info(f"Falling back to next API...")
                    continue

        # 所有API都失败
        error_summary = "; ".join(errors)
        exchange_logger.error(f"All APIs failed for ticker {symbol}: {error_summary}")
        raise BinanceAPIError(f"Failed to get ticker from all sources: {error_summary}")

    async def validate_symbol(self, symbol: str) -> bool:
        """
        验证交易对是否有效

        Args:
            symbol: 交易对

        Returns:
            True if valid, False otherwise
        """
        try:
            await self.get_current_price(symbol)
            return True
        except:
            return False

    async def get_multiple_prices(self, symbols: list) -> Dict[str, float]:
        """
        批量获取多个币种价格

        Args:
            symbols: 币种列表

        Returns:
            {symbol: price} 字典，失败的币种价格为None
        """
        tasks = []
        for symbol in symbols:
            task = self._get_price_safe(symbol)
            tasks.append(task)

        results = await asyncio.gather(*tasks, return_exceptions=True)

        prices = {}
        for i, symbol in enumerate(symbols):
            if isinstance(results[i], Exception):
                prices[symbol] = None
                exchange_logger.error(f"Failed to get price for {symbol}: {results[i]}")
            else:
                prices[symbol] = results[i]

        return prices

    async def _get_price_safe(self, symbol: str) -> Optional[float]:
        """
        安全地获取价格（不抛出异常）

        Args:
            symbol: 交易对符号

        Returns:
            价格或None
        """
        try:
            return await self.get_current_price(symbol)
        except Exception as e:
            exchange_logger.error(f"Error getting price for {symbol}: {e}")
            return None

    async def close(self):
        """关闭所有API客户端"""
        for api_name, api_client in self.apis:
            try:
                await api_client.close()
                exchange_logger.info(f"{api_name} client closed")
            except Exception as e:
                exchange_logger.error(f"Error closing {api_name} client: {e}")

    def get_current_api_name(self) -> str:
        """获取当前使用的API名称"""
        return self.apis[self.current_api_index][0]


# 全局API管理器实例
price_api_manager = PriceAPIManager()

__all__ = ['PriceAPIManager', 'price_api_manager']
