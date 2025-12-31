"""
AI Service for processing business cards
Handles AI Agent integration with retry logic
"""
import frappe
import time
from frappe import _


def process_business_card_with_context(image_url, text_context="", max_retries=3):
    """
    Extract data from business card image using AI Agent
    
    Args:
        image_url: URL of the business card image
        text_context: Additional text context for the AI
        max_retries: Maximum number of retry attempts (default: 3)
    
    Returns:
        AI Agent result
    """
    # Get AI Agent from Telegram Setting
    telegram_setting = frappe.get_single("Telegram Setting")
    ai_agent_name = telegram_setting.ai_agent
    
    if not ai_agent_name:
        frappe.throw("AI Agent not configured in Telegram Setting")
    
    agent = frappe.get_doc("AI Agent", ai_agent_name)
    
    ai_input_data = {
        "image_url": image_url,
        "context": text_context or "No additional context provided"
    }
    
    last_exception = None
    
    for attempt in range(1, max_retries + 1):
        try:
            result = agent.agent_service.invoke(**ai_input_data)
            return result
            
        except Exception as e:
            last_exception = e
            frappe.log_error(
                f"Attempt {attempt}/{max_retries} failed: {str(e)}",
                "Business Card AI Processing Error"
            )
            
            # Don't sleep on the last attempt
            if attempt < max_retries:
                # Exponential backoff: 1s, 2s, 4s...
                sleep_time = 2 ** (attempt - 1)
                time.sleep(sleep_time)
    
    # All retries exhausted
    frappe.log_error(
        f"All {max_retries} attempts failed. Last error: {str(last_exception)}",
        "Business Card AI Processing Error - All Retries Failed"
    )
    raise last_exception

