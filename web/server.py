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
import secrets
import hmac
import hashlib
from pathlib import Path

from src.database.connection import db_manager
from src.database.models import MonitorTask, AlertHistory, User, ReportConfig, Base
from src.exchange.price_api_manager import price_api_manager
from src.utils.logger import exchange_logger
from config.settings import settings
from sqlalchemy import select, func


class WebDashboardAPI:
    """Web管理后台API"""

    def __init__(self):
        self.app = web.Application()
        self.csrf_secret = secrets.token_bytes(32)
        self.setup_middlewares()
        self.setup_routes()
        self.setup_static()

    def setup_middlewares(self):
        """设置中间件（按顺序执行）"""
        self.app.middlewares.append(self.error_handling_middleware)
        self.app.middlewares.append(self.security_headers_middleware)
        self.app.middlewares.append(self.auth_middleware)
        self.app.middlewares.append(self.csrf_middleware)

    @web.middleware
    async def error_handling_middleware(self, request, handler):
        """统一错误处理中间件"""
        try:
            return await handler(request)
        except web.HTTPException:
            # HTTP异常直接抛出
            raise
        except Exception as e:
            # 记录详细错误到日志
            exchange_logger.error(f"Unhandled error in {request.path}: {e}", exc_info=True)

            # 生产环境返回通用错误信息
            if settings.DEBUG:
                return web.json_response({
                    'error': 'Internal server error',
                    'message': str(e),
                    'type': type(e).__name__
                }, status=500)
            else:
                return web.json_response({
                    'error': 'Internal server error'
                }, status=500)

    @web.middleware
    async def security_headers_middleware(self, request, handler):
        """添加安全HTTP响应头"""
        response = await handler(request)

        # Content Security Policy - 防止XSS
        response.headers['Content-Security-Policy'] = (
            "default-src 'self'; "
            "script-src 'self'; "
            "style-src 'self' 'unsafe-inline' https://fonts.googleapis.com; "
            "font-src 'self' https://fonts.gstatic.com; "
            "img-src 'self' data:; "
            "connect-src 'self' ws://localhost:8888 wss://localhost:8888; "
            "frame-ancestors 'none'"
        )

        # 其他安全头
        response.headers['X-Content-Type-Options'] = 'nosniff'
        response.headers['X-Frame-Options'] = 'DENY'
        response.headers['X-XSS-Protection'] = '1; mode=block'
        response.headers['Referrer-Policy'] = 'strict-origin-when-cross-origin'
        response.headers['Permissions-Policy'] = 'geolocation=(), microphone=(), camera=()'

        # API响应不缓存
        if request.path.startswith('/api/'):
            response.headers['Cache-Control'] = 'no-store, no-cache, must-revalidate, private'
            response.headers['Pragma'] = 'no-cache'

        return response

    @web.middleware
    async def auth_middleware(self, request, handler):
        """认证中间件"""
        # 白名单：静态资源、首页、登录页面和登录接口不需要认证
        if (request.path.startswith('/static') or
            request.path == '/' or
            request.path == '/login.html' or
            request.path == '/api/login'):
            return await handler(request)

        # 检查Authorization header或cookie
        token = request.headers.get('Authorization')
        if token and token.startswith('Bearer '):
            token = token[7:]  # 移除 'Bearer ' 前缀
        else:
            token = request.cookies.get('auth_token')

        expected_token = settings.WEB_ADMIN_TOKEN

        # 验证token
        if not expected_token:
            # 如果未配置token，记录警告但允许访问（开发模式）
            if settings.DEBUG:
                exchange_logger.warning("WEB_ADMIN_TOKEN not configured, authentication disabled")
                return await handler(request)
            else:
                return web.json_response({'error': 'Authentication not configured'}, status=500)

        if not token or token != expected_token:
            return web.json_response({'error': 'Unauthorized'}, status=401)

        return await handler(request)

    @web.middleware
    async def csrf_middleware(self, request, handler):
        """CSRF保护中间件"""
        # GET、HEAD、OPTIONS请求不需要CSRF保护
        if request.method in ('GET', 'HEAD', 'OPTIONS'):
            return await handler(request)

        # 静态资源和登录不需要保护
        if request.path.startswith('/static') or request.path == '/api/login':
            return await handler(request)

        # 检查CSRF token
        token_header = request.headers.get('X-CSRF-Token')
        token_cookie = request.cookies.get('csrf_token')

        if not token_header or not token_cookie:
            return web.json_response({'error': 'CSRF token missing'}, status=403)

        # 验证token
        if not self._verify_csrf_token(token_cookie, token_header):
            return web.json_response({'error': 'CSRF token invalid'}, status=403)

        return await handler(request)

    def _generate_csrf_token(self) -> str:
        """生成CSRF token"""
        return secrets.token_urlsafe(32)

    def _verify_csrf_token(self, cookie_token: str, header_token: str) -> bool:
        """验证CSRF token"""
        return hmac.compare_digest(cookie_token, header_token)

    def _mask_username(self, username: Optional[str]) -> str:
        """脱敏用户名"""
        if not username or len(username) <= 5:
            return "***"
        return f"{username[:3]}***{username[-2:]}"

    def _validate_limit(self, limit_str: str, max_limit: int = 1000) -> int:
        """验证并返回limit参数"""
        try:
            limit = int(limit_str)
        except ValueError:
            raise web.HTTPBadRequest(text=json.dumps({'error': 'Invalid limit parameter'}),
                                    content_type='application/json')

        if limit < 1 or limit > max_limit:
            raise web.HTTPBadRequest(text=json.dumps({'error': f'Limit must be between 1 and {max_limit}'}),
                                    content_type='application/json')

        return limit

    def setup_routes(self):
        """设置API路由"""
        # 页面路由
        self.app.router.add_get('/', self.index_handler)
        self.app.router.add_get('/login.html', self.login_page_handler)

        # API路由
        self.app.router.add_post('/api/login', self.login_handler)
        self.app.router.add_get('/api/stats', self.stats_handler)
        self.app.router.add_get('/api/prices', self.prices_handler)
        self.app.router.add_get('/api/tasks', self.tasks_handler)
        self.app.router.add_post('/api/tasks', self.create_task_handler)
        self.app.router.add_delete('/api/tasks/{task_id}', self.delete_task_handler)
        self.app.router.add_get('/api/alerts', self.alerts_handler)
        self.app.router.add_get('/api/system', self.system_handler)
        self.app.router.add_get('/api/users', self.users_handler)
        self.app.router.add_get('/api/reports', self.reports_handler)
        self.app.router.add_post('/api/reports', self.update_report_config_handler)

    def setup_static(self):
        """设置静态文件服务"""
        web_dir = Path(__file__).parent
        static_dir = web_dir / 'static'
        templates_dir = web_dir / 'templates'

        self.app.router.add_static('/static', static_dir, name='static')

    async def login_page_handler(self, request):
        """登录页面处理器"""
        web_dir = Path(__file__).parent
        login_file = web_dir / 'templates' / 'login.html'

        with open(login_file, 'r', encoding='utf-8') as f:
            html_content = f.read()

        response = web.Response(text=html_content, content_type='text/html')
        return response

    async def index_handler(self, request):
        """首页处理器（设置CSRF token）"""
        web_dir = Path(__file__).parent
        index_file = web_dir / 'templates' / 'index.html'

        with open(index_file, 'r', encoding='utf-8') as f:
            html_content = f.read()

        # 生成并设置CSRF token
        csrf_token = self._generate_csrf_token()

        response = web.Response(text=html_content, content_type='text/html')
        response.set_cookie('csrf_token', csrf_token, httponly=False, secure=False, samesite='Strict')
        return response

    async def login_handler(self, request):
        """登录处理器"""
        try:
            data = await request.json()
        except json.JSONDecodeError:
            return web.json_response({'error': 'Invalid JSON'}, status=400)

        password = data.get('password')

        if not password:
            return web.json_response({'error': 'Password required'}, status=400)

        # 验证密码
        if password == settings.WEB_ADMIN_PASSWORD:
            token = settings.WEB_ADMIN_TOKEN

            if not token:
                return web.json_response({'error': 'Authentication not configured'}, status=500)

            response = web.json_response({'success': True, 'token': token})
            response.set_cookie('auth_token', token, httponly=True, secure=False, samesite='Strict', max_age=86400)
            return response

        return web.json_response({'error': 'Invalid password'}, status=401)

    async def stats_handler(self, request):
        """统计数据API"""
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

    async def prices_handler(self, request):
        """实时价格API"""
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

    async def tasks_handler(self, request):
        """监控任务列表API"""
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

    async def alerts_handler(self, request):
        """预警历史API（带输入验证）"""
        # 验证limit参数
        limit_str = request.query.get('limit', '50')
        limit = self._validate_limit(limit_str)

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

    async def system_handler(self, request):
        """系统状态API"""
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

    async def users_handler(self, request):
        """用户列表API（隐私保护）"""
        async with db_manager.get_session() as session:
            stmt = select(User)
            result = await session.execute(stmt)
            users = result.scalars().all()

            users_data = []
            for user in users:
                users_data.append({
                    'user_id': user.user_id,
                    # 脱敏用户名：仅显示前3位和末2位
                    'username': self._mask_username(user.username),
                    # 移除真实姓名以保护隐私
                    'created_at': user.created_at.isoformat() if user.created_at else None,
                    'task_count': len(user.monitor_tasks) if hasattr(user, 'monitor_tasks') else 0
                })

            return web.json_response(users_data)

    async def create_task_handler(self, request):
        """创建监控任务API"""
        try:
            data = await request.json()
        except json.JSONDecodeError:
            return web.json_response({'error': 'Invalid JSON'}, status=400)

        # 验证必需字段
        required_fields = ['user_id', 'symbol', 'rule_type', 'rule_config']
        for field in required_fields:
            if field not in data:
                return web.json_response({'error': f'Missing required field: {field}'}, status=400)

        async with db_manager.get_session() as session:
            # 创建新任务
            task = MonitorTask(
                user_id=data['user_id'],
                symbol=data['symbol'].upper(),
                rule_type=data['rule_type'],
                rule_config=data['rule_config'],
                status='ACTIVE',
                created_at=datetime.utcnow()
            )

            session.add(task)
            await session.commit()
            await session.refresh(task)

            return web.json_response({
                'success': True,
                'task_id': task.task_id,
                'message': '任务创建成功'
            })

    async def delete_task_handler(self, request):
        """删除监控任务API"""
        task_id = request.match_info.get('task_id')

        if not task_id:
            return web.json_response({'error': 'Missing task_id'}, status=400)

        try:
            task_id = int(task_id)
        except ValueError:
            return web.json_response({'error': 'Invalid task_id'}, status=400)

        async with db_manager.get_session() as session:
            stmt = select(MonitorTask).where(MonitorTask.task_id == task_id)
            result = await session.execute(stmt)
            task = result.scalar_one_or_none()

            if not task:
                return web.json_response({'error': 'Task not found'}, status=404)

            # 删除任务
            await session.delete(task)
            await session.commit()

            return web.json_response({
                'success': True,
                'message': '任务删除成功'
            })

    async def reports_handler(self, request):
        """汇报配置API"""
        async with db_manager.get_session() as session:
            stmt = select(ReportConfig)
            result = await session.execute(stmt)
            configs = result.scalars().all()

            configs_data = []
            for config in configs:
                configs_data.append({
                    'config_id': config.config_id,
                    'symbols': config.symbols,
                    'schedule_cron': config.schedule_cron,
                    'enabled': config.enabled,
                    'created_at': config.created_at.isoformat() if config.created_at else None
                })

            return web.json_response(configs_data)

    async def update_report_config_handler(self, request):
        """更新汇报配置API"""
        try:
            data = await request.json()
        except json.JSONDecodeError:
            return web.json_response({'error': 'Invalid JSON'}, status=400)

        symbols = data.get('symbols', ['BTC', 'ETH', 'ADA'])
        schedule_cron = data.get('schedule_cron', '*/5 * * * *')  # 默认每5分钟
        enabled = data.get('enabled', True)

        async with db_manager.get_session() as session:
            # 查找或创建配置
            stmt = select(ReportConfig).limit(1)
            result = await session.execute(stmt)
            config = result.scalar_one_or_none()

            if config:
                # 更新现有配置
                config.symbols = symbols
                config.schedule_cron = schedule_cron
                config.enabled = enabled
            else:
                # 创建新配置
                config = ReportConfig(
                    symbols=symbols,
                    schedule_cron=schedule_cron,
                    enabled=enabled,
                    created_at=datetime.utcnow()
                )
                session.add(config)

            await session.commit()

            return web.json_response({
                'success': True,
                'message': '汇报配置更新成功'
            })


async def start_web_server(host=None, port=None):
    """启动Web服务器（使用配置的绑定地址）"""
    host = host or settings.WEB_HOST
    port = port or settings.WEB_PORT

    # 安全警告
    if host == '0.0.0.0':
        exchange_logger.warning(
            "⚠️  WARNING: Web server is binding to 0.0.0.0 (all interfaces). "
            "This exposes the dashboard to the network. "
            "Consider using 127.0.0.1 for localhost-only access."
        )

    # 初始化数据库
    db_manager.initialize()
    await db_manager.create_tables()

    dashboard = WebDashboardAPI()

    runner = web.AppRunner(dashboard.app)
    await runner.setup()

    site = web.TCPSite(runner, host, port)
    await site.start()

    print(f"✓ Web Dashboard started at http://{host}:{port}")
    if host == '127.0.0.1':
        print(f"  Access locally: http://localhost:{port}")
        print(f"  To expose to network, set WEB_HOST=0.0.0.0 in .env")
    else:
        print(f"  Access from anywhere: http://{host}:{port}")

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
