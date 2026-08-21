
import frappe

from docvision.telegram_bot.utils.logging import log_exception


def create_address_for_party(data, party_type, party_name, address_title):
    """Create an Address linked to the same party as the Contact."""
    address_data = getattr(data, "address", None)
    if not address_data:
        return None

    country = getattr(address_data, "country", None) or "India"
    state = getattr(address_data, "state", None)

    ignore_validate = (
        country.strip().casefold() == "india" and not (state or "").strip()
    )

    address = frappe.get_doc({
        "doctype": "Address",
        "address_title": address_title or party_name,
        "address_type": "Office",
        "address_line1": getattr(address_data, "address_line1", None),
        "address_line2": getattr(address_data, "address_line2", None),
        "city": getattr(address_data, "city", None),
        "state": state,
        "pincode": getattr(address_data, "pincode", None),
        "country": country,
        "is_primary_address": 1,
        "links": [{
            "link_doctype": party_type,
            "link_name": party_name,
        }],
    })
    if ignore_validate:
        # India Compliance requires a state for Indian addresses. Contact data
        # extracted from a document may not contain one, but the partial address
        # should still be stored.
        address.flags.ignore_validate = True
    address.insert(ignore_permissions=True)

    return address

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
        
        # Link to party
        contact.append('links', {
            'link_doctype': party_type,
            'link_name': party_name
        })
        
        contact.insert(ignore_permissions=True)
        create_address_for_party(
            data,
            party_type,
            party_name,
            getattr(data, "company_name", None) or contact.full_name,
        )
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
    
    # Check by phone / whatsapp number
    if primary_phone:
        normalized_phone = primary_phone.strip()
        lead_meta = frappe.get_meta("Lead")
        phone_fields = [f for f in ["whatsapp_number", "whatsapp_no", "phone", "mobile_no"] if lead_meta.has_field(f)]
        if not phone_fields:
            phone_fields = ["phone"]
        
        conditions = " OR ".join([f"`{f}` = %s" for f in phone_fields])
        result = frappe.db.sql(f"""
            SELECT name
            FROM `tabLead`
            WHERE ({conditions})
            AND status != 'Converted'
            LIMIT 1
        """, tuple(normalized_phone for _ in phone_fields), as_dict=True)
        
        if result:
            return frappe.get_doc("Lead", result[0].name)
    
    # No existing lead - create new one
    source_field, source_name = get_or_create_lead_source("Telegram Bot")
    
    lead_data = {
        "doctype": "Lead",
        "first_name": getattr(data, 'first_name', '') or '',
        "last_name": getattr(data, 'last_name', '') or '',
        "salutation": getattr(data, 'salutation', None),
        "gender": getattr(data, 'gender', None),
        "designation": getattr(data, 'designation', None),
        "company_name": getattr(data, 'company_name', None),
        "email_id": primary_email.lower().strip() if primary_email else None,
        "website": getattr(data, 'website', None) or getattr(data, 'company_domain', None)
    }

    if primary_phone:
        phone_val = primary_phone.strip()
        lead_meta = frappe.get_meta("Lead")
        if lead_meta.has_field("whatsapp_number"):
            lead_data["whatsapp_number"] = phone_val
        if lead_meta.has_field("whatsapp_no"):
            lead_data["whatsapp_no"] = phone_val
        if lead_meta.has_field("phone"):
            lead_data["phone"] = phone_val
        if lead_meta.has_field("mobile_no"):
            lead_data["mobile_no"] = phone_val
        # Default fallback to whatsapp_number
        if "whatsapp_number" not in lead_data and "whatsapp_no" not in lead_data and "phone" not in lead_data:
            lead_data["whatsapp_number"] = phone_val
    
    if source_name:
        lead_data[source_field] = source_name
    
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
    """Get or create the source used by the installed ERPNext version."""
    try:
        if frappe.get_meta("Lead").has_field("utm_source"):
            source_doctype = "UTM Source"
            source_field = "utm_source"
            source_values = {
                "doctype": source_doctype,
                "name": source_name,
                "slug": frappe.utils.slug(source_name),
            }
        else:
            source_doctype = "Lead Source"
            source_field = "source"
            source_values = {
                "doctype": source_doctype,
                "source_name": source_name,
            }

        if not frappe.db.exists(source_doctype, source_name):
            frappe.get_doc(source_values).insert(ignore_permissions=True)

        frappe.db.commit()

        return source_field, source_name

    except Exception:
        log_exception("Lead Source Creation Error", source_name=source_name)
        return "utm_source", None
