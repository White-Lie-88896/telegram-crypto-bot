#!/usr/bin/env python3
"""
彻底清除 Telegram Bot 的所有待处理更新
解决 Conflict 错误
"""
import sys
sys.path.insert(0, '/opt/tgbotbinance')

from config.settings import settings
import requests
import time

TOKEN = settings.TELEGRAM_BOT_TOKEN

def delete_webhook():
    """删除 webhook"""
    url = f"https://api.telegram.org/bot{TOKEN}/deleteWebhook"
    response = requests.post(url, params={'drop_pending_updates': True})
    result = response.json()
    print(f"Delete webhook: {result}")
    return result.get('ok', False)

def get_updates_with_offset():
    """获取并清除所有待处理的更新"""
    url = f"https://api.telegram.org/bot{TOKEN}/getUpdates"

    print("Fetching all pending updates...")
    max_attempts = 10

    for attempt in range(max_attempts):
        response = requests.get(url, params={'timeout': 1})
        result = response.json()

        if not result.get('ok'):
            print(f"Error: {result}")
            return False

        updates = result.get('result', [])

        if not updates:
            print(f"✅ No more pending updates (attempt {attempt + 1})")
            break

        # 获取最大的 update_id
        max_update_id = max(update['update_id'] for update in updates)
        print(f"   Found {len(updates)} updates, max ID: {max_update_id}")

        # 确认这些更新（通过获取 offset = max_update_id + 1）
        response = requests.get(url, params={'offset': max_update_id + 1, 'timeout': 1})
        time.sleep(0.5)

    print("✅ All pending updates cleared")
    return True

def test_bot():
    """测试 Bot 连接"""
    url = f"https://api.telegram.org/bot{TOKEN}/getMe"
    response = requests.get(url)
    result = response.json()

    if result.get('ok'):
        bot = result['result']
        print(f"\n✅ Bot ready: @{bot['username']}")
        return True
    else:
        print(f"\n❌ Bot test failed: {result}")
        return False

if __name__ == "__main__":
    print("=" * 60)
    print("Clearing all pending updates...")
    print("=" * 60)

    # 1. 删除 webhook
    delete_webhook()
    time.sleep(2)

    # 2. 清除所有待处理更新
    get_updates_with_offset()
    time.sleep(2)

    # 3. 测试连接
    test_bot()

    print("\n" + "=" * 60)
    print("Ready to start Bot!")
    print("=" * 60)
