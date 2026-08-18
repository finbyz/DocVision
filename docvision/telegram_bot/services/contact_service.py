"""
Contact and Lead service
Handles all contact/lead creation and management logic
"""
from docvision.telegram_bot.utils.formatters import (
    format_existing_party_message,
    format_contact_created_with_party_message,
    format_new_lead_and_contact_message
)
from docvision.telegram_bot.utils.logging import log_exception
from docvision.telegram_bot.services.search_service import (
    get_contact_with_domain_or_email,
    find_customer_by_company_name,
    find_lead_by_company_name
)
from docvision.telegram_bot.services.create_service import (
    create_contact_with_party,
    create_lead_from_data
)


def process_contact_or_lead(data):
    """
    Main flow for processing contact/lead from extracted data
    Follows the exact n8n logic
    """
    stage = "contact_lookup"

    try:
        # Step 1: Check if contact exists with domain/email
        contact_result = get_contact_with_domain_or_email(data)

        if contact_result.get("status") == "error":
            return {
                "success": False,
                "message": "Unable to check for an existing contact. Please try again.",
            }
        
        if contact_result.get('status') == 'success' and contact_result.get('contact'):
            if contact_result.get('with_domain'):
                # Contact exists - Return existing
                return {
                    "success": True,
                    "message": format_existing_party_message(
                        contact_result['party_type'],
                        contact_result['party_name'],
                        contact_result['party_display'],
                        contact_result['contact']
                    )
                }
        
        # Step 2: Check if customer exists
        company_name = data.core_company_name or data.company_name
        
        stage = "customer_lookup"
        customer = find_customer_by_company_name(company_name)
        if customer:
            stage = "customer_contact_creation"
            contact = create_contact_with_party(data, "Customer", customer['name'])
            return {
                "success": True,
                "message": format_contact_created_with_party_message(
                    contact, "Customer", customer['name'], customer.get('customer_name', '')
                )
            }
        
        # Step 3: Check if lead exists
        stage = "lead_lookup"
        lead = find_lead_by_company_name(company_name)
        if lead:
            stage = "lead_contact_creation"
            contact = create_contact_with_party(data, "Lead", lead['name'])
            return {
                "success": True,
                "message": format_contact_created_with_party_message(
                    contact, "Lead", lead['name'], lead.get('lead_name', '')
                )
            }
        
        # Step 4: Create new Lead + Contact
        stage = "lead_creation"
        lead = create_lead_from_data(data)
        stage = "new_lead_contact_creation"
        contact = create_contact_with_party(data, "Lead", lead.name)
        
        return {
            "success": True,
            "message": format_new_lead_and_contact_message(lead, contact)
        }
        
    except Exception:
        if stage not in {"customer_lookup", "lead_lookup"}:
            log_exception("Contact/Lead Flow Error", stage=stage)
        return {
            "success": False,
            "message": "Unable to create the contact or lead. Please try again.",
        }
