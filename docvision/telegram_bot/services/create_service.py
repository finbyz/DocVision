
import frappe
from frappe import _

def create_contact_with_party(data, party_type, party_name):
  
    # Get primary identifiers
    primary_email = data.email_ids[0].email_id if data.email_ids and len(data.email_ids) > 0 else None
    primary_phone = data.phone_nos[0].phone if data.phone_nos and len(data.phone_nos) > 0 else None
    
    existing_contact = None
    
    # Check if contact already exists by email
    if primary_email:
        normalized_email = primary_email.lower().strip()
        
        result = frappe.db.sql("""
            SELECT parent
            FROM `tabContact Email`
            WHERE LOWER(email_id) = %s
            LIMIT 1
        """, (normalized_email,), as_dict=True)
        
        if result:
            existing_contact = frappe.get_doc("Contact", result[0].parent)
    
    # Check by phone if email not found
    if not existing_contact and primary_phone:
        normalized_phone = primary_phone.strip()
        
        result = frappe.db.sql("""
            SELECT parent
            FROM `tabContact Phone`
            WHERE phone = %s
            LIMIT 1
        """, (normalized_phone,), as_dict=True)
        
        if result:
            existing_contact = frappe.get_doc("Contact", result[0].parent)
    
    # If contact exists, just link it to the party
    if existing_contact:
        already_linked = any(
            link.link_doctype == party_type and link.link_name == party_name
            for link in existing_contact.links
        )
        
        if not already_linked:
            existing_contact.append('links', {
                'link_doctype': party_type,
                'link_name': party_name
            })
            existing_contact.save(ignore_permissions=True)
            frappe.db.commit()
        
        return existing_contact
    
    # No existing contact - create new one
    try:
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
        
        # Add email (normalized)
        if primary_email:
            contact.append('email_ids', {
                'email_id': primary_email.lower().strip(),
                'is_primary': 1
            })
        
        # Add phone
        if primary_phone:
            contact.append('phone_nos', {
                'phone': primary_phone.strip(),
                'is_primary_phone': 1,
                'is_primary_mobile_no': 1
            })
        
        # Add address if available
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
        
    except frappe.exceptions.DuplicateEntryError:
        # Race condition - fetch the just-created contact
        if primary_email:
            result = frappe.db.sql("""
                SELECT parent
                FROM `tabContact Email`
                WHERE LOWER(email_id) = %s
                LIMIT 1
            """, (primary_email.lower().strip(),), as_dict=True)
            
            if result:
                contact = frappe.get_doc("Contact", result[0].parent)
                
                # Link to party if not already linked
                already_linked = any(
                    link.link_doctype == party_type and link.link_name == party_name
                    for link in contact.links
                )
                
                if not already_linked:
                    contact.append('links', {
                        'link_doctype': party_type,
                        'link_name': party_name
                    })
                    contact.save(ignore_permissions=True)
                    frappe.db.commit()
                
                return contact
        
        # Re-raise if we couldn't recover
        raise


def create_lead_from_data(data):
    """Create new Lead from extracted data or return existing"""
    
    primary_email = data.email_ids[0].email_id if data.email_ids and len(data.email_ids) > 0 else None
    primary_phone = data.phone_nos[0].phone if data.phone_nos and len(data.phone_nos) > 0 else None
    
    # Check if lead already exists by email
    if primary_email:
        normalized_email = primary_email.lower().strip()
        
        result = frappe.db.sql("""
            SELECT name
            FROM `tabLead`
            WHERE LOWER(email_id) = %s
            AND status != 'Converted'
            LIMIT 1
        """, (normalized_email,), as_dict=True)
        
        if result:
            return frappe.get_doc("Lead", result[0].name)
    
    # Check by phone
    if primary_phone:
        normalized_phone = primary_phone.strip()
        
        result = frappe.db.sql("""
            SELECT name
            FROM `tabLead`
            WHERE phone = %s
            AND status != 'Converted'
            LIMIT 1
        """, (normalized_phone,), as_dict=True)
        
        if result:
            return frappe.get_doc("Lead", result[0].name)
    
    # No existing lead - create new one
    source_name = get_or_create_lead_source("Telegram Bot")
    
    lead_data = {
        "doctype": "Lead",
        "first_name": getattr(data, 'first_name', '') or '',
        "last_name": getattr(data, 'last_name', '') or '',
        "salutation": getattr(data, 'salutation', None),
        "gender": getattr(data, 'gender', None),
        "designation": getattr(data, 'designation', None),
        "company_name": getattr(data, 'company_name', None),
        "email_id": primary_email.lower().strip() if primary_email else None,
        "phone": primary_phone.strip() if primary_phone else None,
        "website": getattr(data, 'website', None) or getattr(data, 'company_domain', None)
    }
    
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
        if frappe.db.exists("Lead Source", source_name):
            return source_name
        
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