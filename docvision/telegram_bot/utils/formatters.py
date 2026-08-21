"""
Message formatters
Formats Telegram messages for different scenarios
"""
from docvision.telegram_bot.utils.telegram_html import (
    escape_telegram,
    telegram_form_link,
)


def format_existing_party_message(party_type, party_name, party_display, contact):
    """Format message when Customer/Lead already exists with contact"""
    
    msg = f"<b>✅ {escape_telegram(party_type)} Already Exists</b>\n\n"
    msg += f"👤 Contact: {escape_telegram(contact.first_name)} {escape_telegram(contact.last_name)}\n"
    
    if contact.email_ids and len(contact.email_ids) > 0:
        msg += f"📧 Email: {escape_telegram(contact.email_ids[0].email_id)}\n"
    
    if contact.phone_nos and len(contact.phone_nos) > 0:
        msg += f"📞 Phone: {escape_telegram(contact.phone_nos[0].phone)}\n"
    
    if contact.company_name:
        msg += f"🏢 Company: {escape_telegram(contact.company_name)}\n"
    
    msg += f"\n🔗 Linked {escape_telegram(party_type)}: {escape_telegram(party_display)}\n"
    msg += f"\n{telegram_form_link(party_type, party_name, f'View {party_type}')}"
    msg += f"\n{telegram_form_link('Contact', contact.name, 'View Contact')}"
    
    return msg


def format_existing_contact_message(contact, party_type=None, party=None):
    """Format message for existing contact"""
    
    msg = "<b>✅ Contact Already Exists</b>\n\n"
    msg += f"👤 Name: {escape_telegram(contact.first_name)} {escape_telegram(contact.last_name)}\n"
    
    if contact.email_ids and len(contact.email_ids) > 0:
        msg += f"📧 Email: {escape_telegram(contact.email_ids[0].email_id)}\n"
    
    if contact.phone_nos and len(contact.phone_nos) > 0:
        msg += f"📞 Phone: {escape_telegram(contact.phone_nos[0].phone)}\n"
    
    if contact.company_name:
        msg += f"🏢 Company: {escape_telegram(contact.company_name)}\n"
    
    if party_type and party:
        msg += f"\n🔗 Linked to {escape_telegram(party_type)}: {escape_telegram(party)}\n"
    
    msg += f"\n{telegram_form_link('Contact', contact.name, 'View Contact')}"
    
    return msg


def format_contact_created_with_party_message(contact, party_type, party_name, party_display):
    """Format message when contact is created with existing party"""
    
    msg = "<b>✅ Contact Created Successfully!</b>\n\n"
    msg += f"👤 Name: {escape_telegram(contact.first_name)} {escape_telegram(contact.last_name)}\n"
    
    if contact.email_ids and len(contact.email_ids) > 0:
        msg += f"📧 Email: {escape_telegram(contact.email_ids[0].email_id)}\n"
    
    if contact.phone_nos and len(contact.phone_nos) > 0:
        msg += f"📞 Phone: {escape_telegram(contact.phone_nos[0].phone)}\n"
    
    if contact.company_name:
        msg += f"🏢 Company: {escape_telegram(contact.company_name)}\n"
    
    msg += f"\n🔗 Linked to existing {escape_telegram(party_type)}: {escape_telegram(party_display)}\n"
    msg += f"\n{telegram_form_link('Contact', contact.name, 'View Contact')}"
    msg += f"\n{telegram_form_link(party_type, party_name, f'View {party_type}')}"
    
    return msg


def format_new_lead_and_contact_message(lead, contact):
    """Format message when both lead and contact are created"""
    
    msg = "<b>✅ New Lead Created!</b>\n\n"
    msg += f"👤 Name: {escape_telegram(lead.lead_name)}\n"
    
    if lead.email_id:
        msg += f"📧 Email: {escape_telegram(lead.email_id)}\n"
    
    if lead.phone:
        msg += f"📞 Phone: {escape_telegram(lead.phone)}\n"
    
    if lead.company_name:
        msg += f"🏢 Company: {escape_telegram(lead.company_name)}\n"
    
    msg += "\n✅ Contact also created and linked\n"
    msg += f"\n{telegram_form_link('Lead', lead.name, 'View Lead')}"
    msg += f"\n{telegram_form_link('Contact', contact.name, 'View Contact')}"
    
    return msg
