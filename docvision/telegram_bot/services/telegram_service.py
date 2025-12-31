"""
Telegram API service
Handles all communication with Telegram API
"""
import frappe
import requests
from frappe import _
from requests.adapters import HTTPAdapter
from urllib3.util.retry import Retry
import socket

# Force IPv4 to avoid "Network is unreachable" errors
# This happens when IPv6 is preferred but not properly configured
original_getaddrinfo = socket.getaddrinfo

def forced_ipv4_getaddrinfo(*args, **kwargs):
    """Force IPv4 address resolution"""
    responses = original_getaddrinfo(*args, **kwargs)
    return [r for r in responses if r[0] == socket.AF_INET] or responses

# Apply IPv4 monkey patch
socket.getaddrinfo = forced_ipv4_getaddrinfo


def get_telegram_session():
    """Create a requests session with retry logic and timeouts"""
    session = requests.Session()
    
    # Retry strategy: 3 retries with backoff
    retry_strategy = Retry(
        total=3,
        backoff_factor=1,  # 1s, 2s, 4s
        status_forcelist=[429, 500, 502, 503, 504],
        allowed_methods=["GET", "POST"]
    )
    
    adapter = HTTPAdapter(max_retries=retry_strategy)
    session.mount("https://", adapter)
    session.mount("http://", adapter)
    
    return session


def get_telegram_image_url(file_id):
    """Get direct URL for a Telegram image file"""
    try:
        telegram_setting = frappe.get_single("Telegram Setting")
        bot_token = telegram_setting.get_password("telegram_bot_token")
        
        if not bot_token:
            return None
        
        session = get_telegram_session()
        file_info_response = session.get(
            f"https://api.telegram.org/bot{bot_token}/getFile",
            params={"file_id": file_id},
            timeout=(10, 30)  # (connect timeout, read timeout)
        )
        
        file_info = file_info_response.json()
        
        if not file_info.get('ok'):
            return None
        
        file_path = file_info['result']['file_path']
        image_url = f"https://api.telegram.org/file/bot{bot_token}/{file_path}"
        
        return image_url
        
    except requests.exceptions.Timeout:
        frappe.log_error(title="Telegram Timeout", message=f"Timeout getting file: {file_id}")
        return None
    except requests.exceptions.ConnectionError as e:
        frappe.log_error(title="Telegram Connection Error", message=f"Connection error: {str(e)[:200]}")
        return None
    except Exception as e:
        frappe.log_error(title="Telegram Image Error", message=str(e)[:500])
        return None


def send_telegram_message(chat_id, text):
    """Send message to Telegram chat"""
    try:
        telegram_setting = frappe.get_single("Telegram Setting")
        bot_token = telegram_setting.get_password("telegram_bot_token")
        
        if not bot_token:
            frappe.log_error(title="Telegram Send Error", message="Bot token not found")
            return
        
        bot_token = bot_token.strip()
        url = f"https://api.telegram.org/bot{bot_token}/sendMessage"
        
        session = get_telegram_session()
        response = session.post(
            url,
            json={
                "chat_id": chat_id,
                "text": text,
                "parse_mode": "HTML",
                "disable_web_page_preview": True
            },
            timeout=(10, 30)  # (connect timeout, read timeout)
        )
        
        if response.status_code != 200:
            frappe.log_error(
                title="Telegram Send Error",
                message=f"Status: {response.status_code}\nChat: {chat_id}\nResponse: {response.text[:200]}"
            )
        
    except requests.exceptions.ConnectionError as e:
        frappe.log_error(
            title="Telegram Connection Error",
            message=f"Chat: {chat_id}\nError: {str(e)[:300]}"
        )
    except Exception as e:
        frappe.log_error(
            title="Telegram Send Error",
            message=f"Chat: {chat_id}\nError: {str(e)[:300]}"
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
        
        session = get_telegram_session()
        info_response = session.get(
            f"https://api.telegram.org/bot{bot_token}/getWebhookInfo",
            timeout=(10, 30)
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
            
    except requests.exceptions.ConnectionError as e:
        return {
            "success": False,
            "message": f"Connection error: {str(e)[:200]}"
        }
    except Exception as e:
        frappe.log_error(title="Webhook Info Error", message=str(e)[:500])
        return {
            "success": False,
            "message": str(e)[:200]
        }
