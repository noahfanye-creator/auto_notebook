import requests
import os
from loguru import logger

def send_telegram_msg(message: str):
    """
    发送消息到 Telegram Bot
    
    Args:
        message: 要发送的消息内容（支持 Markdown）
    """
    token = os.getenv("TELEGRAM_BOT_TOKEN")
    chat_id = os.getenv("TELEGRAM_CHAT_ID")
    
    if not token or not chat_id:
        logger.warning("⚠️ TELEGRAM_BOT_TOKEN 或 TELEGRAM_CHAT_ID 未设置，跳过发送消息")
        return False
        
    url = f"https://api.telegram.org/bot{token}/sendMessage"
    payload = {
        "chat_id": chat_id,
        "text": message,
        "parse_mode": "Markdown",
        "disable_web_page_preview": True
    }
    
    try:
        response = requests.post(url, json=payload, timeout=10)
        response.raise_for_status()
        data = response.json()
        if data.get("ok"):
            logger.info("✅ Telegram 消息发送成功")
            return True
        else:
            logger.error(f"❌ Telegram 消息发送失败: {data.get('description')}")
            return False
    except Exception as e:
        logger.error(f"❌ 发送 Telegram 消息出错: {e}")
        return False
