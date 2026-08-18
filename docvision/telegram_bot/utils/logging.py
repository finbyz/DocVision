"""Safe, contextual logging helpers for the Telegram integration."""

import json

import frappe


MAX_CONTEXT_LENGTH = 500
SENSITIVE_KEYS = {
    "access_key",
    "api_key",
    "authorization",
    "bot_token",
    "cookie",
    "credential",
    "image_url",
    "password",
    "secret",
    "telegram_bot_token",
    "token",
}


def _sanitize(value, key=None):
    if key and any(sensitive_key in key.lower() for sensitive_key in SENSITIVE_KEYS):
        return "[redacted]"

    if isinstance(value, dict):
        return {str(item_key): _sanitize(item_value, str(item_key)) for item_key, item_value in value.items()}

    if isinstance(value, (list, tuple)):
        return [_sanitize(item) for item in value]

    if value is None or isinstance(value, (bool, int, float)):
        return value

    return str(value)[:MAX_CONTEXT_LENGTH]


def _format_message(message, context):
    safe_context = _sanitize(context)
    if not safe_context:
        return message

    return f"{message}\n\nContext:\n{json.dumps(safe_context, indent=2, sort_keys=True)}"


def log_exception(title, **context):
    """Log the active exception traceback with sanitized operational context."""
    frappe.log_error(
        title=title,
        message=_format_message(frappe.get_traceback(), context),
    )


def log_error(title, message, **context):
    """Log a handled error with sanitized operational context."""
    frappe.log_error(
        title=title,
        message=_format_message(str(message), context),
    )
