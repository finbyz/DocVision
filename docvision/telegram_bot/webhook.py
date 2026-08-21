"""
Main webhook handler for Telegram bot
Entry point for all incoming Telegram messages, callback queries, and revision replies
"""
import hmac

import frappe
from docvision.telegram_bot.handlers.message_handler import handle_private_message, handle_group_message
from docvision.telegram_bot.services.telegram_service import send_telegram_message, answer_callback_query
from docvision.telegram_bot.services.outreach_service import (
    approve_and_send,
    prompt_revision,
    process_revision_reply,
    extract_outreach_name_from_reply,
)
from docvision.telegram_bot.utils.access_control import check_bot_access
from docvision.telegram_bot.utils.logging import log_exception

SECRET_HEADER = "X-Telegram-Bot-Api-Secret-Token"


@frappe.whitelist(allow_guest=True, methods=["POST"])
def telegram_webhook():
    """Main webhook endpoint for Telegram"""
    chat_id = None
    update_id = None

    _validate_webhook_secret()

    try:
        data = frappe.request.get_json()
        if not data:
            return {"status": "ok"}
            
        update_id = data.get("update_id")

        # 1. Handle Inline Button Callback Queries
        callback_query = data.get("callback_query")
        if callback_query:
            return _handle_callback_query(callback_query)

        # 2. Handle Messages
        message = data.get("message") or data.get("channel_post") or {}
        chat_id = message.get("chat", {}).get("id")
        chat_type = message.get("chat", {}).get("type")
        
        if not chat_id:
            return {"status": "error", "message": "No chat_id"}

        from_user = message.get("from") or {}
        if not _is_authorized(from_user):
            send_telegram_message(
                chat_id,
                "⛔ Access is not enabled for your Telegram account. Contact an administrator.",
            )
            return {"status": "ok"}

        # Check if this is a reply to a revision prompt
        if message.get("reply_to_message"):
            replied_text = message.get("reply_to_message", {}).get("text", "")
            outreach_name = extract_outreach_name_from_reply(replied_text)
            if outreach_name:
                revision_text = message.get("text", "").strip()
                if revision_text:
                    process_revision_reply(
                        outreach_name=outreach_name,
                        chat_id=chat_id,
                        revision_text=revision_text,
                        from_user=from_user,
                    )
                    return {"status": "ok"}

        # Route to standard message handlers
        if chat_type in ["group", "supergroup", "channel"]:
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


def _handle_callback_query(callback_query: dict):
    """Processes inline keyboard taps (Approve & Send, Revise)"""
    callback_id = callback_query.get("id")
    callback_data = callback_query.get("data", "")
    message = callback_query.get("message", {})
    chat_id = message.get("chat", {}).get("id")
    message_id = message.get("message_id")
    from_user = callback_query.get("from", {})

    try:
        if not _is_authorized(from_user):
            answer_callback_query(callback_id, text="Access denied.", show_alert=True)
            return {"status": "ok"}

        # Action 1: Approve & Send
        if callback_data.startswith("dov:app:"):
            outreach_name = callback_data.replace("dov:app:", "")
            alert_text, is_error = approve_and_send(outreach_name, chat_id, message_id, from_user)
            answer_callback_query(callback_id, text=alert_text, show_alert=is_error)
            return {"status": "ok"}

        # Action 2: Request Revision
        elif callback_data.startswith("dov:rev:"):
            outreach_name = callback_data.replace("dov:rev:", "")
            alert_text, is_error = prompt_revision(outreach_name, chat_id, message_id)
            answer_callback_query(callback_id, text=alert_text, show_alert=is_error)
            return {"status": "ok"}

        # Unknown callback
        answer_callback_query(callback_id, text="Action not recognized.", show_alert=False)
        return {"status": "ok"}

    except Exception:
        log_exception("Telegram Callback Error", callback_data=callback_data)
        answer_callback_query(callback_id, text="Error processing action.", show_alert=True)
        return {"status": "error"}


@frappe.whitelist(methods=["POST"])
def setup_webhook_manual():
    """Manual webhook setup via button click"""
    try:
        frappe.has_permission("Telegram Setting", "write", throw=True)
        telegram_setting = frappe.get_single("Telegram Setting")
        telegram_setting.setup_telegram_webhook()
        
        return {
            "success": True,
            "message": "Webhook setup triggered successfully"
        }
        
    except frappe.PermissionError:
        raise
    except Exception:
        log_exception("Manual Webhook Setup Error")
        return {
            "success": False,
            "message": "Unable to configure the webhook"
        }


@frappe.whitelist(methods=["GET"])
def get_webhook_info():
    """Get current webhook information for debugging"""
    try:
        frappe.has_permission("Telegram Setting", "read", throw=True)
        from docvision.telegram_bot.services.telegram_service import get_webhook_info as get_info

        return get_info()
            
    except frappe.PermissionError:
        raise
    except Exception:
        log_exception("Get Webhook Info Error")
        return {
            "success": False,
            "message": "Unable to retrieve webhook information"
        }


def _validate_webhook_secret() -> None:
    setting = frappe.get_single("Telegram Setting")
    expected = setting.get_password("telegram_webhook_secret", raise_exception=False) or ""
    provided = frappe.get_request_header(SECRET_HEADER) or ""
    if not expected or not hmac.compare_digest(expected, provided):
        raise frappe.PermissionError("Invalid Telegram webhook token")


def _is_authorized(from_user: dict) -> bool:
    telegram_id = from_user.get("id")
    return check_bot_access(telegram_id, _get_user_display_name(from_user))


def _get_user_display_name(from_user: dict) -> str:
    first_name = from_user.get("first_name") or ""
    last_name = from_user.get("last_name") or ""
    full_name = f"{first_name} {last_name}".strip()
    if full_name:
        return full_name
    return from_user.get("username") or str(from_user.get("id") or "")
