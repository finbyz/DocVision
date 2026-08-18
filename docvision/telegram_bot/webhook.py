"""
Main webhook handler for Telegram bot
Entry point for all incoming Telegram messages
"""
import frappe
from docvision.telegram_bot.handlers.message_handler import handle_private_message, handle_group_message
from docvision.telegram_bot.services.telegram_service import send_telegram_message
from docvision.telegram_bot.utils.logging import log_exception


@frappe.whitelist(allow_guest=True)
def telegram_webhook():
    """Main webhook endpoint for Telegram"""
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
def setup_webhook_manual():
    """Manual webhook setup via button click"""
    try:
        telegram_setting = frappe.get_single("Telegram Setting")
        telegram_setting.setup_telegram_webhook()
        
        return {
            "success": True,
            "message": "Webhook setup triggered successfully"
        }
        
    except Exception:
        log_exception("Manual Webhook Setup Error")
        return {
            "success": False,
            "message": "Unable to configure the webhook"
        }


@frappe.whitelist()
def get_webhook_info():
    """Get current webhook information for debugging"""
    try:
        from docvision.telegram_bot.services.telegram_service import get_webhook_info as get_info

        return get_info()
            
    except Exception:
        log_exception("Get Webhook Info Error")
        return {
            "success": False,
            "message": "Unable to retrieve webhook information"
        }
