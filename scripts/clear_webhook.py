#!/usr/bin/env python3
"""
清除 Telegram Bot Webhook 并测试连接
"""
import sys
sys.path.insert(0, '/opt/tgbotbinance')

from config.settings import settings
import requests

def clear_webhook():
    """清除 webhook"""
    token = settings.TELEGRAM_BOT_TOKEN
    url = f"https://api.telegram.org/bot{token}/deleteWebhook"

    print("Clearing webhook...")
    response = requests.post(url, params={'drop_pending_updates': True})
    result = response.json()

    if result.get('ok'):
        print("✅ Webhook cleared successfully!")
    else:
        print(f"❌ Failed to clear webhook: {result}")

    return result.get('ok', False)

def get_me():
    """测试 Bot 连接"""
    token = settings.TELEGRAM_BOT_TOKEN
    url = f"https://api.telegram.org/bot{token}/getMe"

    print("\nTesting Bot connection...")
    response = requests.get(url)
    result = response.json()

    if result.get('ok'):
        bot_info = result['result']
        print(f"✅ Bot connected successfully!")
        print(f"   Bot Name: {bot_info.get('first_name')}")
        print(f"   Username: @{bot_info.get('username')}")
        print(f"   Bot ID: {bot_info.get('id')}")
    else:
        print(f"❌ Failed to connect: {result}")

    return result.get('ok', False)

if __name__ == "__main__":
    clear_webhook()
    get_me()

    print("\n" + "="*50)
    print("Now you can run the Bot:")
    print("  ./venv/bin/python main.py")
    print("="*50)
