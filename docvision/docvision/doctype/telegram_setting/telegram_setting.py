# Copyright (c) 2025, Finbyz and contributors
# For license information, please see license.txt

# Copyright (c) 2025, Finbyz and contributors
# For license information, please see license.txt

import frappe
import requests
from frappe.model.document import Document

from docvision.telegram_bot.utils.logging import log_error, log_exception


class TelegramSetting(Document):
    def on_update(self):
        """Remove and re-register Telegram webhook on update"""
        self.setup_telegram_webhook()
    
    def setup_telegram_webhook(self):
     
        try:
            bot_token = self.get_password("telegram_bot_token")
            
            if not bot_token:
                log_error("Telegram Webhook Setup", "No bot token configured")
                frappe.msgprint(
                    " Bot token not found. Please add bot token first.",
                    title="Webhook Setup Failed",
                    indicator="red"
                )
                return
            
            # Step 1: Remove existing webhook
            remove_response = requests.get(
                f"https://api.telegram.org/bot{bot_token}/deleteWebhook",
                timeout=10
            )
            
            if remove_response.status_code == 200:
                frappe.logger().info("Telegram webhook removed successfully")
            else:
                log_error(
                    "Telegram Webhook Removal",
                    "Telegram API rejected deleteWebhook request",
                    http_status=remove_response.status_code,
                    telegram_response=remove_response.text,
                )
            
            webhook_url = self.get_webhook_url()
            
            if not webhook_url:
                frappe.throw(
                    "Unable to determine site URL. Please configure it in site_config.json",
                    title="Configuration Error"
                )
                        
            set_response = requests.get(
                f"https://api.telegram.org/bot{bot_token}/setWebhook",
                params={"url": webhook_url},
                timeout=10
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
            log_exception("Telegram Webhook Setup Timeout")
            frappe.msgprint(
                "⚠️ Telegram API timeout. Please try again.",
                title="Webhook Setup",
                indicator="orange"
            )
            
        except Exception:
            log_exception("Telegram Webhook Setup Error")
            frappe.msgprint(
                "❌ Unable to configure the webhook. Check Error Log for details.",
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
