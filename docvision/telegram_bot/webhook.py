"""
Main webhook handler for Telegram bot
Entry point for all incoming Telegram messages
"""
import hashlib
import hmac

import frappe
from docvision.telegram_bot.handlers.message_handler import handle_private_message, handle_group_message
from docvision.telegram_bot.services.telegram_service import send_telegram_message
from docvision.telegram_bot.utils.logging import log_exception


def webhook_secret(bot_token):
    """Secret registered with Telegram's setWebhook and sent back by Telegram on every update.

    Derived from the bot token so no extra setting is needed; changing the bot token
    changes the secret (re-save Telegram Setting to register it again).
    """
    return hashlib.sha256(f"docvision-telegram-webhook:{bot_token}".encode()).hexdigest()


@frappe.whitelist(allow_guest=True)
def telegram_webhook():
    """Main webhook endpoint for Telegram.

    Only requests carrying Telegram's X-Telegram-Bot-Api-Secret-Token header with our
    secret are processed, so nobody can forge updates by posting here directly.
    """
    bot_token = frappe.get_single("Telegram Setting").get_password("telegram_bot_token", raise_exception=False)
    received = frappe.get_request_header("X-Telegram-Bot-Api-Secret-Token") or ""
    if not bot_token or not hmac.compare_digest(received, webhook_secret(bot_token)):
        frappe.local.response["http_status_code"] = 403
        return {"status": "error", "message": "Forbidden"}

    chat_id = None
    update_id = None

    try:
        # Get incoming data
        data = frappe.request.get_json()
        update_id = data.get("update_id")
        message = data.get('message', {})
        chat_id = message.get('chat', {}).get('id')
        chat_type = message.get('chat', {}).get('type')
        
        if not chat_id:
            return {"status": "error", "message": "No chat_id"}
        
        # Route to appropriate handler
        if chat_type in ['group', 'supergroup', 'channel']:
            return handle_group_message(message, chat_id)
        else:
            return handle_private_message(message, chat_id)
        
    except Exception:
        log_exception(
            "Telegram Webhook Error",
            chat_id=chat_id,
            update_id=update_id,
        )
        
        if chat_id:
            send_telegram_message(
                chat_id, 
                "⚠️ System error. Please try again or contact support."
            )
        
        return {"status": "error", "message": "Unable to process webhook"}


@frappe.whitelist()
def get_webhook_info():
    """Get current webhook information for debugging (needs write access to Telegram Setting)"""
    frappe.has_permission("Telegram Setting", "write", throw=True)
    try:
        from docvision.telegram_bot.services.telegram_service import get_webhook_info as get_info

        return get_info()
            
    except Exception:
        log_exception("Get Webhook Info Error")
        return {
            "success": False,
            "message": "Unable to retrieve webhook information"
        }
