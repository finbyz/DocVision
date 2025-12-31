# Copyright (c) 2025, Finbyz and contributors
# For license information, please see license.txt

# Copyright (c) 2025, Finbyz and contributors
# For license information, please see license.txt

import frappe
import requests
from requests.adapters import HTTPAdapter
from urllib3.util.retry import Retry
from frappe.model.document import Document


def get_telegram_session():
    """Create a requests session with retry logic for Telegram API"""
    session = requests.Session()
    retries = Retry(
        total=3,
        backoff_factor=1,
        status_forcelist=[500, 502, 503, 504],
        allowed_methods=["GET", "POST"]
    )
    adapter = HTTPAdapter(max_retries=retries)
    session.mount("https://", adapter)
    return session

class TelegramSetting(Document):
    def on_update(self):
        """Remove and re-register Telegram webhook on update"""
        self.setup_telegram_webhook()
    
    def setup_telegram_webhook(self):
     
        try:
            bot_token = self.get_password("telegram_bot_token")
            
            if not bot_token:
                frappe.log_error("No bot token found", "Telegram Webhook Setup")
                frappe.msgprint(
                    " Bot token not found. Please add bot token first.",
                    title="Webhook Setup Failed",
                    indicator="red"
                )
                return
            
            # Step 1: Remove existing webhook
            session = get_telegram_session()
            remove_response = session.get(
                f"https://api.telegram.org/bot{bot_token}/deleteWebhook",
            )
            
            if remove_response.status_code == 200:
                frappe.logger().info("Telegram webhook removed successfully")
            else:
                frappe.log_error(
                    f"Failed to remove webhook: {remove_response.text}", 
                    "Telegram Webhook Removal"
                )
            
            webhook_url = self.get_webhook_url()
            
            if not webhook_url:
                frappe.throw(
                    "Unable to determine site URL. Please configure it in site_config.json",
                    title="Configuration Error"
                )
                        
            set_response = session.get(
                f"https://api.telegram.org/bot{bot_token}/setWebhook",
                params={"url": webhook_url},
            )
            
            response_data = set_response.json()
            
            if set_response.status_code == 200 and response_data.get('ok'):
                frappe.msgprint(
                    f"✅ Webhook registered successfully!<br><br>"
                    f"<b>Webhook URL:</b><br>{webhook_url}<br><br>"
                    f"<b>Response:</b><br>{response_data.get('description', 'OK')}",
                    title="Telegram Webhook",
                    indicator="green"
                )
                frappe.logger().info(f"Telegram webhook set to: {webhook_url}")
            else:
                error_msg = response_data.get('description', 'Unknown error')
                frappe.throw(
                    f"Failed to set webhook: {error_msg}<br><br>"
                    f"<b>Attempted URL:</b> {webhook_url}<br><br>"
                    f"<b>Note:</b> Telegram requires HTTPS. Make sure your site has SSL certificate.",
                    title="Telegram Webhook Error"
                )
                
        except requests.exceptions.Timeout:
            frappe.log_error("Telegram API timeout", "Telegram Webhook Setup")
            frappe.msgprint(
                "⚠️ Telegram API timeout. Please try again.",
                title="Webhook Setup",
                indicator="orange"
            )
            
        except Exception as e:
            frappe.log_error(str(e), "Telegram Webhook Setup Error")
            frappe.msgprint(
                f"❌ Error: {str(e)}",
                title="Webhook Setup Failed",
                indicator="red"
            )
    
    def get_webhook_url(self):        
        site_url = frappe.conf.get('host_name')
        webhook_url = None
        if site_url:
            if not site_url.startswith('http'):
                webhook_url = f"https://{site_url}/api/method/docvision.telegram_bot.webhook.telegram_webhook"
            if site_url.startswith('http://'):
                webhook_url =  f"{site_url}/api/method/docvision.telegram_bot.webhook.telegram_webhook"
        if webhook_url:
            return webhook_url
        site_url = frappe.utils.get_url()
        
        if site_url.startswith('http://'):
            site_url = site_url.replace('http://', 'https://')
        webhook_url = f"{site_url}/api/method/docvision.telegram_bot.webhook.telegram_webhook"
        return webhook_url

    @frappe.whitelist()
    def disconnect_webhook(self):
        """Remove Telegram webhook"""
        try:
            bot_token = self.get_password("telegram_bot_token")
            
            if not bot_token:
                frappe.msgprint(
                    "Bot token not found. Please add bot token first.",
                    title="Disconnect Failed",
                    indicator="red"
                )
                return
            
            session = get_telegram_session()
            remove_response = session.get(
                f"https://api.telegram.org/bot{bot_token}/deleteWebhook",
            )
            
            response_data = remove_response.json()
            
            if remove_response.status_code == 200 and response_data.get('ok'):
                frappe.msgprint(
                    "✅ Webhook disconnected successfully!",
                    title="Telegram Webhook",
                    indicator="green"
                )
            else:
                error_msg = response_data.get('description', 'Unknown error')
                frappe.msgprint(
                    f"❌ Failed to disconnect webhook: {error_msg}",
                    title="Disconnect Failed",
                    indicator="red"
                )
                
        except requests.exceptions.Timeout:
            frappe.msgprint(
                "⚠️ Telegram API timeout. Please try again.",
                title="Disconnect Failed",
                indicator="orange"
            )
            
        except Exception as e:
            frappe.log_error(str(e), "Telegram Webhook Disconnect Error")
            frappe.msgprint(
                f"❌ Error: {str(e)}",
                title="Disconnect Failed",
                indicator="red"
            )