"""Restricted, non-sensitive DocVision runtime diagnostics."""

import frappe


def inspect():
    frappe.only_for("System Manager")
    setting = frappe.get_single("Telegram Setting")
    latest = frappe.get_all(
        "DocVision Outreach",
        fields=["name", "lead", "status", "modified"],
        order_by="creation desc",
        limit=1,
    )
    return {
        "latest_outreach": latest[0] if latest else None,
        "agents": {
            "card": setting.ai_agent,
            "company_research": setting.company_research_agent,
            "person_research": setting.person_research_agent,
            "email": setting.email_agent,
        },
        "auto_outreach_enabled": bool(setting.enable_auto_outreach),
    }
