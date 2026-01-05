#!/usr/bin/env python3
"""
Web管理后台启动脚本
"""
import asyncio
import sys
import os

# 添加项目根目录到Python路径
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from web.server import start_web_server


async def main():
    """主函数"""
    print("=" * 70)
    print("  加密货币监控 Web 管理后台")
    print("  Crypto Monitoring Web Dashboard")
    print("=" * 70)
    print()

    # 启动Web服务器
    print("正在启动Web服务器...")
    runner = await start_web_server(host='0.0.0.0', port=8888)
    print("✓ Web服务器启动成功")
    print()

    print("=" * 70)
    print("  🎉 Web管理后台已启动!")
    print()
    print("  📱 访问地址:")
    print("     http://localhost:8080")
    print("     http://0.0.0.0:8080")
    print()
    print("  按 Ctrl+C 停止服务器")
    print("=" * 70)
    print()

    try:
        # 保持运行
        await asyncio.Event().wait()
    except KeyboardInterrupt:
        print("\n正在关闭服务器...")
        await runner.cleanup()
        print("✓ 服务器已关闭")


if __name__ == '__main__':
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        print("\n程序已退出")
