"""
Access control utilities
Manages bot access for users
"""
import frappe
from frappe import _


def check_bot_access(telegram_id, chat_id, user_name):
    """Check if user has bot access, create entry if new"""
    try:
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
                    "full_name": user_name,
                    "allow_access": 0
                }).insert(ignore_permissions=True)
                frappe.db.commit()
            except Exception as e:
                frappe.log_error(str(e), "Bot Access Creation Error")
        
        return False
        
    except Exception as e:
        frappe.log_error(str(e), "Access Check Error")
        return False
