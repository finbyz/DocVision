"""
Create service for creating new contacts and leads
"""
import frappe
from frappe import _


def create_contact_with_party(data, party_type, party_name):
    """Create contact and link to existing party (Customer/Lead)"""
    
    # Direct Pydantic access
    primary_email = data.email_ids[0].email_id if data.email_ids and len(data.email_ids) > 0 else None
    primary_phone = data.phone_nos[0].phone if data.phone_nos and len(data.phone_nos) > 0 else None
    
    contact = frappe.get_doc({
        "doctype": "Contact",
        "first_name": getattr(data, 'first_name', '') or '',
        "last_name": getattr(data, 'last_name', '') or '',
        "salutation": getattr(data, 'salutation', None),  
        "gender": getattr(data, 'gender', None),          
        "designation": getattr(data, 'designation', None),
        "company_name": getattr(data, 'company_name', None),
        "status": "Passive"
    })
    
    if primary_email:
        contact.append('email_ids', {
            'email_id': primary_email,
            'is_primary': 1
        })
    
    if primary_phone:
        contact.append('phone_nos', {
            'phone': primary_phone,
            'is_primary_phone': 1,
            'is_primary_mobile_no': 1
        })
    
    if hasattr(data, 'address') and data.address:
        contact.append('address', {
            'address_type': 'Office',
            'address_line1': getattr(data.address, 'address_line1', None),
            'address_line2': getattr(data.address, 'address_line2', None),
            'city': getattr(data.address, 'city', None),
            'state': getattr(data.address, 'state', None),
            'pincode': getattr(data.address, 'pincode', None),
            'country': getattr(data.address, 'country', None) or 'India',
            'is_primary_address': 1
        })
    
    # Link to party
    contact.append('links', {
        'link_doctype': party_type,
        'link_name': party_name
    })
    
    contact.insert(ignore_permissions=True)
    frappe.db.commit()
    
    return contact


def create_lead_from_data(data):
    """Create new Lead from extracted data"""
    
    primary_email = data.email_ids[0].email_id if data.email_ids and len(data.email_ids) > 0 else None
    primary_phone = data.phone_nos[0].phone if data.phone_nos and len(data.phone_nos) > 0 else None
    
    source_name = get_or_create_lead_source("Telegram Bot")
    
    lead_data = {
        "doctype": "Lead",
        "first_name": getattr(data, 'first_name', '') or '',
        "last_name": getattr(data, 'last_name', '') or '',
        "salutation": getattr(data, 'salutation', None),  
        "gender": getattr(data, 'gender', None),         
        "designation": getattr(data, 'designation', None),
        "company_name": getattr(data, 'company_name', None),
        "email_id": primary_email,
        "phone": primary_phone,
        "website": getattr(data, 'website', None) or getattr(data, 'company_domain', None)
    }
    
    # Only add source if it was successfully created/found
    if source_name:
        lead_data["source"] = source_name
    
    lead = frappe.get_doc(lead_data)
    
    # Add address if available
    if hasattr(data, 'address') and data.address:
        lead.address_line1 = getattr(data.address, 'address_line1', None)
        lead.address_line2 = getattr(data.address, 'address_line2', None)
        lead.city = getattr(data.address, 'city', None)
        lead.state = getattr(data.address, 'state', None)
        lead.pincode = getattr(data.address, 'pincode', None)
        lead.country = getattr(data.address, 'country', None) or 'India'
    
    lead.insert(ignore_permissions=True)
    frappe.db.commit()
    
    return lead


def get_or_create_lead_source(source_name):
    """Get existing Lead Source or create if doesn't exist"""
    try:
        # Check if source exists
        if frappe.db.exists("Lead Source", source_name):
            return source_name
        
        # Create new Lead Source
        lead_source = frappe.get_doc({
            "doctype": "Lead Source",
            "source_name": source_name
        })
        lead_source.insert(ignore_permissions=True)
        frappe.db.commit()
        
        return source_name
        
    except Exception as e:
        frappe.log_error(str(e), "Lead Source Creation Error")
        return None
