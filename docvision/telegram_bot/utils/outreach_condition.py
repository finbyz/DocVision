"""Safe evaluation for the optional outreach drafting condition."""

import frappe
from frappe import _


def evaluate_outreach_condition(condition: str | None, lead, contact=None) -> bool:
    if not (condition or "").strip():
        return True

    context = {
        "doc": lead,
        "contact": contact or frappe._dict(),
    }
    return bool(frappe.safe_eval(condition, None, context))


def validate_outreach_condition(condition: str | None) -> None:
    if not (condition or "").strip():
        return

    try:
        evaluate_outreach_condition(
            condition,
            frappe.new_doc("Lead"),
            frappe.new_doc("Contact"),
        )
    except Exception:
        frappe.throw(_("The Outreach Draft Condition is invalid."))
