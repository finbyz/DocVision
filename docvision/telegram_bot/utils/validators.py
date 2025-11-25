"""
Validators for data validation
"""
import frappe
from frappe import _


def is_valid_extraction(data):
    """Check if extraction has minimum required data"""
    if not data:
        return False
    
    has_name = getattr(data, 'first_name', None) or getattr(data, 'last_name', None)
    has_company = getattr(data, 'company_name', None) or getattr(data, 'core_company_name', None)
    has_contact = (hasattr(data, 'email_ids') and data.email_ids and len(data.email_ids) > 0) or \
                  (hasattr(data, 'phone_nos') and data.phone_nos and len(data.phone_nos) > 0)
    
    return has_name or has_company or has_contact
