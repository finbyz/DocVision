"""
Main webhook handler for Telegram bot
Entry point for all incoming Telegram messages
"""
import frappe
import json
from frappe import _
from docvision.telegram_bot.handlers.message_handler import handle_private_message, handle_group_message
from docvision.telegram_bot.services.telegram_service import send_telegram_message


@frappe.whitelist(allow_guest=True)
def telegram_webhook():
    """Main webhook endpoint for Telegram"""
    try:
        # Get incoming data
        data = frappe.request.get_json()
        frappe.log_error("Telegram Webhook Data", json.dumps(data))
        
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
        
    except Exception as e:
        frappe.log_error(str(e), "Telegram Webhook Error")
        
        if 'chat_id' in locals() and chat_id:
            send_telegram_message(
                chat_id, 
                f"⚠️ System Error\n\n{str(e)}\n\nPlease contact support."
            )
        
        return {"status": "error", "message": str(e)}


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
        
    except Exception as e:
        frappe.log_error(str(e), "Manual Webhook Setup Error")
        return {
            "success": False,
            "message": str(e)
        }


@frappe.whitelist()
def get_webhook_info():
    """Get current webhook information for debugging"""
    try:
        from docvision.telegram_bot.services.telegram_service import get_webhook_info as get_info
        return get_info()
            
    except Exception as e:
        frappe.log_error(str(e), "Get Webhook Info Error")
        return {
            "success": False,
            "message": str(e)
        }
