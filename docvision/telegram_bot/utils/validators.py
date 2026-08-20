import re
import frappe
from frappe import _


def clean_phone_number(phone):
    """
    Normalizes a phone number to only contain digits, spaces, and '+',
    preventing validation errors in productivity_next or other hooks.
    Example: '+91-9810123456' -> '+91 9810123456'
             '(011) 2755-4433' -> '011 2755 4433'
    """
    if not phone:
        return None
    phone_str = str(phone).strip()
    if not phone_str:
        return None
    # Replace common separator characters with space
    cleaned = re.sub(r"[-./\(\)\[\],_]", " ", phone_str)
    # Strip any characters except digits, '+', and whitespace
    cleaned = re.sub(r"[^\d+ ]", "", cleaned)
    # Collapse multiple spaces
    cleaned = re.sub(r"\s+", " ", cleaned).strip()
    return cleaned if cleaned else None


def is_valid_extraction(data):
    """Check if extraction has minimum required data"""
    if not data:
        return False
    
    has_name = getattr(data, 'first_name', None) or getattr(data, 'last_name', None)
    has_company = getattr(data, 'company_name', None) or getattr(data, 'core_company_name', None)
    has_contact = (hasattr(data, 'email_ids') and data.email_ids and len(data.email_ids) > 0) or \
                  (hasattr(data, 'phone_nos') and data.phone_nos and len(data.phone_nos) > 0)
    
    return has_name or has_company or has_contact

