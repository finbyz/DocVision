"""
Telegram API service
Handles all communication with Telegram API
"""
import json
import frappe
import requests

from docvision.telegram_bot.utils.logging import log_error, log_exception


def _get_bot_token():
    telegram_setting = frappe.get_single("Telegram Setting")
    bot_token = telegram_setting.get_password("telegram_bot_token")
    if bot_token:
        return bot_token.strip()
    return None


def get_telegram_image_url(file_id):
    """Get direct URL for a Telegram image file"""
    try:
        bot_token = _get_bot_token()
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
        log_exception("Get Telegram Image Timeout", file_id=file_id)
        return None
    except Exception:
        log_exception("Get Telegram Image Error", file_id=file_id)
        return None


def send_telegram_message(chat_id, text, reply_markup=None, reply_to_message_id=None, parse_mode="HTML"):
    """Send message to Telegram chat, optionally with reply_markup / inline keyboard"""
    try:
        bot_token = _get_bot_token()
        if not bot_token:
            log_error(
                "Telegram Send Error",
                "Bot token not found in Telegram Setting",
                chat_id=chat_id,
            )
            return None
        
        url = f"https://api.telegram.org/bot{bot_token}/sendMessage"
        payload = {
            "chat_id": chat_id,
            "text": text,
            "disable_web_page_preview": True
        }
        if parse_mode:
            payload["parse_mode"] = parse_mode
        if reply_markup is not None:
            payload["reply_markup"] = reply_markup
        if reply_to_message_id:
            payload["reply_to_message_id"] = reply_to_message_id

        response = requests.post(url, json=payload, timeout=15)
        res_json = response.json()
        
        if response.status_code != 200 or not res_json.get("ok"):
            log_error(
                "Telegram Send Error",
                "Telegram API rejected sendMessage request",
                chat_id=chat_id,
                http_status=response.status_code,
                telegram_response=response.text,
            )
            return None
        
        return res_json.get("result")
        
    except Exception:
        log_exception(
            "Telegram Send Error",
            chat_id=chat_id,
            has_message=bool(text),
        )
        return None


def send_message_with_inline_buttons(chat_id, text, inline_keyboard, reply_to_message_id=None, parse_mode="HTML"):
    """
    Send message with an inline keyboard.
    inline_keyboard format: [[{"text": "Button 1", "callback_data": "data1"}, ...]]
    """
    reply_markup = {"inline_keyboard": inline_keyboard}
    return send_telegram_message(
        chat_id=chat_id,
        text=text,
        reply_markup=reply_markup,
        reply_to_message_id=reply_to_message_id,
        parse_mode=parse_mode
    )


def send_force_reply(chat_id, text, placeholder="Type your revision here...", reply_to_message_id=None, parse_mode="HTML"):
    """Send message requesting a force reply from the user"""
    reply_markup = {
        "force_reply": True,
        "selective": True,
        "input_field_placeholder": placeholder
    }
    return send_telegram_message(
        chat_id=chat_id,
        text=text,
        reply_markup=reply_markup,
        reply_to_message_id=reply_to_message_id,
        parse_mode=parse_mode
    )


def edit_message_text(chat_id, message_id, text, reply_markup=None, parse_mode="HTML"):
    """Edit an existing Telegram message's text and reply markup"""
    try:
        bot_token = _get_bot_token()
        if not bot_token:
            return None
        
        url = f"https://api.telegram.org/bot{bot_token}/editMessageText"
        payload = {
            "chat_id": chat_id,
            "message_id": message_id,
            "text": text,
            "disable_web_page_preview": True
        }
        if parse_mode:
            payload["parse_mode"] = parse_mode
        if reply_markup is not None:
            payload["reply_markup"] = reply_markup

        response = requests.post(url, json=payload, timeout=15)
        res_json = response.json()
        
        if response.status_code != 200 or not res_json.get("ok"):
            log_error(
                "Telegram Edit Message Error",
                "Telegram API rejected editMessageText request",
                chat_id=chat_id,
                message_id=message_id,
                http_status=response.status_code,
                telegram_response=response.text,
            )
            return None
            
        return res_json.get("result")
        
    except Exception:
        log_exception(
            "Telegram Edit Message Error",
            chat_id=chat_id,
            message_id=message_id,
        )
        return None


def answer_callback_query(callback_query_id, text="", show_alert=False):
    """Acknowledge a callback query from an inline button tap"""
    try:
        bot_token = _get_bot_token()
        if not bot_token or not callback_query_id:
            return None
        
        url = f"https://api.telegram.org/bot{bot_token}/answerCallbackQuery"
        payload = {
            "callback_query_id": callback_query_id,
            "show_alert": show_alert
        }
        if text:
            payload["text"] = text

        response = requests.post(url, json=payload, timeout=10)
        return response.json()
        
    except Exception:
        log_exception(
            "Telegram Answer Callback Error",
            callback_query_id=callback_query_id,
        )
        return None


def get_webhook_info():
    """Get current webhook information"""
    try:
        bot_token = _get_bot_token()
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
            
    except Exception:
        log_exception("Get Webhook Info Error")
        return {
            "success": False,
            "message": "Unable to retrieve webhook information"
        }
