# Copyright (c) 2026, Finbyz and contributors
# For license information, please see license.txt

import frappe
from frappe.model.document import Document
from frappe.utils import now_datetime


class DocVisionOutreach(Document):
    def send_outreach_email(self):
        """Dispatch the drafted email to the Lead/Contact and update status"""
        if not self.recipient_email:
            frappe.throw("Recipient email is required to send outreach email.")
        
        if not self.subject or not self.body:
            frappe.throw("Subject and body cannot be empty.")

        telegram_setting = frappe.get_single("Telegram Setting")
        sender = None
        if telegram_setting.email_account:
            sender = frappe.get_value("Email Account", telegram_setting.email_account, "email_id")
        else:
            sender = frappe.get_value("Email Account", {"default_outgoing": 1}, "email_id")

        # Webhook runs as 'Guest' in Telegram callbacks. Strictly elevate to Administrator.
        original_user = frappe.session.user
        try:
            frappe.set_user("Administrator")

            from frappe.core.doctype.communication.email import make
            make(
                recipients=self.recipient_email,
                subject=self.subject,
                content=self.body,
                doctype="Lead",
                name=self.lead,
                send_email=True,
                sender=sender,
            )

            self.status = "Sent"
            self.sent_on = now_datetime()
            self.save(ignore_permissions=True)
            frappe.db.commit()

        finally:
            frappe.set_user(original_user)
