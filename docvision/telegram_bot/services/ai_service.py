"""
AI Service for processing business cards
Handles AI Agent integration
"""
import frappe


def process_business_card_with_context(image_url, text_context=""):
    """Extract data from business card image using AI Agent"""
    telegram_setting = frappe.get_single("Telegram Setting")
    ai_agent_name = telegram_setting.ai_agent

    if not ai_agent_name:
        frappe.throw("AI Agent not configured in Telegram Setting")

    agent = frappe.get_doc("AI Agent", ai_agent_name)

    ai_input_data = {
        "image_url": image_url,
        "context": text_context or "No additional context provided"
    }

    return agent.agent_service.invoke(**ai_input_data)
