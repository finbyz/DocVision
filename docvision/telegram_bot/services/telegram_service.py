"""
Telegram API service
Handles all communication with Telegram API
"""
import frappe
import requests
from frappe import _


def get_telegram_image_url(file_id):
    """Get direct URL for a Telegram image file"""
    try:
        telegram_setting = frappe.get_single("Telegram Setting")
        bot_token = telegram_setting.get_password("telegram_bot_token")
        
        if not bot_token:
            return None
        
        file_info_response = requests.get(
            f"https://api.telegram.org/bot{bot_token}/getFile",
            params={"file_id": file_id},
            timeout=15
        )
        
        file_info = file_info_response.json()
        
        if not file_info.get('ok'):
            return None
        
        file_path = file_info['result']['file_path']
        image_url = f"https://api.telegram.org/file/bot{bot_token}/{file_path}"
        
        return image_url
        
    except requests.exceptions.Timeout:
        return None
    except Exception as e:
        frappe.log_error(str(e), "Get Telegram Image Error")
        return None


def send_telegram_message(chat_id, text):
    """Send message to Telegram chat"""
    try:
        telegram_setting = frappe.get_single("Telegram Setting")
        bot_token = telegram_setting.get_password("telegram_bot_token")
        
        if not bot_token:
            frappe.log_error("Bot token not found in Telegram Setting", "Telegram Send Error")
            return
        
        bot_token = bot_token.strip()
        url = f"https://api.telegram.org/bot{bot_token}/sendMessage"
        
        response = requests.post(
            url,
            json={
                "chat_id": chat_id,
                "text": text,
                "parse_mode": "HTML",
                "disable_web_page_preview": True
            },
            timeout=10
        )
        
        if response.status_code != 200:
            frappe.log_error(
                f"Failed to send message.\n"
                f"Status: {response.status_code}\n"
                f"URL: {url}\n"
                f"Response: {response.text}\n"
                f"Chat ID: {chat_id}", 
                "Telegram Send Error"
            )
        
    except Exception as e:
        frappe.log_error(
            f"Exception: {str(e)}\n"
            f"Chat ID: {chat_id}\n"
            f"Message: {text[:100] if text else 'Empty'}", 
            "Telegram Send Error"
        )


def get_webhook_info():
    """Get current webhook information"""
    try:
        telegram_setting = frappe.get_single("Telegram Setting")
        bot_token = telegram_setting.get_password("telegram_bot_token")
        
        if not bot_token:
            return {
                "success": False,
                "message": "Bot token not found"
            }
        
        info_response = requests.get(
            f"https://api.telegram.org/bot{bot_token}/getWebhookInfo",
            timeout=10
        )
        
        webhook_info = info_response.json()
        
        if webhook_info.get('ok'):
            result = webhook_info.get('result', {})
            return {
                "success": True,
                "webhook_url": result.get('url', 'Not set'),
                "pending_update_count": result.get('pending_update_count', 0),
                "last_error_date": result.get('last_error_date'),
                "last_error_message": result.get('last_error_message'),
                "max_connections": result.get('max_connections', 40)
            }
        else:
            return {
                "success": False,
                "message": webhook_info.get('description', 'Failed to get webhook info')
            }
            
    except Exception as e:
        frappe.log_error(str(e), "Get Webhook Info Error")
        return {
            "success": False,
            "message": str(e)
        }
