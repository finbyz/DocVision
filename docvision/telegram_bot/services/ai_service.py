"""
AI Service for processing business cards
Handles AI Agent integration
"""
import frappe

from docvision.telegram_bot.utils.country import get_country_extraction_prompt


def process_business_card_with_context(image_data_url: str, text_context: str = ""):
    """Extract data from business card image using AI Agent"""
    telegram_setting = frappe.get_single("Telegram Setting")
    ai_agent_name = telegram_setting.ai_agent

    if not ai_agent_name:
        frappe.throw("AI Agent not configured in Telegram Setting")

    agent = frappe.get_doc("AI Agent", ai_agent_name)

    country_guidelines = get_country_extraction_prompt()
    context_str = f"{text_context}\n\n{country_guidelines}".strip() if text_context else country_guidelines

    ai_input_data = {
        "image_url": image_data_url,
        "context": context_str
    }

    return agent.agent_service.invoke(**ai_input_data)

