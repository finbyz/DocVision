"""
Search service for finding existing contacts, customers, and leads
"""
import frappe
from frappe import _


def get_contact_with_domain_or_email(data):
    """Find contact by email or company domain"""
    try:
        # Safe attribute access for Pydantic
        primary_email = data.email_ids[0].email_id if data.email_ids and len(data.email_ids) > 0 else None
        company_domain = getattr(data, 'company_domain', None) or getattr(data, 'website', None)
        
        # STEP 1: Check by email
        if primary_email:
            contact = frappe.get_all(
                "Contact Email",
                filters={"email_id": primary_email},
                fields=["parent"],
                limit=1
            )
            
            if contact:
                contact_doc = frappe.get_doc("Contact", contact[0].parent)
                
                # Get linked party
                customer_link = None
                lead_link = None
                
                for link in contact_doc.links:
                    if link.link_doctype == "Customer":
                        customer_link = link
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
        
        # STEP 2: Check by company domain (if email not found)
        if company_domain:
            # Clean domain
            domain = company_domain.lower()
            domain = domain.replace('http://', '').replace('https://', '')
            domain = domain.replace('www.', '').strip('/')
            domain = domain.split('/')[0]
            
            # Better matching - check both company name and email domain
            contacts = frappe.db.sql("""
                SELECT DISTINCT c.name
                FROM `tabContact` c
                LEFT JOIN `tabContact Email` ce ON ce.parent = c.name
                WHERE (LOWER(c.company_name) LIKE %s 
                       OR LOWER(ce.email_id) LIKE %s)
                LIMIT 1
            """, (f"%{domain}%", f"%@{domain}%"), as_dict=True)
            
            if contacts:
                contact_doc = frappe.get_doc("Contact", contacts[0].name)
                
                customer_link = None
                lead_link = None
                
                for link in contact_doc.links:
                    if link.link_doctype == "Customer":
                        customer_link = link
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
            "with_domain": False,
            "contact": None
        }
        
    except Exception as e:
        frappe.log_error(str(e), "Get Contact Error")
        return {
            "status": "error",
            "with_domain": False,
            "contact": None
        }


def find_customer_by_company_name(company_name):
    """Find customer by company name"""
    if not company_name:
        return None
    
    try:
        customer = frappe.db.get_value(
            "Customer",
            {"customer_name": ["like", f"%{company_name}%"]},
            ["name", "customer_name"],
            as_dict=True
        )
        return customer
    except:
        return None


def find_lead_by_company_name(company_name):
    """Find unconverted lead by company name"""
    if not company_name:
        return None
    
    try:
        leads = frappe.db.sql("""
            SELECT name, company_name, lead_name
            FROM `tabLead`
            WHERE company_name LIKE %s
            AND status != 'Converted'
            LIMIT 1
        """, (f"%{company_name}%",), as_dict=True)
        
        return leads[0] if leads else None
    except:
        return None
