"""
Web管理后台API服务器
提供RESTful API接口供前端调用
"""
import asyncio
from datetime import datetime
from typing import Dict, List, Optional
from aiohttp import web
import json
import os
from pathlib import Path

from src.database.connection import db_manager
from src.database.models import MonitorTask, AlertHistory, User, ReportConfig
from src.exchange.price_api_manager import price_api_manager
from sqlalchemy import select, func


class WebDashboardAPI:
    """Web管理后台API"""

    def __init__(self):
        self.app = web.Application()
        self.setup_routes()
        self.setup_static()

    def setup_routes(self):
        """设置API路由"""
        self.app.router.add_get('/', self.index_handler)
        self.app.router.add_get('/api/stats', self.stats_handler)
        self.app.router.add_get('/api/prices', self.prices_handler)
        self.app.router.add_get('/api/tasks', self.tasks_handler)
        self.app.router.add_get('/api/alerts', self.alerts_handler)
        self.app.router.add_get('/api/system', self.system_handler)
        self.app.router.add_get('/api/users', self.users_handler)

    def setup_static(self):
        """设置静态文件服务"""
        web_dir = Path(__file__).parent
        static_dir = web_dir / 'static'
        templates_dir = web_dir / 'templates'

        self.app.router.add_static('/static', static_dir, name='static')

    async def index_handler(self, request):
        """首页处理器"""
        web_dir = Path(__file__).parent
        index_file = web_dir / 'templates' / 'index.html'

        with open(index_file, 'r', encoding='utf-8') as f:
            html_content = f.read()

        return web.Response(text=html_content, content_type='text/html')

    async def stats_handler(self, request):
        """统计数据API"""
        try:
            async with db_manager.get_session() as session:
                # 活跃任务数
                active_tasks_query = select(func.count()).select_from(MonitorTask).where(
                    MonitorTask.status == 'ACTIVE'
                )
                active_tasks_result = await session.execute(active_tasks_query)
                active_tasks = active_tasks_result.scalar()

                # 今日预警数
                today_start = datetime.utcnow().replace(hour=0, minute=0, second=0, microsecond=0)
                alerts_query = select(func.count()).select_from(AlertHistory).where(
                    AlertHistory.triggered_at >= today_start
                )
                alerts_result = await session.execute(alerts_query)
                alert_count = alerts_result.scalar()

                # 用户数
                users_query = select(func.count()).select_from(User)
                users_result = await session.execute(users_query)
                user_count = users_result.scalar()

                stats = {
                    'activeTasks': active_tasks or 0,
                    'alertCount': alert_count or 0,
                    'apiUptime': 98.5,  # 可以从监控系统获取
                    'userCount': user_count or 0
                }

                return web.json_response(stats)

        except Exception as e:
            return web.json_response({'error': str(e)}, status=500)

    async def prices_handler(self, request):
        """实时价格API"""
        try:
            symbols = ['BTC', 'ETH', 'SOL', 'ADA', 'BNB', 'XRP']
            prices = await price_api_manager.get_multiple_prices(symbols)

            # 模拟涨跌幅（实际应从数据库获取24h数据）
            price_data = {}
            for symbol, price in prices.items():
                price_data[symbol] = {
                    'price': price,
                    'change': 0.0,  # 实际应计算24h涨跌幅
                    'api_source': price_api_manager.last_api_used
                }

            return web.json_response(price_data)

        except Exception as e:
            return web.json_response({'error': str(e)}, status=500)

    async def tasks_handler(self, request):
        """监控任务列表API"""
        try:
            async with db_manager.get_session() as session:
                stmt = select(MonitorTask).where(MonitorTask.status == 'ACTIVE')
                result = await session.execute(stmt)
                tasks = result.scalars().all()

                tasks_data = []
                for task in tasks:
                    tasks_data.append({
                        'task_id': task.task_id,
                        'user_id': task.user_id,
                        'symbol': task.symbol,
                        'rule_type': task.rule_type,
                        'rule_config': task.rule_config,
                        'status': task.status,
                        'created_at': task.created_at.isoformat() if task.created_at else None,
                        'last_triggered_at': task.last_triggered_at.isoformat() if task.last_triggered_at else None
                    })

                return web.json_response(tasks_data)

        except Exception as e:
            return web.json_response({'error': str(e)}, status=500)

    async def alerts_handler(self, request):
        """预警历史API"""
        try:
            # 获取查询参数
            limit = int(request.query.get('limit', 50))

            async with db_manager.get_session() as session:
                stmt = select(AlertHistory).order_by(
                    AlertHistory.triggered_at.desc()
                ).limit(limit)
                result = await session.execute(stmt)
                alerts = result.scalars().all()

                alerts_data = []
                for alert in alerts:
                    alerts_data.append({
                        'alert_id': alert.alert_id,
                        'task_id': alert.task_id,
                        'user_id': alert.user_id,
                        'symbol': alert.symbol,
                        'trigger_price': float(alert.trigger_price),
                        'message': alert.message,
                        'sent_success': alert.sent_success,
                        'triggered_at': alert.triggered_at.isoformat() if alert.triggered_at else None
                    })

                return web.json_response(alerts_data)

        except Exception as e:
            return web.json_response({'error': str(e)}, status=500)

    async def system_handler(self, request):
        """系统状态API"""
        try:
            # 获取数据库大小
            db_path = 'data/crypto_bot.db'
            db_size = 0
            if os.path.exists(db_path):
                db_size = os.path.getsize(db_path)

            # 获取总记录数
            async with db_manager.get_session() as session:
                alerts_count = await session.execute(select(func.count()).select_from(AlertHistory))
                total_records = alerts_count.scalar()

            system_info = {
                'apiStatus': {
                    'Cryptocompare': 'online',
                    'CoinGecko': 'online',
                    'Binance': 'online'
                },
                'monitorEngine': {
                    'status': 'running',
                    'checkInterval': 30,
                    'lastCheck': datetime.utcnow().isoformat()
                },
                'database': {
                    'status': 'healthy',
                    'size': f'{db_size / 1024:.1f} KB',
                    'records': total_records or 0
                }
            }

            return web.json_response(system_info)

        except Exception as e:
            return web.json_response({'error': str(e)}, status=500)

    async def users_handler(self, request):
        """用户列表API"""
        try:
            async with db_manager.get_session() as session:
                stmt = select(User)
                result = await session.execute(stmt)
                users = result.scalars().all()

                users_data = []
                for user in users:
                    users_data.append({
                        'user_id': user.user_id,
                        'username': user.username,
                        'first_name': user.first_name,
                        'last_name': user.last_name,
                        'created_at': user.created_at.isoformat() if user.created_at else None
                    })

                return web.json_response(users_data)

        except Exception as e:
            return web.json_response({'error': str(e)}, status=500)


async def start_web_server(host='0.0.0.0', port=8080):
    """启动Web服务器"""
    dashboard = WebDashboardAPI()

    runner = web.AppRunner(dashboard.app)
    await runner.setup()

    site = web.TCPSite(runner, host, port)
    await site.start()

    print(f"Web Dashboard started at http://{host}:{port}")
    print(f"Access the dashboard: http://localhost:{port}")

    return runner


if __name__ == '__main__':
    # 独立运行Web服务器
    async def main():
        runner = await start_web_server()
        try:
            await asyncio.Event().wait()
        except KeyboardInterrupt:
            await runner.cleanup()

    asyncio.run(main())
