"""
Access control utilities
Manages bot access for users
"""
import frappe

from docvision.telegram_bot.utils.logging import log_exception


def check_bot_access(telegram_id: int | str | None, user_name: str) -> bool:
    """Check if user has bot access, create entry if new"""
    if telegram_id is None:
        return False

    try:
        if not frappe.db.exists("DocType", "Bot Access"):
            frappe.log_error("Bot Access DocType is not installed", "DocVision Access Check")
            return False

        bot_access = frappe.db.get_value(
            "Bot Access",
            {"telegram_id": str(telegram_id)},
            ["allow_access", "name"],
            as_dict=True
        )
        
        if bot_access and bot_access.allow_access:
            return True
        
        if not bot_access:
            try:
                frappe.get_doc({
                    "doctype": "Bot Access",
                    "telegram_id": str(telegram_id),
                    "full_name": user_name or str(telegram_id),
                    "allow_access": 0
                }).insert(ignore_permissions=True)
            except Exception:
                log_exception("Bot Access Creation Error", telegram_id=telegram_id)
        
        return False
        
    except Exception:
        log_exception("Access Check Error", telegram_id=telegram_id)
        return False
