"""
CoinGecko API 客户端封装
免费、无地理限制的加密货币价格数据源
"""
import aiohttp
from typing import Dict, List, Optional, Any

from src.utils.logger import exchange_logger
from src.utils.exceptions import BinanceAPIError, InvalidSymbolError


class CoinGeckoClient:
    """CoinGecko API 客户端"""

    def __init__(self):
        """初始化客户端"""
        self.base_url = "https://api.coingecko.com/api/v3"
        self.session: Optional[aiohttp.ClientSession] = None

        # 常见交易对符号到 CoinGecko ID 的映射
        self.symbol_map = {
            'BTC': 'bitcoin',
            'ETH': 'ethereum',
            'USDT': 'tether',
            'BNB': 'binancecoin',
            'SOL': 'solana',
            'XRP': 'ripple',
            'ADA': 'cardano',
            'DOGE': 'dogecoin',
            'AVAX': 'avalanche-2',
            'DOT': 'polkadot',
            'MATIC': 'matic-network',
            'LINK': 'chainlink',
            'UNI': 'uniswap',
            'LTC': 'litecoin',
            'ATOM': 'cosmos',
            'ETC': 'ethereum-classic',
            'XLM': 'stellar',
            'NEAR': 'near',
            'ALGO': 'algorand',
            'BCH': 'bitcoin-cash',
            'FIL': 'filecoin',
            'APT': 'aptos',
            'ARB': 'arbitrum',
            'OP': 'optimism',
            'IMX': 'immutable-x',
            'STX': 'blockstack',
            'HBAR': 'hedera-hashgraph',
            'VET': 'vechain',
            'GRT': 'the-graph',
            'SAND': 'the-sandbox',
            'MANA': 'decentraland',
            'AAVE': 'aave',
            'RUNE': 'thorchain',
        }

        exchange_logger.info("CoinGecko client created")

    async def _get_session(self) -> aiohttp.ClientSession:
        """获取或创建 aiohttp session"""
        if self.session is None or self.session.closed:
            timeout = aiohttp.ClientTimeout(total=30, connect=10)
            self.session = aiohttp.ClientSession(timeout=timeout)
        return self.session

    async def _request(self, endpoint: str, params: Optional[Dict] = None) -> Dict:
        """
        发送 HTTP GET 请求到 CoinGecko API

        Args:
            endpoint: API 端点
            params: 查询参数

        Returns:
            JSON 响应数据
        """
        session = await self._get_session()
        url = f"{self.base_url}{endpoint}"

        try:
            async with session.get(url, params=params) as response:
                if response.status == 429:
                    raise BinanceAPIError("API rate limit exceeded, please try again later")

                if response.status != 200:
                    text = await response.text()
                    raise BinanceAPIError(f"API error {response.status}: {text}")

                data = await response.json()
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
        解析交易对符号，转换为 CoinGecko ID

        Args:
            symbol: 如 BTC, BTCUSDT, bitcoin

        Returns:
            CoinGecko coin ID
        """
        symbol = symbol.upper().strip()

        # 移除 USDT 后缀
        if symbol.endswith('USDT'):
            symbol = symbol[:-4]

        # 查找映射
        if symbol in self.symbol_map:
            return self.symbol_map[symbol]

        # 如果是完整名称，直接返回小写
        return symbol.lower()

    async def get_current_price(self, symbol: str) -> float:
        """
        获取当前价格

        Args:
            symbol: 交易对符号，如 BTC, BTCUSDT

        Returns:
            当前价格（USD）
        """
        try:
            coin_id = self._parse_symbol(symbol)

            data = await self._request(
                '/simple/price',
                {'ids': coin_id, 'vs_currencies': 'usd'}
            )

            if coin_id not in data:
                raise InvalidSymbolError(f"Invalid symbol: {symbol}")

            price = float(data[coin_id]['usd'])
            exchange_logger.debug(f"Got price for {symbol} ({coin_id}): ${price}")
            return price

        except InvalidSymbolError:
            raise
        except Exception as e:
            exchange_logger.error(f"Error getting price for {symbol}: {e}")
            raise BinanceAPIError(f"Failed to get price: {e}")

    async def get_24h_ticker(self, symbol: str) -> Dict[str, Any]:
        """
        获取 24 小时行情数据

        Args:
            symbol: 交易对符号

        Returns:
            行情数据字典
        """
        try:
            coin_id = self._parse_symbol(symbol)

            # 获取详细市场数据
            data = await self._request(f'/coins/{coin_id}')

            market_data = data.get('market_data', {})
            current_price = market_data.get('current_price', {}).get('usd', 0)
            price_change_24h = market_data.get('price_change_24h', 0)
            price_change_percentage_24h = market_data.get('price_change_percentage_24h', 0)
            high_24h = market_data.get('high_24h', {}).get('usd', 0)
            low_24h = market_data.get('low_24h', {}).get('usd', 0)
            total_volume = market_data.get('total_volume', {}).get('usd', 0)

            return {
                'symbol': symbol.upper(),
                'lastPrice': float(current_price),
                'priceChange': float(price_change_24h),
                'priceChangePercent': float(price_change_percentage_24h),
                'highPrice': float(high_24h),
                'lowPrice': float(low_24h),
                'volume': float(total_volume)
            }

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

    async def search_symbols(self, query: str) -> List[str]:
        """
        搜索交易对

        Args:
            query: 搜索关键词

        Returns:
            匹配的交易对列表
        """
        try:
            data = await self._request('/search', {'query': query})

            coins = data.get('coins', [])
            results = []

            for coin in coins[:20]:  # 最多返回 20 个
                symbol = coin.get('symbol', '').upper()
                name = coin.get('name', '')
                results.append(f"{symbol} - {name}")

            return results

        except Exception as e:
            exchange_logger.error(f"Error searching symbols: {e}")
            return []

    async def close(self):
        """关闭 aiohttp session"""
        if self.session and not self.session.closed:
            await self.session.close()
            exchange_logger.info("CoinGecko client session closed")


# 全局客户端实例
coingecko_client = CoinGeckoClient()

__all__ = ['CoinGeckoClient', 'coingecko_client']
