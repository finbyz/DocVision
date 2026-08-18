"""
Message handlers for different chat types
Handles private and group messages
"""
from docvision.telegram_bot.services.telegram_service import send_telegram_message, get_telegram_image_url
from docvision.telegram_bot.services.ai_service import process_business_card_with_context
from docvision.telegram_bot.services.contact_service import process_contact_or_lead
from docvision.telegram_bot.utils.logging import log_exception
from docvision.telegram_bot.utils.validators import is_valid_extraction


def handle_private_message(message, chat_id):
    """Handle messages from private chats"""
    try:
        user_name = message.get('from', {}).get('first_name', 'User')
        
        # Handle /start command
        if message.get('text') == '/start':
            send_telegram_message(
                chat_id,
                f"Hello {user_name}!\n\nSend me a business card image."
            )
            return {"status": "ok"}
        
        # Check if photo exists
        if 'photo' not in message:
            send_telegram_message(
                chat_id, 
                "Please send a business card image.\n\nSupported formats: JPG, PNG"
            )
            return {"status": "ok"}
        
        # Process the business card
        return process_business_card_image(message, chat_id)
        
    except Exception:
        log_exception(
            "Private Message Error",
            chat_id=chat_id,
            message_id=message.get("message_id"),
        )
        return {"status": "error", "message": "Unable to process private message"}


def handle_group_message(message, chat_id):
    """Handle messages from group chats"""
    try:
        text_message = message.get('caption') or message.get('text', '')
        
        if 'photo' not in message:
            return {"status": "ok", "message": "No image in group message"}
        
        # Process the business card
        return process_business_card_image(message, chat_id, text_message)
        
    except Exception:
        log_exception(
            "Group Message Error",
            chat_id=chat_id,
            message_id=message.get("message_id"),
        )
        return {"status": "error", "message": "Unable to process group message"}


def process_business_card_image(message, chat_id, text_context=""):
    """Common logic for processing business card images"""
    stage = "image_selection"

    try:
        # Get photo file_id
        photo = message['photo'][-1] 
        file_id = photo['file_id']
        
        # Send processing message
        send_telegram_message(chat_id, "⏳ Please Wait, we are processing your card...")
        
        # Get direct image URL from Telegram
        stage = "image_download"
        image_url = get_telegram_image_url(file_id)
        
        if not image_url:
            send_telegram_message(
                chat_id, 
                "❌ Failed to access image.\n\nPlease try again."
            )
            return {"status": "image_access_failed"}
        
        # Extract data from image
        send_telegram_message(chat_id, "🔍 Analyzing business card...")
        stage = "ai_extraction"
        structured_data = process_business_card_with_context(image_url, text_context)
        
        # Validate extraction
        if not structured_data or not is_valid_extraction(structured_data):
            send_telegram_message(
                chat_id, 
                "❌ Failed to process business card\n\n"
                "Please ensure:\n"
                "• Image is clear and readable\n"
                "• Business card is fully visible\n"
                "• Good lighting in photo\n\n"
                "Or contact support."
            )
            return {"status": "processing_failed"}
        
        # Process Contact/Lead
        send_telegram_message(chat_id, "💾 Creating contact/lead...")
        stage = "contact_lead_processing"
        result = process_contact_or_lead(structured_data)
        
        # Send final result
        if result.get('success'):
            send_telegram_message(chat_id, result['message'])
        else:
            send_telegram_message(
                chat_id, 
                f"❌ Error: {result.get('message', 'Unknown error')}"
            )
        
        return {"status": "success"}
        
    except Exception:
        log_exception(
            "Business Card Processing Error",
            chat_id=chat_id,
            message_id=message.get("message_id"),
            stage=stage,
        )
        send_telegram_message(
            chat_id, 
            "⚠️ Processing error. Please try again."
        )
        return {"status": "error", "message": "Unable to process business card"}
