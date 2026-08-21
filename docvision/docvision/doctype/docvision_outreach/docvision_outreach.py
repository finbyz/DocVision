# Copyright (c) 2026, Finbyz and contributors
# For license information, please see license.txt

import frappe
from frappe.model.document import Document
from frappe.utils import now_datetime


class DocVisionOutreach(Document):
    @frappe.whitelist(methods=["POST"])
    def send_outreach_email(self):
        """Dispatch the drafted email to the Lead/Contact and update status"""
        self.check_permission("write")
        frappe.db.savepoint("docvision_send_outreach")

        try:
            self._lock_for_sending()
            self._validate_sendable()
            self.status = "Sending"
            self.save()

            telegram_setting = frappe.get_single("Telegram Setting")
            sender = _get_sender(telegram_setting)

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
            self.save()
        except Exception:
            frappe.db.rollback(save_point="docvision_send_outreach")
            raise

    def _lock_for_sending(self):
        outreach = frappe.qb.DocType("DocVision Outreach")
        locked = (
            frappe.qb.from_(outreach)
            .select(outreach.name)
            .where(outreach.name == self.name)
            .for_update()
            .run()
        )
        if not locked:
            frappe.throw("Outreach record no longer exists.")
        self.reload()

    def _validate_sendable(self):
        if not self.recipient_email:
            frappe.throw("Recipient email is required to send outreach email.")

        if not self.subject or not self.body:
            frappe.throw("Subject and body cannot be empty.")

        if self.status != "Pending Approval":
            frappe.throw(f"Outreach must be Pending Approval, not {self.status}.")


def _get_sender(telegram_setting) -> str | None:
    if telegram_setting.email_account:
        return frappe.db.get_value("Email Account", telegram_setting.email_account, "email_id")
    return frappe.db.get_value("Email Account", {"default_outgoing": 1}, "email_id")
