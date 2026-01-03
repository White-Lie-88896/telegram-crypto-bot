"""
Cryptocompare API 客户端封装
使用 Binance 作为数据源，确保与 TradingView 数据一致
"""
import aiohttp
from typing import Dict, List, Optional, Any
from datetime import datetime

from src.utils.logger import exchange_logger
from src.utils.exceptions import BinanceAPIError, InvalidSymbolError


class CryptocompareClient:
    """Cryptocompare API 客户端（使用 Binance 数据源）"""

    def __init__(self):
        """初始化客户端"""
        self.base_url = "https://min-api.cryptocompare.com/data"
        self.session: Optional[aiohttp.ClientSession] = None
        self.exchange = "Binance"  # 固定使用 Binance 数据源

        exchange_logger.info(f"Cryptocompare client created (data source: {self.exchange})")

    async def _get_session(self) -> aiohttp.ClientSession:
        """获取或创建 aiohttp session"""
        if self.session is None or self.session.closed:
            timeout = aiohttp.ClientTimeout(total=30, connect=10)
            self.session = aiohttp.ClientSession(timeout=timeout)
        return self.session

    async def _request(self, endpoint: str, params: Optional[Dict] = None) -> Dict:
        """
        发送 HTTP GET 请求到 Cryptocompare API

        Args:
            endpoint: API 端点
            params: 查询参数

        Returns:
            JSON 响应数据
        """
        session = await self._get_session()
        url = f"{self.base_url}{endpoint}"

        # 添加交易所参数
        if params is None:
            params = {}
        params['e'] = self.exchange

        try:
            async with session.get(url, params=params) as response:
                if response.status == 429:
                    raise BinanceAPIError("API rate limit exceeded, please try again later")

                if response.status != 200:
                    text = await response.text()
                    raise BinanceAPIError(f"API error {response.status}: {text}")

                data = await response.json()

                # 检查 API 错误响应
                if 'Response' in data and data['Response'] == 'Error':
                    error_msg = data.get('Message', 'Unknown error')
                    raise BinanceAPIError(f"API error: {error_msg}")

                return data

        except aiohttp.ClientError as e:
            exchange_logger.error(f"HTTP request failed: {e}")
            raise BinanceAPIError(f"Network error: {e}")
        except Exception as e:
            if isinstance(e, BinanceAPIError):
                raise
            exchange_logger.error(f"Unexpected error in API request: {e}")
            raise BinanceAPIError(f"Request failed: {e}")

    def _parse_symbol(self, symbol: str) -> str:
        """
        解析交易对符号

        Args:
            symbol: 如 BTC, BTCUSDT, bitcoin

        Returns:
            标准化的符号（如 BTC）
        """
        symbol = symbol.upper().strip()

        # 移除 USDT 后缀
        if symbol.endswith('USDT'):
            symbol = symbol[:-4]

        return symbol

    async def get_current_price(self, symbol: str) -> float:
        """
        获取当前价格

        Args:
            symbol: 交易对符号，如 BTC, BTCUSDT

        Returns:
            当前价格（USDT）
        """
        try:
            symbol = self._parse_symbol(symbol)

            data = await self._request(
                '/price',
                {'fsym': symbol, 'tsyms': 'USDT'}
            )

            if 'USDT' not in data:
                raise InvalidSymbolError(f"Invalid symbol: {symbol}")

            price = float(data['USDT'])
            exchange_logger.debug(f"Got price for {symbol} from {self.exchange}: ${price}")
            return price

        except InvalidSymbolError:
            raise
        except Exception as e:
            exchange_logger.error(f"Error getting price for {symbol}: {e}")
            raise BinanceAPIError(f"Failed to get price: {e}")

    async def get_24h_ticker(self, symbol: str) -> Dict[str, Any]:
        """
        获取 24 小时行情数据（从 Binance）

        Args:
            symbol: 交易对符号

        Returns:
            行情数据字典
        """
        try:
            symbol = self._parse_symbol(symbol)

            # 获取详细市场数据
            data = await self._request(
                '/pricemultifull',
                {'fsyms': symbol, 'tsyms': 'USDT'}
            )

            if 'RAW' not in data or symbol not in data['RAW'] or 'USDT' not in data['RAW'][symbol]:
                raise InvalidSymbolError(f"Invalid symbol: {symbol}")

            ticker = data['RAW'][symbol]['USDT']

            # 确认数据来自 Binance
            if ticker.get('MARKET') != 'Binance':
                exchange_logger.warning(f"Data source is {ticker.get('MARKET')}, not Binance")

            return {
                'symbol': f"{symbol}USDT",
                'lastPrice': float(ticker.get('PRICE', 0)),
                'priceChange': float(ticker.get('CHANGE24HOUR', 0)),
                'priceChangePercent': float(ticker.get('CHANGEPCT24HOUR', 0)),
                'highPrice': float(ticker.get('HIGH24HOUR', 0)),
                'lowPrice': float(ticker.get('LOW24HOUR', 0)),
                'volume': float(ticker.get('VOLUME24HOUR', 0)),
                'quoteVolume': float(ticker.get('VOLUME24HOURTO', 0)),
                'openPrice': float(ticker.get('OPEN24HOUR', 0)),
                'market': ticker.get('MARKET', 'Unknown'),
                'lastUpdate': datetime.fromtimestamp(ticker.get('LASTUPDATE', 0))
            }

        except InvalidSymbolError:
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
            await self.get_current_price(symbol)
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
        获取 K 线数据（历史数据）

        Args:
            symbol: 交易对
            interval: 时间间隔 (支持: minute, hour, day)
            limit: 返回数量

        Returns:
            K线数据列表
        """
        try:
            symbol = self._parse_symbol(symbol)

            # 转换时间间隔格式
            interval_map = {
                '1m': ('minute', 1),
                '5m': ('minute', 5),
                '15m': ('minute', 15),
                '1h': ('hour', 1),
                '4h': ('hour', 4),
                '1d': ('day', 1)
            }

            if interval not in interval_map:
                interval = '1h'

            aggregate_type, aggregate_value = interval_map[interval]

            # Cryptocompare 使用不同的端点
            endpoint_map = {
                'minute': '/v2/histominute',
                'hour': '/v2/histohour',
                'day': '/v2/histoday'
            }

            endpoint = endpoint_map[aggregate_type]

            data = await self._request(
                endpoint,
                {
                    'fsym': symbol,
                    'tsym': 'USDT',
                    'limit': limit,
                    'aggregate': aggregate_value
                }
            )

            if 'Data' not in data or 'Data' not in data['Data']:
                return []

            result = []
            for candle in data['Data']['Data']:
                result.append({
                    'openTime': candle['time'] * 1000,
                    'open': float(candle['open']),
                    'high': float(candle['high']),
                    'low': float(candle['low']),
                    'close': float(candle['close']),
                    'volume': float(candle['volumefrom']),
                    'closeTime': (candle['time'] + (aggregate_value * 60 if aggregate_type == 'minute' else aggregate_value * 3600 if aggregate_type == 'hour' else aggregate_value * 86400)) * 1000
                })

            return result

        except Exception as e:
            exchange_logger.error(f"Error getting klines for {symbol}: {e}")
            raise BinanceAPIError(f"Failed to get klines: {e}")

    async def search_symbols(self, query: str) -> List[str]:
        """
        搜索交易对

        Args:
            query: 搜索关键词

        Returns:
            匹配的交易对列表
        """
        try:
            # Cryptocompare 不提供搜索功能，返回常见交易对
            common_symbols = [
                'BTC', 'ETH', 'BNB', 'SOL', 'XRP', 'ADA', 'DOGE', 'AVAX',
                'DOT', 'MATIC', 'LINK', 'UNI', 'LTC', 'ATOM', 'ETC', 'XLM',
                'NEAR', 'ALGO', 'BCH', 'FIL', 'APT', 'ARB', 'OP', 'HBAR'
            ]

            query = query.upper()
            results = [s for s in common_symbols if query in s]
            return results[:20]

        except Exception as e:
            exchange_logger.error(f"Error searching symbols: {e}")
            return []

    async def close(self):
        """关闭 aiohttp session"""
        if self.session and not self.session.closed:
            await self.session.close()
            exchange_logger.info("Cryptocompare client session closed")


# 全局客户端实例
cryptocompare_client = CryptocompareClient()

__all__ = ['CryptocompareClient', 'cryptocompare_client']
