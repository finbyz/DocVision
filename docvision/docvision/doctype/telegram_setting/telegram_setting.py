# Copyright (c) 2025, Finbyz and contributors
# For license information, please see license.txt

import frappe
import requests
from frappe import _
from frappe.model.document import Document

from docvision.telegram_bot.utils.logging import log_exception
from docvision.telegram_bot.utils.outreach_condition import validate_outreach_condition

WEBHOOK_METHOD = "/api/method/docvision.telegram_bot.webhook.telegram_webhook"


class TelegramSetting(Document):
    def validate(self):
        if not self.get_password("telegram_webhook_secret", raise_exception=False):
            self.telegram_webhook_secret = frappe.generate_hash(length=48)
        validate_outreach_condition(self.get("outreach_draft_condition"))

    def on_update(self):
        self.setup_telegram_webhook()

    def setup_telegram_webhook(self):
        bot_token = self.get_password("telegram_bot_token")
        if not bot_token:
            frappe.throw(_("Add a Telegram bot token before configuring the webhook."))

        webhook_url = self.get_webhook_url()
        webhook_secret = self.get_password("telegram_webhook_secret")

        try:
            response = requests.post(
                f"https://api.telegram.org/bot{bot_token}/setWebhook",
                json={
                    "url": webhook_url,
                    "secret_token": webhook_secret,
                    "allowed_updates": ["message", "channel_post", "callback_query"],
                },
                timeout=10,
            )
            response.raise_for_status()
            response_data = response.json()
        except (requests.RequestException, ValueError):
            log_exception("Telegram Webhook Setup Error")
            frappe.throw(_("Telegram could not configure the webhook. Check the Error Log."))

        if not response_data.get("ok"):
            description = response_data.get("description") or _("Unknown Telegram error")
            frappe.throw(_("Telegram rejected the webhook: {0}").format(description))

        frappe.msgprint(
            _("Telegram webhook registered at {0}").format(webhook_url),
            title=_("Telegram Webhook"),
            indicator="green",
        )

    def get_webhook_url(self):
        site_url = (frappe.conf.get("host_name") or frappe.utils.get_url()).rstrip("/")
        if not site_url.startswith(("http://", "https://")):
            site_url = f"https://{site_url}"
        elif site_url.startswith("http://"):
            site_url = f"https://{site_url.removeprefix('http://')}"
        return f"{site_url}{WEBHOOK_METHOD}"
