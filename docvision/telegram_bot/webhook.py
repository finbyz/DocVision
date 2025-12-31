"""
Main webhook handler for Telegram bot
Entry point for all incoming Telegram messages
"""
import frappe
import json
from frappe import _


@frappe.whitelist(allow_guest=True)
def telegram_webhook():
    """Main webhook endpoint for Telegram - responds immediately and processes in background"""
    try:
        # Get incoming data
        data = frappe.request.get_json()
        frappe.log_error("Telegram Webhook Data", json.dumps(data))
        
        message = data.get('message', {})
        chat_id = message.get('chat', {}).get('id')
        chat_type = message.get('chat', {}).get('type')
        
        if not chat_id:
            return {"status": "error", "message": "No chat_id"}
        
        # Enqueue processing in background
        frappe.enqueue(
            "docvision.telegram_bot.webhook.process_telegram_message",
            queue="short",
            message=message,
            chat_id=chat_id,
            chat_type=chat_type,
            enqueue_after_commit=True
        )
        
        # Respond immediately to Telegram
        return {"status": "ok", "message": "Processing in background"}
        
    except Exception as e:
        frappe.log_error(str(e), "Telegram Webhook Error")
        return {"status": "error", "message": str(e)}


def process_telegram_message(message, chat_id, chat_type):
    """Background job to process Telegram message"""
    from docvision.telegram_bot.handlers.message_handler import handle_private_message, handle_group_message
    from docvision.telegram_bot.services.telegram_service import send_telegram_message
    
    try:
        # Route to appropriate handler
        if chat_type in ['group', 'supergroup', 'channel']:
            handle_group_message(message, chat_id)
        else:
            handle_private_message(message, chat_id)
            
    except Exception as e:
        # Safe error logging - truncate to prevent cascade failures
        error_msg = str(e)[:500] if len(str(e)) > 500 else str(e)
        try:
            frappe.log_error(
                title="Telegram Processing Error",
                message=f"Chat ID: {chat_id}\nError: {error_msg}"
            )
        except:
            pass  # Silently fail if logging fails
        
        try:
            send_telegram_message(
                chat_id, 
                f"⚠️ System Error\n\nPlease try again later or contact support."
            )
        except:
            pass  # Don't fail if error notification fails


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
