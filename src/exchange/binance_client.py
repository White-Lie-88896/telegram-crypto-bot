"""
Binance API 客户端封装
使用直接 HTTP 请求绕过地理限制
"""
import asyncio
import aiohttp
from typing import Dict, List, Optional, Any

from config.settings import settings
from src.utils.logger import exchange_logger
from src.utils.exceptions import BinanceAPIError, InvalidSymbolError


class BinanceClient:
    """Binance API 客户端（使用 aiohttp 直接请求）"""

    def __init__(self):
        """初始化客户端"""
        self.base_url = "https://api.binance.com"
        self.session: Optional[aiohttp.ClientSession] = None
        exchange_logger.info("Binance client created (HTTP-based)")

    async def _get_session(self) -> aiohttp.ClientSession:
        """获取或创建 aiohttp session"""
        if self.session is None or self.session.closed:
            timeout = aiohttp.ClientTimeout(total=10)
            self.session = aiohttp.ClientSession(timeout=timeout)
        return self.session

    async def _request(self, endpoint: str, params: Optional[Dict] = None) -> Dict:
        """
        发送 HTTP GET 请求到 Binance API

        Args:
            endpoint: API 端点（如 /api/v3/ticker/price）
            params: 查询参数

        Returns:
            JSON 响应数据

        Raises:
            BinanceAPIError: API 错误
        """
        session = await self._get_session()
        url = f"{self.base_url}{endpoint}"

        try:
            async with session.get(url, params=params) as response:
                data = await response.json()

                if response.status != 200:
                    error_msg = data.get('msg', 'Unknown error')
                    error_code = data.get('code', response.status)
                    raise BinanceAPIError(f"API error {error_code}: {error_msg}")

                return data

        except aiohttp.ClientError as e:
            exchange_logger.error(f"HTTP request failed: {e}")
            raise BinanceAPIError(f"Network error: {e}")
        except Exception as e:
            exchange_logger.error(f"Unexpected error in API request: {e}")
            raise BinanceAPIError(f"Request failed: {e}")

    async def get_current_price(self, symbol: str) -> float:
        """
        获取当前价格（现货市场）

        Args:
            symbol: 交易对，如 BTCUSDT

        Returns:
            当前价格（float）

        Raises:
            BinanceAPIError: API 调用失败
            InvalidSymbolError: 无效的交易对
        """
        try:
            symbol = symbol.upper()
            data = await self._request('/api/v3/ticker/price', {'symbol': symbol})
            price = float(data['price'])
            exchange_logger.debug(f"Got price for {symbol}: {price}")
            return price

        except BinanceAPIError as e:
            if 'Invalid symbol' in str(e):
                raise InvalidSymbolError(f"Invalid symbol: {symbol}")
            raise
        except Exception as e:
            exchange_logger.error(f"Error getting price for {symbol}: {e}")
            raise BinanceAPIError(f"Failed to get price: {e}")

    async def get_24h_ticker(self, symbol: str) -> Dict[str, Any]:
        """
        获取 24 小时行情数据

        Args:
            symbol: 交易对

        Returns:
            行情数据字典，包含：
            - priceChange: 价格变化
            - priceChangePercent: 涨跌幅百分比
            - highPrice: 24h最高价
            - lowPrice: 24h最低价
            - volume: 24h成交量
            - lastPrice: 最新价格
        """
        try:
            symbol = symbol.upper()
            data = await self._request('/api/v3/ticker/24hr', {'symbol': symbol})

            return {
                'symbol': symbol,
                'lastPrice': float(data['lastPrice']),
                'priceChange': float(data['priceChange']),
                'priceChangePercent': float(data['priceChangePercent']),
                'highPrice': float(data['highPrice']),
                'lowPrice': float(data['lowPrice']),
                'volume': float(data['volume'])
            }

        except BinanceAPIError as e:
            if 'Invalid symbol' in str(e):
                raise InvalidSymbolError(f"Invalid symbol: {symbol}")
            raise
        except Exception as e:
            exchange_logger.error(f"Error getting 24h ticker for {symbol}: {e}")
            raise BinanceAPIError(f"Failed to get ticker: {e}")

    async def validate_symbol(self, symbol: str) -> bool:
        """
        验证交易对是否有效

        Args:
            symbol: 交易对

        Returns:
            True if valid, False otherwise
        """
        try:
            symbol = symbol.upper()
            await self._request('/api/v3/ticker/price', {'symbol': symbol})
            return True
        except:
            return False

    async def get_klines(
        self,
        symbol: str,
        interval: str = '1h',
        limit: int = 100
    ) -> List[Dict[str, Any]]:
        """
        获取 K 线数据

        Args:
            symbol: 交易对
            interval: 时间间隔 (1m, 5m, 15m, 1h, 4h, 1d, etc.)
            limit: 返回数量

        Returns:
            K线数据列表
        """
        try:
            symbol = symbol.upper()
            params = {
                'symbol': symbol,
                'interval': interval,
                'limit': limit
            }
            klines = await self._request('/api/v3/klines', params)

            # 转换为易用格式
            result = []
            for kline in klines:
                result.append({
                    'openTime': kline[0],
                    'open': float(kline[1]),
                    'high': float(kline[2]),
                    'low': float(kline[3]),
                    'close': float(kline[4]),
                    'volume': float(kline[5]),
                    'closeTime': kline[6]
                })

            return result

        except Exception as e:
            exchange_logger.error(f"Error getting klines for {symbol}: {e}")
            raise BinanceAPIError(f"Failed to get klines: {e}")

    async def search_symbols(self, query: str) -> List[str]:
        """
        搜索交易对（模糊匹配）

        Args:
            query: 搜索关键词

        Returns:
            匹配的交易对列表
        """
        try:
            query = query.upper()
            exchange_info = await self._request('/api/v3/exchangeInfo')

            # 过滤 USDT 交易对
            symbols = []
            for symbol_info in exchange_info['symbols']:
                symbol = symbol_info['symbol']
                if 'USDT' in symbol and symbol_info['status'] == 'TRADING':
                    if query in symbol:
                        symbols.append(symbol)

            return sorted(symbols)[:20]  # 最多返回 20 个

        except Exception as e:
            exchange_logger.error(f"Error searching symbols: {e}")
            return []

    async def close(self):
        """关闭 aiohttp session"""
        if self.session and not self.session.closed:
            await self.session.close()
            exchange_logger.info("Binance client session closed")


# 全局客户端实例
binance_client = BinanceClient()

__all__ = ['BinanceClient', 'binance_client']
