import re
import frappe

from docvision.telegram_bot.utils.logging import log_exception
from docvision.telegram_bot.utils.validators import clean_phone_number


def get_contact_with_domain_or_email(data):
    """Find contact by email or company domain"""
    try:
        # Safe attribute access for Pydantic
        primary_email = data.email_ids[0].email_id if data.email_ids and len(data.email_ids) > 0 else None
        raw_phone = data.phone_nos[0].phone if data.phone_nos and len(data.phone_nos) > 0 else None
        primary_phone = clean_phone_number(raw_phone)
        company_domain = getattr(data, 'company_domain', None) or getattr(data, 'website', None)
        
        # Normalize email
        if primary_email:
            primary_email = primary_email.lower().strip()
        
        # STEP 1: Check by email (case-insensitive, exact match)
        if primary_email:
            contact = frappe.db.sql("""
                SELECT DISTINCT parent
                FROM `tabContact Email`
                WHERE LOWER(email_id) = %s
                LIMIT 1
            """, (primary_email,), as_dict=True)
            
            if contact:
                contact_doc = frappe.get_doc("Contact", contact[0].parent)
                
                # Get linked party
                customer_link = None
                lead_link = None
                
                for link in contact_doc.links:
                    if link.link_doctype == "Customer":
                        customer_link = link
                        break  # Prioritize Customer
                    elif link.link_doctype == "Lead":
                        lead_link = link
                
                if customer_link:
                    customer = frappe.get_doc("Customer", customer_link.link_name)
                    return {
                        "status": "success",
                        "with_domain": bool(company_domain),
                        "contact": contact_doc,
                        "party_type": "Customer",
                        "party_name": customer.name,
                        "party_display": customer.customer_name
                    }
                
                if lead_link:
                    lead = frappe.get_doc("Lead", lead_link.link_name)
                    return {
                        "status": "success",
                        "with_domain": bool(company_domain),
                        "contact": contact_doc,
                        "party_type": "Lead",
                        "party_name": lead.name,
                        "party_display": lead.lead_name or lead.company_name
                    }
                    
                return {
                    "status": "success",
                    "with_domain": bool(company_domain),
                    "contact": contact_doc,
                    "party_type": None,
                    "party_name": None,
                    "party_display": contact_doc.first_name or contact_doc.name
                }
        
        # STEP 2: Check by phone (if email not found)
        if primary_phone:
            last_10 = re.sub(r"\D", "", primary_phone)[-10:]
            if last_10:
                contact = frappe.db.sql("""
                    SELECT DISTINCT parent
                    FROM `tabContact Phone`
                    WHERE phone LIKE %s
                    LIMIT 1
                """, (f"%{last_10}",), as_dict=True)
                
                if contact:
                    contact_doc = frappe.get_doc("Contact", contact[0].parent)
                    
                    customer_link = None
                    lead_link = None
                    
                    for link in contact_doc.links:
                        if link.link_doctype == "Customer":
                            customer_link = link
                            break
                        elif link.link_doctype == "Lead":
                            lead_link = link
                    
                    if customer_link:
                        customer = frappe.get_doc("Customer", customer_link.link_name)
                        return {
                            "status": "success",
                            "with_domain": bool(company_domain),
                            "contact": contact_doc,
                            "party_type": "Customer",
                            "party_name": customer.name,
                            "party_display": customer.customer_name
                        }
                    
                    if lead_link:
                        lead = frappe.get_doc("Lead", lead_link.link_name)
                        return {
                            "status": "success",
                            "with_domain": bool(company_domain),
                            "contact": contact_doc,
                            "party_type": "Lead",
                            "party_name": lead.name,
                            "party_display": lead.lead_name or lead.company_name
                        }
                        
                    return {
                        "status": "success",
                        "with_domain": bool(company_domain),
                        "contact": contact_doc,
                        "party_type": None,
                        "party_name": None,
                        "party_display": contact_doc.first_name or contact_doc.name
                    }

        
        # STEP 3: Check by company domain (only if email AND phone not found)
        if company_domain and not primary_email:
            # Clean domain
            domain = company_domain.lower()
            domain = domain.replace('http://', '').replace('https://', '')
            domain = domain.replace('www.', '').strip('/')
            domain = domain.split('/')[0]
            domain = domain.split(':')[0]  # Remove port
            
            if domain:
                # FIXED: Only match exact domain in email addresses
                # Removed company_name LIKE which was too broad
                contacts = frappe.db.sql("""
                    SELECT DISTINCT c.name
                    FROM `tabContact` c
                    INNER JOIN `tabContact Email` ce ON ce.parent = c.name
                    WHERE LOWER(ce.email_id) LIKE %s
                    LIMIT 1
                """, (f"%@{domain}",), as_dict=True)
                
                if contacts:
                    contact_doc = frappe.get_doc("Contact", contacts[0].name)
                    
                    customer_link = None
                    lead_link = None
                    
                    for link in contact_doc.links:
                        if link.link_doctype == "Customer":
                            customer_link = link
                            break
                        elif link.link_doctype == "Lead":
                            lead_link = link
                    
                    if customer_link:
                        customer = frappe.get_doc("Customer", customer_link.link_name)
                        return {
                            "status": "success",
                            "with_domain": True,
                            "contact": contact_doc,
                            "party_type": "Customer",
                            "party_name": customer.name,
                            "party_display": customer.customer_name
                        }
                    
                    if lead_link:
                        lead = frappe.get_doc("Lead", lead_link.link_name)
                        return {
                            "status": "success",
                            "with_domain": True,
                            "contact": contact_doc,
                            "party_type": "Lead",
                            "party_name": lead.name,
                            "party_display": lead.lead_name or lead.company_name
                        }
                    
                    return {
                        "status": "success",
                        "with_domain": True,
                        "contact": contact_doc,
                        "party_type": None,
                        "party_name": None,
                        "party_display": contact_doc.first_name or contact_doc.name
                    }
        
        # No match found
        return {
            "status": "success",
            "with_domain": False,
            "contact": None,
            "party_type": None,
            "party_name": None,
            "party_display": None
        }
        
    except Exception:
        log_exception(
            "Get Contact Error",
            lookup_email=bool(primary_email) if "primary_email" in locals() else False,
            lookup_phone=bool(primary_phone) if "primary_phone" in locals() else False,
            lookup_domain=bool(company_domain) if "company_domain" in locals() else False,
        )
        
        return {
            "status": "error",
            "with_domain": False,
            "contact": None,
            "party_type": None,
            "party_name": None,
            "party_display": None
        }


def find_customer_by_company_name(company_name):
    """Find customer by company name"""
    if not company_name:
        return None
    
    try:
        # Try exact match first
        customer = frappe.db.get_value(
            "Customer",
            {"customer_name": company_name},
            ["name", "customer_name"],
            as_dict=True
        )
        
        if customer:
            return customer

        return None
    except Exception:
        log_exception("Find Customer Error", lookup_type="company_name")
        raise


def find_lead_by_company_name(company_name):
    """Find unconverted lead by company name"""
    if not company_name:
        return None
    
    try:
        # Try exact match first
        leads = frappe.db.sql("""
            SELECT name, company_name, lead_name
            FROM `tabLead`
            WHERE company_name = %s
            AND status != 'Converted'
            LIMIT 1
        """, (company_name,), as_dict=True)
        
        if leads:
            return leads[0]

        return None
    except Exception:
        log_exception("Find Lead Error", lookup_type="company_name")
        raise
