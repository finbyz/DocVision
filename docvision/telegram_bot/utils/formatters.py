"""
Message formatters
Formats Telegram messages for different scenarios
"""
import frappe
from frappe import _


def format_existing_party_message(party_type, party_name, party_display, contact):
    """Format message when Customer/Lead already exists with contact"""
    site_url = frappe.utils.get_url()
    
    msg = f"<b>✅ {party_type} Already Exists</b>\n\n"
    msg += f"👤 Contact: {contact.first_name or ''} {contact.last_name or ''}\n"
    
    if contact.email_ids and len(contact.email_ids) > 0:
        msg += f"📧 Email: {contact.email_ids[0].email_id}\n"
    
    if contact.phone_nos and len(contact.phone_nos) > 0:
        msg += f"📞 Phone: {contact.phone_nos[0].phone}\n"
    
    if contact.company_name:
        msg += f"🏢 Company: {contact.company_name}\n"
    
    msg += f"\n🔗 Linked {party_type}: {party_display}\n"
    msg += f"\n<a href='{site_url}/app/{party_type.lower()}/{party_name}'>View {party_type}</a>"
    msg += f"\n<a href='{site_url}/app/contact/{contact.name}'>View Contact</a>"
    
    return msg


def format_existing_contact_message(contact, party_type=None, party=None):
    """Format message for existing contact"""
    site_url = frappe.utils.get_url()
    
    msg = "<b>✅ Contact Already Exists</b>\n\n"
    msg += f"👤 Name: {contact.first_name or ''} {contact.last_name or ''}\n"
    
    if contact.email_ids and len(contact.email_ids) > 0:
        msg += f"📧 Email: {contact.email_ids[0].email_id}\n"
    
    if contact.phone_nos and len(contact.phone_nos) > 0:
        msg += f"📞 Phone: {contact.phone_nos[0].phone}\n"
    
    if contact.company_name:
        msg += f"🏢 Company: {contact.company_name}\n"
    
    if party_type and party:
        msg += f"\n🔗 Linked to {party_type}: {party}\n"
    
    msg += f"\n<a href='{site_url}/app/contact/{contact.name}'>View Contact</a>"
    
    return msg


def format_contact_created_with_party_message(contact, party_type, party_name, party_display):
    """Format message when contact is created with existing party"""
    site_url = frappe.utils.get_url()
    
    msg = "<b>✅ Contact Created Successfully!</b>\n\n"
    msg += f"👤 Name: {contact.first_name or ''} {contact.last_name or ''}\n"
    
    if contact.email_ids and len(contact.email_ids) > 0:
        msg += f"📧 Email: {contact.email_ids[0].email_id}\n"
    
    if contact.phone_nos and len(contact.phone_nos) > 0:
        msg += f"📞 Phone: {contact.phone_nos[0].phone}\n"
    
    if contact.company_name:
        msg += f"🏢 Company: {contact.company_name}\n"
    
    msg += f"\n🔗 Linked to existing {party_type}: {party_display}\n"
    msg += f"\n<a href='{site_url}/app/contact/{contact.name}'>View Contact</a>"
    msg += f"\n<a href='{site_url}/app/{party_type.lower()}/{party_name}'>View {party_type}</a>"
    
    return msg


def format_new_lead_and_contact_message(lead, contact):
    """Format message when both lead and contact are created"""
    site_url = frappe.utils.get_url()
    
    msg = "<b>✅ New Lead Created!</b>\n\n"
    msg += f"👤 Name: {lead.lead_name}\n"
    
    if lead.email_id:
        msg += f"📧 Email: {lead.email_id}\n"
    
    if lead.phone:
        msg += f"📞 Phone: {lead.phone}\n"
    
    if lead.company_name:
        msg += f"🏢 Company: {lead.company_name}\n"
    
    msg += "\n✅ Contact also created and linked\n"
    msg += f"\n<a href='{site_url}/app/lead/{lead.name}'>View Lead</a>"
    msg += f"\n<a href='{site_url}/app/contact/{contact.name}'>View Contact</a>"
    
    return msg
